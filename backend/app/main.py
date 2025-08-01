import socketio # <-- ADD THIS LINE
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.base import Base, engine
# Import the ADK-based Socket.IO server from your new adk_agent_service
from app.services.adk_agent_service import adk_sio, health_check

# Create the FastAPI app instance
app = FastAPI(title=settings.PROJECT_NAME)

# Add standard HTTP middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all your normal REST API routes
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
def on_startup():
    # This is a good practice to ensure tables are created
    Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to the ADK AI Agent Platform API"}

@app.get("/health/adk")
async def adk_health():
    """Health check for ADK agent service"""
    return await health_check()

# Create the final ASGI app by WRAPPING the FastAPI app with the ADK Socket.IO server.
# This makes the socket.io server handle /socket.io/ requests and fallback to FastAPI for others
socket_app = socketio.ASGIApp(adk_sio, other_asgi_app=app, socketio_path='/socket.io/')

# Export socket_app as the main app for uvicorn
app = socket_app