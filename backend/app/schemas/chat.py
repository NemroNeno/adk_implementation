from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict, List, Optional

class ChatMessageBase(BaseModel):
    # ... (no change)
    agent_id: int
    user_id: int
    role: str 
    content: str

class ChatMessageCreate(ChatMessageBase):
    response_time_seconds: Optional[float] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    # --- ADD THIS FIELD ---
    token_usage: Optional[Dict[str, int]] = None

class ChatMessage(ChatMessageBase):
    id: int
    timestamp: datetime
    response_time_seconds: Optional[float] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    # --- ADD THIS FIELD ---
    token_usage: Optional[Dict[str, int]] = None

    class Config:
        from_attributes = True