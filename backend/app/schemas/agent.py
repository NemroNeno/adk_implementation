from pydantic import BaseModel
from typing import List, Optional

class AgentBase(BaseModel):
    name: str
    system_prompt: str
    tools: Optional[List[str]] = []

class AgentCreate(AgentBase):
    pass

# --- ADD THIS NEW SCHEMA ---
# All fields are optional, so the user can update just the name, or just the tools, etc.
class AgentUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    tools: Optional[List[str]] = None

class Agent(AgentBase):
    id: int
    owner_id: int
    class Config:
        from_attributes = True