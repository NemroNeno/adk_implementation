import socketio
import asyncio
from sqlalchemy.orm import Session

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

# Global handler for ADK (can be shared across connections)
handler = AdkAsyncHandler()

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="http://localhost:3000")

# In-memory storage for agent instances
agent_instances = {}
session_user_info = {}

def get_db(): return SessionLocal()

@sio.event
async def connect(sid, environ): print(f"Socket connected: {sid}")

@sio.event
async def disconnect(sid):
    if sid in agent_instances: del agent_instances[sid]
    if sid in session_user_info: del session_user_info[sid]
    print(f"Socket disconnected: {sid}")

@sio.on('start_chat')
async def start_chat(sid, data):
    agent_id, user_id = data.get('agent_id'), data.get('user_id')
    if not all([agent_id, user_id]): return
    
    db = get_db()
    try:
        agent_config = crud_agent.get_agent_by_id(db, agent_id=agent_id)
        if not agent_config or agent_config.owner_id != user_id: return

        session_user_info[sid] = {'user_id': user_id, 'agent_id': agent_id}
        
        # Get the tool objects from our registry based on agent config
        tools = [ADK_TOOL_REGISTRY[key] for key in agent_config.tools if key in ADK_TOOL_REGISTRY]
        
        # The underlying model is still Gemini, configured via the LangChain wrapper
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=settings.GOOGLE_API_KEY)

        # --- Create an Agent using the Google ADK's LlmAgent ---
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
    if sid not in agent_instances: return
    user_input = data.get('message')
    if not user_input: return

    adk_agent = agent_instances[sid]
    user_info = session_user_info[sid]
    db = get_db() # Get a DB session for saving history

    try:
        # Save the human message first
        human_msg = ChatMessageCreate(agent_id=user_info['agent_id'], user_id=user_info['user_id'], role='human', content=user_input)
        crud_chat.create_chat_message(db, message=human_msg)

        # --- Use the ADK to process the message and get a streaming response ---
        # We need to load history for the ADK in LangChain's format
        history = crud_chat.get_chat_history_for_agent(db, agent_id=user_info['agent_id'], owner_id=user_info['user_id'])
        langchain_history = [HumanMessage(content=msg.content) for msg in history if msg.role == 'human']

        response_generator = handler.stream(
            agent=adk_agent,
            prompt=user_input,
            previous_messages=langchain_history
        )

        full_response_content = ""
        async for step in response_generator:
            if step.is_last_step and step.outputs:
                # The final output from the agent
                final_output = step.outputs.get("output", "")
                full_response_content += final_output
                await sio.emit('token', {'token': final_output}, to=sid)
            elif step.intermediate_steps:
                # This is where you could stream back tool usage info
                print(f"ADK Intermediate Step: {step.intermediate_steps}")

        # Save the AI response
        ai_msg = ChatMessageCreate(agent_id=user_info['agent_id'], user_id=user_info['user_id'], role='ai', content=full_response_content)
        crud_chat.create_chat_message(db, message=ai_msg)

        await sio.emit('stream_end', {'metrics': {}}) # Metrics would need to be re-implemented

    except Exception as e:
        print(f"!! AGENT EXECUTION ERROR: {e}")
        send_alert("critical", "Agent execution error", {"error": str(e), "user_id": user_info['user_id']})
        await sio.emit('error', {'message': "An error occurred."})
    finally:
        db.close()