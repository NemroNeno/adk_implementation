import asyncio
import socketio
from sqlalchemy.orm import Session
import time
import google.generativeai as genai

from app.tools.google_tool import tavily_search, send_sms
from app.core.config import settings
from app.db.base import SessionLocal
from app.crud import crud_agent, crud_chat, crud_user
from app.schemas.chat import ChatMessageCreate
from app.services.audit_service import log_activity
import sentry_sdk

# --- THIS IS THE FIX ---
# REMOVE the genai.init() line entirely.
# The library automatically finds and uses the service account file
# specified by GOOGLE_APPLICATION_CREDENTIALS in your .env file.
# --- END OF FIX ---

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=["http://localhost:3000", "*"])

chat_sessions = {}
session_user_info = {}

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@sio.on('connect', namespace='/text')
async def connect_text(sid, environ):
    print(f"Text Chat Client connected: {sid}")

@sio.on('disconnect', namespace='/text')
def disconnect_text(sid):
    chat_sessions.pop(sid, None)
    session_user_info.pop(sid, None)
    print(f"Text Chat Client disconnected: {sid}")

@sio.on('start_chat', namespace='/text')
async def start_chat(sid, data):
    agent_id = data.get('agent_id')
    user_id = data.get('user_id')
    with get_db_session() as db:
        try:
            agent_config = crud_agent.get_agent_by_id(db, agent_id=agent_id)
            if not agent_config:
                await sio.emit('error', {'message': 'Agent not found.'}, to=sid, namespace='/text')
                return

            session_user_info[sid] = {'user_id': user_id, 'agent_id': agent_id}
            
            tool_function_map = {"tavily_search": tavily_search, "send_sms": send_sms}
            tools_for_genai = [tool_function_map[key] for key in agent_config.tools if key in tool_function_map]

            model = genai.GenerativeModel(
                'gemini-1.5-flash',
                system_instruction=agent_config.system_prompt,
                tools=tools_for_genai
            )
            
            history_from_db = crud_chat.get_chat_history_for_agent(db, agent_id=agent_id, owner_id=user_id)
            history_for_genai = [{"role": msg.role.replace("human", "user").replace("ai", "model"), "parts": [msg.content]} for msg in history_from_db]

            chat = model.start_chat(history=history_for_genai)
            
            chat_sessions[sid] = chat
            await sio.emit('chat_started', to=sid, namespace='/text')

        except Exception as e:
            sentry_sdk.capture_exception(e)
            await sio.emit('error', {'message': f"Failed to start chat: {e}"}, to=sid, namespace='/text')

@sio.on('chat_message', namespace='/text')
async def handle_chat_message(sid, data):
    if sid not in chat_sessions: return
    user_input = data.get('message')
    if not user_input: return

    chat = chat_sessions[sid]
    user_info = session_user_info[sid]

    with get_db_session() as db:
        try:
            start_time = time.time()
            crud_chat.create_chat_message(db, ChatMessageCreate(
                agent_id=user_info['agent_id'], user_id=user_info['user_id'], role='human', content=user_input
            ))
            
            response = await chat.send_message_async(user_input, stream=True)
            
            full_response = ""
            tool_calls = []
            async for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    await sio.emit('token', {'token': chunk.text}, to=sid, namespace='/text')
                if hasattr(chunk, 'function_calls') and chunk.function_calls:
                    for fc in chunk.function_calls:
                        tool_calls.append({"name": fc.name, "args": dict(fc.args)})
                        await sio.emit('tool_start', {"name": fc.name}, to=sid, namespace='/text')

            end_time = time.time()
            response_time = end_time - start_time
            token_count = len(full_response.split())
            
            crud_chat.create_chat_message(db, ChatMessageCreate(
                agent_id=user_info['agent_id'], user_id=user_info['user_id'], role='ai',
                content=full_response, response_time_seconds=response_time,
                tool_calls=tool_calls, token_usage={"total_tokens": token_count}
            ))
            db.commit()
            
            await sio.emit('stream_end', {'metrics': {"response_time_seconds": response_time}}, to=sid, namespace='/text')
            
        except Exception as e:
            print(f"!! AGENT EXECUTION ERROR: {e}")
            sentry_sdk.capture_exception(e)
            await sio.emit('error', {'message': f"An agent error occurred: {e}"}, to=sid, namespace='/text')