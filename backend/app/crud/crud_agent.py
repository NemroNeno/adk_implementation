from sqlalchemy.orm import Session
from app.db import models
from app.schemas import agent as agent_schema

def create_agent(db: Session, agent: agent_schema.AgentCreate, owner_id: int):
    db_agent = models.Agent(**agent.dict(), owner_id=owner_id)
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

def get_agents_by_owner(db: Session, owner_id: int):
    return db.query(models.Agent).filter(models.Agent.owner_id == owner_id).all()

def get_agent_by_id(db: Session, agent_id: int):
    return db.query(models.Agent).filter(models.Agent.id == agent_id).first()

# ... (existing imports and create/get functions) ...
from app.schemas import agent as agent_schema


def update_agent(db: Session, db_agent: models.Agent, agent_in: agent_schema.AgentUpdate) -> models.Agent:
    # Convert the Pydantic model to a dictionary, excluding any fields that weren't sent
    update_data = agent_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_agent, key, value)
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

def delete_agent(db: Session, agent_id: int) -> models.Agent:
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if agent:
        db.delete(agent)
        db.commit()
    return agent