import socketio
import asyncio
from sqlalchemy.orm import Session
from app.services.voice_service import synthesize_speech_elevenlabs

# --- Google ADK Imports ---
from google_adk.agents import LlmAgent
from google_adk.orchestration import AdkAsyncHandler
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# --- Our Application Imports ---
from app.tools.google_tools import ADK_TOOL_REGISTRY
from app.core.config import settings
from app.db.base import SessionLocal
from app.crud import crud_agent, crud_chat
from app.schemas.chat import ChatMessageCreate
from app.services.alert_service import send_alert

# --- Socket.IO Setup ---
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="http://localhost:3000")

# --- Globals ---
handler = AdkAsyncHandler()
agent_instances = {}
session_user_info = {}

def get_db():
    return SessionLocal()

@sio.event
async def connect(sid, environ):
    print(f"Socket connected: {sid}")

@sio.event
async def disconnect(sid):
    agent_instances.pop(sid, None)
    session_user_info.pop(sid, None)
    print(f"Socket disconnected: {sid}")

@sio.on('start_chat')
async def start_chat(sid, data):
    agent_id = data.get('agent_id')
    user_id = data.get('user_id')
    if not agent_id or not user_id:
        return

    db = get_db()
    try:
        agent_config = crud_agent.get_agent_by_id(db, agent_id=agent_id)
        if not agent_config or agent_config.owner_id != user_id:
            return

        session_user_info[sid] = {'user_id': user_id, 'agent_id': agent_id}

        tools = [ADK_TOOL_REGISTRY[key] for key in agent_config.tools if key in ADK_TOOL_REGISTRY]

        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GOOGLE_API_KEY
        )

        adk_agent = LlmAgent(
            llm=llm,
            system_prompt=agent_config.system_prompt,
            tools=tools
        )

        agent_instances[sid] = adk_agent

        await sio.emit('chat_started', to=sid)
    finally:
        db.close()

@sio.on('chat_message')
async def handle_chat_message(sid, data):
    if sid not in agent_instances:
        return

    user_input = data.get('message')
    if not user_input:
        return

    adk_agent = agent_instances[sid]
    user_info = session_user_info.get(sid)
    db = get_db()

    try:
        # Save human message
        crud_chat.create_chat_message(db, ChatMessageCreate(
            agent_id=user_info['agent_id'],
            user_id=user_info['user_id'],
            role='human',
            content=user_input
        ))

        # Build history
        history = crud_chat.get_chat_history_for_agent(
            db,
            agent_id=user_info['agent_id'],
            owner_id=user_info['user_id']
        )
        langchain_history = [HumanMessage(content=msg.content) for msg in history if msg.role == 'human']

        # Get agent response
        response_generator = handler.stream(agent=adk_agent, prompt=user_input, previous_messages=langchain_history)
        full_response_content = ""
        async for step in response_generator:
            if step.is_last_step and step.outputs:
                final_output = step.outputs.get("output", "")
                full_response_content += final_output

        print(f"[{sid}] Agent Response Text: {full_response_content}")

        # Convert to speech
        audio_response_data = synthesize_speech_elevenlabs(full_response_content)

        if audio_response_data:
            await sio.emit('audio_response', {
                'audio': audio_response_data,
                'text': full_response_content
            }, to=sid)
        else:
            await sio.emit('error', {'message': "Failed to synthesize audio response."})

        # Save AI message
        crud_chat.create_chat_message(db, ChatMessageCreate(
            agent_id=user_info['agent_id'],
            user_id=user_info['user_id'],
            role='ai',
            content=full_response_content
        ))

    except Exception as e:
        print(f"!! AGENT EXECUTION ERROR: {e}")
        await sio.emit('error', {'message': "An agent error occurred."})
    finally:
        db.close()
