import socketio
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.base import Base, engine
from app.services.agent_service import sio

# This is a standard setup for a combined FastAPI + Socket.IO app
# 1. Create the FastAPI app
app = FastAPI(title="ADK AI Agent Platform")

# 2. Add standard HTTP middleware to the FastAPI app
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Include the FastAPI routers
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to the ADK AI Agent Platform API"}

# 4. Create the final Socket.IO ASGI app, wrapping the FastAPI app.
# This ensures Socket.IO handles WebSocket connections correctly at the root.
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)