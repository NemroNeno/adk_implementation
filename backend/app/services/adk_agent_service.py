"""
ADK-based Agent Service
Reimplementation of agent_service.py using Google Agent Development Kit (ADK)
Based on the working examples from AhsanAyaz/ai-agents-google-adk repository
"""

import asyncio
import socketio
from sqlalchemy.orm import Session
import time
import logging
import os
import json
from typing import Dict, Any, AsyncGenerator, Optional

# ADK imports - using the Runner approach with proper async iteration
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.genai import types as genai_types
from google.adk.tools import FunctionTool

# Your existing imports
from app.tools.google_tool import tavily_search, send_sms
from app.core.config import settings
from app.core.adk_config import adk_config
from app.db.base import SessionLocal
from app.crud import crud_agent, crud_chat, crud_user
from app.schemas.chat import ChatMessageCreate
from app.services.audit_service import log_activity
import sentry_sdk

# Initialize logging
logger = logging.getLogger(__name__)

# Check and log Google ADK credentials
gcp_credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
if os.path.exists(gcp_credentials_path):
    logger.info(f"Google ADK credentials found at {gcp_credentials_path}")
else:
    logger.error(f"Google ADK credentials NOT FOUND at {gcp_credentials_path}")

# ADK Services
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()

# Socket.IO setup with debug logging
sio = socketio.AsyncServer(
    async_mode='asgi', 
    cors_allowed_origins=["http://localhost:3000", "*"],
    logger=True,
    engineio_logger=True
)

# Session management
chat_sessions = {}
session_user_info = {}
adk_runners = {}  # Store ADK runners for each session
active_chat_tasks = {}  # Store chat processing tasks

def get_db_session():
    """Get database session - returns the session directly for context manager usage"""
    return SessionLocal()

# Tool functions wrapped for ADK
def tavily_search_tool(query: str) -> Dict[str, Any]:
    """Search tool using Tavily for web search capabilities."""
    try:
        result = tavily_search(query)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return {
            "status": "error", 
            "error_message": str(e)
        }

def send_sms_tool(to_number: str, message: str) -> Dict[str, Any]:
    """SMS tool using Twilio for sending text messages."""
    try:
        result = send_sms(to_number, message)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"SMS send error: {e}")
        return {
            "status": "error",
            "error_message": str(e)
        }

def create_adk_agent(agent_config, user_id: str, agent_id: str) -> Agent:
    """Create an ADK Agent based on the agent configuration."""
    
    # Map tool names to actual functions
    tool_function_map = {
        "tavily_search": tavily_search_tool,
        "send_sms": send_sms_tool
    }
    
    # Handle both dictionary and object agent_config
    if isinstance(agent_config, dict):
        tools = agent_config.get('tools', [])
        system_prompt = agent_config.get('instructions', '')
    else:
        tools = agent_config.tools if hasattr(agent_config, 'tools') and agent_config.tools else []
        system_prompt = agent_config.system_prompt if hasattr(agent_config, 'system_prompt') else ''
    
    # Create ADK FunctionTools from available tools
    adk_tools = []
    if tools:
        for tool_name in tools:
            if tool_name in tool_function_map:
                adk_tools.append(FunctionTool(func=tool_function_map[tool_name]))
    
    # Create the ADK Agent using the standard approach
    model_config = adk_config.get_model_config()
    agent = Agent(
        name=f"agent_{agent_id}",
        model=model_config["model"],
        description=f"AI Agent for user {user_id}",
        instruction=system_prompt,
        tools=adk_tools,
    )
    
    return agent

@sio.on('connect', namespace='/text')
async def connect_text(sid, environ):
    logger.info(f"Text Chat Client connected: {sid}")
    logger.info(f"Connect environ: {environ.get('REMOTE_ADDR')} - {environ.get('HTTP_USER_AGENT', 'Unknown')}")

@sio.on('disconnect', namespace='/text')
def disconnect_text(sid):
    # Clean up sessions and cancel any active tasks
    if sid in active_chat_tasks:
        task = active_chat_tasks[sid]
        if not task.done():
            task.cancel()
        active_chat_tasks.pop(sid, None)
    
    chat_sessions.pop(sid, None)
    session_user_info.pop(sid, None)
    adk_runners.pop(sid, None)
    logger.info(f"Text Chat Client disconnected: {sid} - cleaned up session data")

# Add generic connection handlers to debug namespace routing
@sio.on('connect')
async def connect_generic(sid, environ):
    logger.info(f"GENERIC connection from {sid} - no namespace specified")
    
@sio.on('disconnect')
def disconnect_generic(sid):
    logger.info(f"GENERIC disconnection from {sid}")

# Add generic start_chat handler to redirect to correct namespace
@sio.on('start_chat')
async def start_chat_generic(sid, data):
    logger.info(f"Received start_chat on DEFAULT namespace from {sid}, processing directly")
    # Process the start_chat logic directly here for the default namespace
    agent_id = data.get('agent_id')
    user_id = data.get('user_id')
    
    logger.info(f"Processing start_chat for agent_id={agent_id}, user_id={user_id}")
    
    # Validate required data
    if not agent_id or not user_id:
        logger.error(f"Missing agent_id or user_id in start_chat data: {data}")
        await sio.emit('error', {'message': 'Missing agent_id or user_id'}, to=sid)
        return
    
    try:
        # Get database session
        db = get_db_session()
        
        # Get the agent configuration from database
        db_agent = crud_agent.get_agent_by_id(db=db, agent_id=agent_id)
        
        logger.info(f"DEBUG: db_agent type: {type(db_agent)}")
        logger.info(f"DEBUG: db_agent value: {db_agent}")
        
        if not db_agent:
            await sio.emit('error', {'message': 'Agent not found.'}, to=sid)
            db.close()
            return
        
        # Store session info
        session_user_info[sid] = {
            'user_id': user_id,
            'agent_id': agent_id,
            'db': db
        }
        
        # Setup the ADK session
        session_id = f"session_{sid}_{int(time.time())}"
        
        # Use the agent object directly
        agent_config = db_agent
        
        # Initialize ADK runner
        runner, session = await setup_adk_session(agent_config, str(user_id), str(agent_id))
        
        # Store the runner for this session
        adk_runners[sid] = {
            'runner': runner,
            'session': session,
            'agent_config': agent_config,
            'user_id': user_id,
            'agent_id': agent_id
        }
        
        logger.info(f"Chat session started for {sid} with agent {agent_id}")
        await sio.emit('chat_started', to=sid)
        
        db.close()
        
    except Exception as e:
        logger.error(f"Failed to start chat: {e}")
        await sio.emit('error', {'message': f"Failed to start chat: {e}"}, to=sid)

# Add generic chat_message handler to redirect to correct namespace
@sio.on('chat_message')
async def chat_message_generic(sid, data):
    logger.info(f"Received chat_message on DEFAULT namespace from {sid}, processing directly")
    
    if sid not in adk_runners:
        logger.error(f"No active chat session for {sid}")
        await sio.emit('error', {'message': 'No active chat session'}, to=sid)
        return
    
    session_info = adk_runners[sid]
    user_id = session_info['user_id']
    agent_id = session_info['agent_id']
    user_message = data.get('message', '')
    
    if not user_message.strip():
        logger.warning(f"Empty message from {sid}")
        await sio.emit('error', {'message': 'Message cannot be empty'}, to=sid)
        return
    
    logger.info(f"Processing chat_message: '{user_message}' from user {user_id} to agent {agent_id}")
    
    try:
        # Store the message in database
        db_session_info = session_user_info.get(sid)
        if db_session_info:
            db = db_session_info['db']
            
            # Save user message
            user_msg = ChatMessageCreate(
                message=user_message,
                role="user",
                agent_id=agent_id,
                user_id=user_id
            )
            crud_chat.create_chat_message(db=db, chat_message=user_msg)
            
        await sio.emit('status', {'status': 'Message received, processing...'}, to=sid)
        
        # Process the message with ADK runner
        runner = session_info['runner']
        session = session_info['session']
        
        # Start the task to process the message
        task = asyncio.create_task(process_agent_response(sid, user_message))
        active_chat_tasks[sid] = task
        
    except Exception as e:
        logger.error(f"Error in chat_message handler: {e}")
        await sio.emit('error', {'message': f"Error processing message: {e}"}, to=sid)

# Add test event handler
@sio.on('test_event', namespace='/text')
async def test_event(sid, data):
    logger.info(f"Test event received from {sid}: {data}")
    await sio.emit('test_response', {'message': 'Hello from server!'}, to=sid, namespace='/text')

async def setup_adk_session(agent_config, user_id: str, agent_id: str):
    """Initialize an ADK session using the standard Runner approach"""
    
    # Create ADK Agent
    adk_agent = create_adk_agent(agent_config, user_id, agent_id)
    
    # Create Runner using the simple approach
    app_name = f"adk_platform_agent_{agent_id}"
    runner = Runner(
        agent=adk_agent,
        session_service=session_service,
        app_name=app_name,
    )
    
    # Create session with initial state
    session_id = f"session_{agent_id}_{user_id}"
    session = await session_service.create_session(
        app_name=app_name,
        user_id=str(user_id),
        session_id=session_id,
        state={}
    )
    
    return runner, session

@sio.on('start_chat', namespace='/text')
async def start_chat(sid, data):
    logger.info(f"Received start_chat event from {sid} with data: {data}")
    agent_id = data.get('agent_id')
    user_id = data.get('user_id')
    
    logger.info(f"Starting chat for agent_id={agent_id}, user_id={user_id}")
    
    db = get_db_session()
    try:
        # Get agent configuration from database
        agent_config = crud_agent.get_agent_by_id(db, agent_id=agent_id)
        if not agent_config:
            logger.error(f"Agent {agent_id} not found in database")
            await sio.emit('error', {'message': 'Agent not found.'}, to=sid, namespace='/text')
            return

        logger.info(f"Found agent: {agent_config.name}")
        
        # Store user info for this session
        session_user_info[sid] = {'user_id': user_id, 'agent_id': agent_id}
        
        # Setup ADK session
        logger.info(f"Setting up ADK session for {sid}")
        runner, session = await setup_adk_session(agent_config, user_id, agent_id)
        
        # Store session data
        adk_runners[sid] = {
            'runner': runner,
            'session': session,
            'agent_config': agent_config,
        }
        
        logger.info(f"ADK session setup complete for {sid}")
        
        # Load and set chat history in session state
        history_from_db = crud_chat.get_chat_history_for_agent(db, agent_id=agent_id, owner_id=user_id)
        conversation_history = []
        for msg in history_from_db:
            conversation_history.append({
                "role": msg.role.replace("human", "user").replace("ai", "assistant"),
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
            })
        session.state.update({"conversation_history": conversation_history})
        
        await sio.emit('chat_started', to=sid, namespace='/text')
        logger.info(f"ADK chat session started for user {user_id}, agent {agent_id}")

    except Exception as e:
        logger.error(f"Failed to start chat: {e}")
        sentry_sdk.capture_exception(e)
        await sio.emit('error', {'message': f"Failed to start chat: {e}"}, to=sid, namespace='/text')
    finally:
        db.close()

async def process_runner_events(runner_events, sid, full_response_container, tool_calls):
    """Helper function to process ADK runner events with proper async iteration"""
    async for event in runner_events:
        try:
            # Log each event type for debugging
            logger.info(f"ADK Event received for {sid}: {type(event).__name__}")
            
            # Check if this event has content to process
            if event.content and event.content.parts:
                logger.info(f"Processing event with content for {sid}")
                
                for part in event.content.parts:
                    # Process text parts
                    if hasattr(part, 'text') and part.text:
                        text_chunk = part.text
                        full_response_container['response'] += text_chunk
                        # Stream the text token to client
                        await sio.emit('token', {'token': text_chunk}, to=sid, namespace='/text')
                        logger.debug(f"Sent text token: {text_chunk[:50]}...")
                        
                    # Handle function calls if present
                    elif hasattr(part, 'function_call') and part.function_call:
                        func_call = part.function_call
                        tool_call_data = {
                            "name": func_call.name,
                            "args": dict(func_call.args) if hasattr(func_call, 'args') else {}
                        }
                        tool_calls.append(tool_call_data)
                        await sio.emit('tool_start', {"name": func_call.name}, to=sid, namespace='/text')
                        logger.info(f"Tool call: {func_call.name}")
                        
                    # Handle function responses
                    elif hasattr(part, 'function_response') and part.function_response:
                        func_response = part.function_response
                        logger.info(f"Function response received: {func_response.name}")
            
            # Check if this is the end of the response
            elif not event.content:
                logger.info(f"Event without content received for {sid} - may indicate completion")
                
        except Exception as event_error:
            logger.error(f"Error processing event: {event_error}")
            await sio.emit('error', {'message': f"Error processing response event: {str(event_error)}"}, to=sid, namespace='/text')
    
    # Signal end of response after processing all events
    await sio.emit('stream_end', {'turn_complete': True}, to=sid, namespace='/text')
    logger.info(f"Response complete for {sid}, total length: {len(full_response_container['response'])}")

async def process_agent_response(sid, user_input):
    """Process agent response using the standard ADK Runner.run approach"""
    if sid not in adk_runners:
        await sio.emit('error', {'message': 'No active session'}, to=sid, namespace='/text')
        return

    runner_data = adk_runners[sid]
    runner = runner_data['runner']
    session = runner_data['session']
    user_info = session_user_info[sid]
    agent_config = runner_data['agent_config']

    start_time = time.time()
    full_response = ""
    tool_calls = []
    response_timeout = 60  # Seconds to wait before sending fallback response

    try:
        # Create the user message content
        user_message = genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=user_input)]
        )

        logger.info(f"Processing message for session {sid}: {user_input}")
        
        # Log detailed environment and configuration information
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        creds_exists = os.path.exists(creds_path) if creds_path else False
        logger.info(f"Google ADK credentials path: {creds_path}")
        logger.info(f"Credentials file exists: {creds_exists}")
        
        if creds_exists:
            logger.info(f"Credentials file size: {os.path.getsize(creds_path)} bytes")
            with open(creds_path, 'r') as f:
                creds_content = f.read()
                logger.debug(f"First 20 chars of credentials file: {creds_content[:20]}...")
                logger.info(f"Credentials file contains valid JSON: {bool(json.loads(creds_content))}")
        else:
            logger.error(f"Credentials file not found at {creds_path}")
            # Send a fallback response if credentials are missing
            await send_fallback_response(sid, user_input, "I'm sorry, but the AI service is not properly configured. Please contact support.")
            return
            
        # Log session information
        logger.info(f"Session ID: {session.id}")
        logger.info(f"User ID: {user_info['user_id']}")
        logger.info(f"Agent ID: {user_info['agent_id']}")
        
        # Log agent configuration
        logger.info(f"Agent name: {agent_config.name}")
        logger.info(f"Agent system prompt length: {len(agent_config.system_prompt)}")
        logger.info(f"Agent tools: {agent_config.tools}")
        
        # Log model configuration
        model_config = adk_config.get_model_config()
        logger.info(f"Using model: {model_config['model']}")
        
        # Use the standard runner.run approach but with timeout handling
        logger.info(f"Starting ADK Runner.run for session {sid}")
        
        # Send initial status to client
        await sio.emit('status', {'status': 'Generating response...'}, to=sid, namespace='/text')
        
        try:
            # Create a timeout for the entire ADK operation
            response_received = False
            
            # Execute the runner with an explicit timeout using asyncio.wait_for
            logger.info(f"Creating runner for user_id={user_info['user_id']}, session_id={session.id}")
            
            try:
                # Use runner.run_async() method which is the correct async approach
                runner_events = runner.run_async(
                    user_id=str(user_info['user_id']),
                    session_id=session.id,
                    new_message=user_message,
                )
                
                # Send status update to client
                await sio.emit('status', {'status': 'Processing response...'}, to=sid, namespace='/text')
                
                # Process events from the runner with timeout
                start_process_time = time.time()
                
                # Apply timeout to the entire async iteration using asyncio.wait_for
                full_response_container = {'response': ''}
                await asyncio.wait_for(
                    process_runner_events(runner_events, sid, full_response_container, tool_calls), 
                    timeout=response_timeout
                )
                full_response = full_response_container['response']
                response_received = True
            
            except asyncio.TimeoutError:
                logger.warning(f"ADK runner timed out for {sid} after {response_timeout} seconds")
                await send_fallback_response(sid, user_input, "I'm sorry, but I'm taking too long to respond. Let me try a simpler answer: How can I help you today?")
            
            except Exception as runner_error:
                logger.error(f"ADK runner error for {sid}: {runner_error}")
                await send_fallback_response(sid, user_input, f"I'm sorry, but I'm having trouble responding right now. Please try again later. (Error: {str(runner_error)[:100]})")
            
            # Check if we got a response
            if not response_received:
                logger.warning(f"No response received from ADK for {sid}")
                if not full_response:  # Only send fallback if we haven't already sent a response
                    await send_fallback_response(sid, user_input, "I apologize, but I didn't receive a response from the AI service. Let me know if you'd like to try again.")
        
        except Exception as outer_error:
            logger.error(f"Outer error running ADK for {sid}: {outer_error}")
            await send_fallback_response(sid, user_input, "I'm experiencing technical difficulties. Please try again in a moment.")
        
        # Final check - if still no response, send a fallback
        if not full_response:
            logger.warning(f"No response generated for {sid}")
            await send_fallback_response(sid, user_input, "I'm sorry, I'm having trouble generating a response. Please try again.")
            full_response = "Error: No response generated"

        # Save the complete response to database
        await save_agent_response(sid, full_response, tool_calls, start_time)
        
        logger.info(f"Successfully processed message for session {sid}")

    except Exception as e:
        logger.error(f"Error processing agent response for {sid}: {e}")
        sentry_sdk.capture_exception(e)
        await sio.emit('error', {'message': f"Agent processing error: {e}"}, to=sid, namespace='/text')

async def save_agent_response(sid, full_response, tool_calls, start_time):
    """Save the complete agent response to database"""
    if sid not in session_user_info:
        return
        
    user_info = session_user_info[sid]
    
    db = get_db_session()
    try:
        end_time = time.time()
        response_time = end_time - start_time
        token_count = len(full_response.split()) if full_response else 0
        
        # Save AI response to database
        crud_chat.create_chat_message(db, ChatMessageCreate(
            agent_id=user_info['agent_id'], 
            user_id=user_info['user_id'], 
            role='ai',
            content=full_response, 
            response_time_seconds=response_time,
            tool_calls=tool_calls, 
            token_usage={"total_tokens": token_count}
        ))
        db.commit()
        
        logger.info(f"Saved agent response for session {sid}, response time: {response_time:.2f}s")
        
    except Exception as e:
        logger.error(f"Error saving agent response for {sid}: {e}")
        sentry_sdk.capture_exception(e)
    finally:
        db.close()

@sio.on('chat_message', namespace='/text')
async def handle_chat_message(sid, data):
    logger.info(f"Received chat_message event from {sid} with data: {data}")
    
    if sid not in adk_runners:
        logger.error(f"No active chat session for {sid}")
        await sio.emit('error', {'message': 'No active chat session'}, to=sid, namespace='/text')
        return
    
    user_input = data.get('message')
    if not user_input:
        logger.warning(f"Empty message received from {sid}")
        return

    user_info = session_user_info[sid]
    logger.info(f"Processing message from user {user_info['user_id']} for agent {user_info['agent_id']}: '{user_input}'")

    db = get_db_session()
    try:
        # Save user message to database
        logger.debug(f"Saving message to database for agent_id={user_info['agent_id']}, user_id={user_info['user_id']}")
        crud_chat.create_chat_message(db, ChatMessageCreate(
            agent_id=user_info['agent_id'], 
            user_id=user_info['user_id'], 
            role='human', 
            content=user_input
        ))
        db.commit()
        
        logger.info(f"Saved user message for session {sid}: {user_input}")
        await sio.emit('status', {'status': 'Message received, processing...'}, to=sid, namespace='/text')
        
        # Cancel any existing chat processing task
        if sid in active_chat_tasks:
            task = active_chat_tasks[sid]
            if not task.done():
                logger.info(f"Cancelling previous task for {sid}")
                task.cancel()
        
        # Start processing the agent response
        logger.info(f"Starting agent response processing for {sid}")
        task = asyncio.create_task(process_agent_response(sid, user_input))
        active_chat_tasks[sid] = task
        logger.debug(f"Task created for {sid}: {task}")
        
        # Send confirmation to client that processing has started
        await sio.emit('status', {'status': 'Agent is thinking...'}, to=sid, namespace='/text')
        
    except Exception as e:
        logger.error(f"Chat message handling error for {sid}: {e}")
        sentry_sdk.capture_exception(e)
        await sio.emit('error', {'message': f"Message processing error: {e}"}, to=sid, namespace='/text')
    finally:
        db.close()

async def send_fallback_response(sid, user_input, response_text):
    """Send a fallback response when the ADK service fails to respond"""
    logger.warning(f"Sending fallback response to {sid}: '{response_text}'")
    
    # Stream the response to the client
    await sio.emit('token', {'token': response_text}, to=sid, namespace='/text')
    await sio.emit('stream_end', {'turn_complete': True}, to=sid, namespace='/text')
    
    # Save the fallback response to the database
    if sid in session_user_info:
        user_info = session_user_info[sid]
        db = get_db_session()
        try:
            # Save AI response to database
            crud_chat.create_chat_message(db, ChatMessageCreate(
                agent_id=user_info['agent_id'], 
                user_id=user_info['user_id'], 
                role='ai',
                content=response_text, 
                response_time_seconds=0,
                tool_calls=[], 
                token_usage={"total_tokens": len(response_text.split())}
            ))
            db.commit()
            logger.info(f"Saved fallback response to database for {sid}")
        except Exception as e:
            logger.error(f"Error saving fallback response: {e}")
        finally:
            db.close()

# Health check endpoint for ADK service
async def health_check():
    """Health check for ADK service."""
    return {
        "status": "healthy",
        "service": "adk_agent_service",
        "session_service": "available" if session_service else "unavailable",
        "active_sessions": len(adk_runners)
    }

# Export the socket.IO app for use in main.py
adk_sio = sio
