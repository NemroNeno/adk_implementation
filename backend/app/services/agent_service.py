import socketio
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy.orm import Session

# --- THE FIX IS HERE ---
# The correct class name to import is TavilySearchAPIWrapper,
# and we create a LangChain Tool object from it.
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain.agents import Tool as LangChainTool
from app.tools.sms_tool import TwilioSmsTool

from app.core.config import settings
from app.db.base import SessionLocal
# ... (rest of imports)

# --- Updated Tool Registry with correct instantiation ---
# We define a function to create the tool to avoid circular dependencies
def get_tavily_tool():
    search = TavilySearchAPIWrapper(tavily_api_key=settings.TAVILY_API_KEY)
    return LangChainTool(
        name="tavily_search",
        func=search.run,
        description="A powerful search engine for finding real-time information."
    )

TOOL_REGISTRY = {
    "tavily_search": get_tavily_tool, # Store the function
    "send_sms": TwilioSmsTool,
}

# ... (sio definition and the rest of the file)

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="http://localhost:3000")
agent_executors = {}
chat_histories = {}
session_user_info = {}

def get_db(): return SessionLocal()

@sio.event
async def connect(sid, environ): print(f"Socket connected: {sid}")

@sio.event
async def disconnect(sid):
    if sid in agent_executors: del agent_executors[sid]
    if sid in chat_histories: del chat_histories[sid]
    if sid in session_user_info: del session_user_info[sid]
    print(f"Socket disconnected: {sid}")

@sio.on('start_chat')
async def start_chat(sid, data):
    agent_id = data.get('agent_id')
    user_id = data.get('user_id')
    if not agent_id or not user_id: return
    
    db = get_db()
    try:
        agent_config = crud_agent.get_agent_by_id(db, agent_id=agent_id)
        if not agent_config or agent_config.owner_id != user_id: return

        session_user_info[sid] = {'user_id': user_id, 'agent_id': agent_id}
        
        # ... (inside start_chat)
        tools = []
        if agent_config.tools:
            for tool_key in agent_config.tools:
                if tool_key in TOOL_REGISTRY:
                    # --- THE FIX ---
                    # Call the function from the registry to get the tool instance
                    tool_instance_or_creator = TOOL_REGISTRY[tool_key]
                    if callable(tool_instance_or_creator):
                        tools.append(tool_instance_or_creator())
                    else:
                        tools.append(tool_instance_or_creator) # For class-based tools like Twilio
# ... (rest of the function))
        
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=settings.GOOGLE_API_KEY, convert_system_message_to_human=True)
        
        db_history = crud_chat.get_chat_history_for_agent(db, agent_id=agent_id, owner_id=user_id)
        langchain_history = [HumanMessage(content=msg.content) if msg.role == 'human' else AIMessage(content=msg.content) for msg in db_history]
        chat_histories[sid] = langchain_history

        prompt = ChatPromptTemplate.from_messages([
            ("system", agent_config.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # --- THE FIX IS HERE: Use the modern agent constructor ---
        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        agent_executors[sid] = agent_executor
        
        await sio.emit('chat_started', to=sid)
    finally:
        db.close()

# The handle_chat_message function remains the same as the simplified 'astream' version
@sio.on('chat_message')
async def handle_chat_message(sid, data):
    if sid not in agent_executors: return

    user_input = data.get('message')
    if not user_input: return

    agent_executor = agent_executors[sid]
    chat_history = chat_histories[sid]
    user_info = session_user_info[sid]
    
    start_time = time.time()
    full_response = ""
    
    try:
        async for chunk in agent_executor.astream({"input": user_input, "chat_history": chat_history}):
            if "output" in chunk:
                content = chunk["output"]
                full_response += content
                await sio.emit('token', {'token': content}, to=sid)
    except Exception as e:
        print(f"!! AGENT EXECUTION ERROR: {e}")
        send_alert(level="critical", message="Agent execution failed", details={"error": str(e), "user_id": user_info.get('user_id'), "agent_id": user_info.get('agent_id')})
        await sio.emit('error', {'message': "An error occurred while processing your request."}, to=sid)
        return

    end_time = time.time()
    response_time = end_time - start_time
    
    await sio.emit('stream_end', { 'metrics': { 'response_time_seconds': round(response_time, 4), 'tool_calls': [], 'token_usage': {} } })

    # Save to DB (unchanged)
    # ...