from sqlalchemy.orm import Session
from typing import List

from app.db import models
from app.schemas import chat as chat_schema # We will create this schema next

def create_chat_message(db: Session, message: chat_schema.ChatMessageCreate) -> models.ChatMessage:
    db_message = models.ChatMessage(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_chat_history_for_agent(db: Session, agent_id: int, owner_id: int) -> List[models.ChatMessage]:
    # Ensure user can only get history for their own agents
    return db.query(models.ChatMessage)\
        .join(models.Agent)\
        .filter(models.ChatMessage.agent_id == agent_id)\
        .filter(models.Agent.owner_id == owner_id)\
        .order_by(models.ChatMessage.timestamp.asc())\
        .all()