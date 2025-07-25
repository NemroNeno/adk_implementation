import socketio
import time
import traceback
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy.orm import Session
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_google_genai import ChatGoogleGenerativeAI
from app.tools.sms_tool import TwilioSmsTool
from app.core.config import settings
from app.db.base import SessionLocal
from app.crud import crud_agent, crud_chat
from app.schemas.chat import ChatMessageCreate
from app.services.alert_service import send_alert

# --- API KEY VALIDATION ---
if not settings.OPENAI_API_KEY or not settings.OPENAI_API_KEY.startswith("sk-"):
    raise ValueError("FATAL ERROR: OPENAI_API_KEY is not set or invalid in .env file.")
if not settings.TAVILY_API_KEY:
    raise ValueError("FATAL ERROR: TAVILY_API_KEY is not set in .env file.")

# --- Tool Registry ---
TOOL_REGISTRY = {
    "tavily_search": TavilySearchResults,
    "send_sms": TwilioSmsTool,
}
# ... (imports) ...

# --- THIS IS THE CRITICAL FIX ---
# We explicitly tell the Socket.IO server about our frontend's origin.
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["http://localhost:3000"]
)

agent_executors = {}
chat_histories = {}
session_user_info = {}

# --- Dependency for DB ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Socket.IO Events ---

@sio.event
async def connect(sid, environ):
    print(f"Socket connected: {sid}")

@sio.event
async def disconnect(sid):
    agent_executors.pop(sid, None)
    chat_histories.pop(sid, None)
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
        
        tools = []
        if agent_config.tools:
            for tool_key in agent_config.tools:
                if tool_key == "tavily_search":
                    tools.append(TavilySearchResults(max_results=3, api_key=settings.TAVILY_API_KEY))
        
        # --- THE FIX IS HERE: SWAP THE LLM ---
        # We are now instantiating the Google Gemini model instead of OpenAI.
        # "gemini-1.5-flash" is the latest, fastest, and most capable free model.
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            convert_system_message_to_human=True # Important for tool use with Gemini
        )
        # --- END OF FIX ---
        
        # The rest of the agent setup is exactly the same
        db_history = crud_chat.get_chat_history_for_agent(db, agent_id=agent_id, owner_id=user_id)
        langchain_history = [HumanMessage(content=msg.content) if msg.role == 'human' else AIMessage(content=msg.content) for msg in db_history]
        chat_histories[sid] = langchain_history

        # Gemini works best with a slightly different prompt structure for tools
        prompt = ChatPromptTemplate.from_messages([
            ("system", agent_config.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # The agent creation function is compatible with Gemini
        agent = create_openai_tools_agent(llm, tools, prompt) # This function name is a bit misleading, it works with any tool-calling LLM
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        agent_executors[sid] = agent_executor
        
        await sio.emit('chat_started', to=sid)
    finally:
        db.close()


@sio.on('chat_message')
async def handle_chat_message(sid, data):
    if sid not in agent_executors:
        return

    user_input = data.get('message')
    if not user_input:
        return

    agent_executor = agent_executors[sid]
    chat_history = chat_histories[sid]
    user_info = session_user_info[sid]

    start_time = time.time()
    full_response = ""

    try:
        async for chunk in agent_executor.astream({"input": user_input, "chat_history": chat_history}):
            if "output" in chunk:
                full_response += chunk["output"]
                await sio.emit('token', {'token': chunk["output"]}, to=sid)
    except Exception as e:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!! AGENT EXECUTION ERROR !!")
        traceback.print_exc()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        await sio.emit('error', {'message': "An error occurred while processing your request."}, to=sid)
        return

    print(f"[DEBUG] Agent finished successfully. Full response generated.")
    end_time = time.time()
    response_time = end_time - start_time

    await sio.emit('stream_end', {
        'metrics': {
            'response_time_seconds': round(response_time, 4)
        }
    })

    # Save chat to DB
    chat_history.extend([
        HumanMessage(content=user_input),
        AIMessage(content=full_response)
    ])

    db_gen = get_db()
    db = next(db_gen)
    try:
        human_msg = ChatMessageCreate(
            agent_id=user_info['agent_id'],
            user_id=user_info['user_id'],
            role='human',
            content=user_input
        )
        crud_chat.create_chat_message(db, message=human_msg)

        ai_msg = ChatMessageCreate(
            agent_id=user_info['agent_id'],
            user_id=user_info['user_id'],
            role='ai',
            content=full_response,
            response_time_seconds=response_time
        )
        crud_chat.create_chat_message(db, message=ai_msg)

        print(f"[DEBUG] Saved conversation to database.")
    finally:
        next(db_gen, None)
