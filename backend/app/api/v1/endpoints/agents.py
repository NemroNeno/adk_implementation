from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.base import get_db
from app.schemas import agent as agent_schema, chat as chat_schema
from app.crud import crud_agent, crud_chat
from app.api.deps import get_current_user
from app.db.models import User, UserRole
from app.db import models
from app.services.audit_service import log_activity
from app.api.permissions import allow_user_and_admin, allow_all_roles, UsageChecker

router = APIRouter()

check_agent_limit = UsageChecker(check_agents=True)

@router.post("/", response_model=agent_schema.Agent, dependencies=[Depends(allow_user_and_admin), Depends(check_agent_limit)])
def create_agent(
    agent_in: agent_schema.AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_agent = crud_agent.create_agent(db=db, agent=agent_in, owner_id=current_user.id)
    log_activity(db, action="AGENT_CREATE", user_id=current_user.id, agent_id=new_agent.id, details={"agent_name": new_agent.name})
    return new_agent

@router.get("/", response_model=List[agent_schema.Agent], dependencies=[Depends(allow_all_roles)])
def read_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve agents.
    - Admins and Viewers see all agents.
    - Users see only their own agents.
    """
    if current_user.role in [UserRole.admin, UserRole.viewer]:
        return db.query(models.Agent).all()
    else: # UserRole.user
        return crud_agent.get_agents_by_owner(db=db, owner_id=current_user.id)

@router.get("/{agent_id}", response_model=agent_schema.Agent, dependencies=[Depends(allow_all_roles)])
def read_agent_by_id(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific agent by ID.
    - Admins and Viewers can see any agent.
    - Users can only see their own.
    """
    agent = crud_agent.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # --- THE FIX IS HERE ---
    if current_user.role == UserRole.user and agent.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this agent")
        
    return agent

@router.get("/{agent_id}/history", response_model=List[chat_schema.ChatMessage], dependencies=[Depends(allow_all_roles)])
def get_agent_chat_history(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve chat history for a specific agent.
    - Admins and Viewers can see any history.
    - Users can only see history for their own agents.
    """
    agent = crud_agent.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    # --- AND THE FIX IS HERE TOO ---
    if current_user.role == UserRole.user and agent.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this agent's history")

    history = db.query(models.ChatMessage)\
        .filter(models.ChatMessage.agent_id == agent_id)\
        .order_by(models.ChatMessage.timestamp.asc())\
        .all()
    return history


# ... (existing imports and create/get endpoints) ...
# ... (existing imports and GET/POST endpoints) ...

# --- ADD THE UPDATE (PUT) ENDPOINT ---
@router.put("/{agent_id}", response_model=agent_schema.Agent, dependencies=[Depends(allow_user_and_admin)])
def update_user_agent(
    agent_id: int,
    agent_in: agent_schema.AgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an agent. A regular user can only update their own agents.
    """
    agent = crud_agent.get_agent_by_id(db, agent_id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized to update this agent")
        
    updated_agent = crud_agent.update_agent(db=db, db_agent=agent, agent_in=agent_in)
    log_activity(db, "AGENT_UPDATE", user_id=current_user.id, agent_id=agent_id, details={"updated_fields": agent_in.dict(exclude_unset=True)})
    return updated_agent

# --- ADD THE DELETE ENDPOINT ---
@router.delete("/{agent_id}", response_model=agent_schema.Agent, dependencies=[Depends(allow_user_and_admin)])
def delete_user_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an agent. A regular user can only delete their own agents.
    """
    agent = crud_agent.get_agent_by_id(db, agent_id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this agent")
        
    deleted_agent = crud_agent.delete_agent(db=db, agent_id=agent_id)
    log_activity(db, "AGENT_DELETE", user_id=current_user.id, agent_id=agent_id, details={"deleted_agent_name": deleted_agent.name})
    return deleted_agent