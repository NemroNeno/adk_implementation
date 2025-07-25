from sqlalchemy.orm import Session
from typing import List

from app.db import models
from app.schemas import tool as tool_schema

def create_tool(db: Session, tool: tool_schema.ToolCreate) -> models.Tool:
    db_tool = models.Tool(**tool.dict())
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    return db_tool

def get_public_tools(db: Session) -> List[models.Tool]:
    return db.query(models.Tool).filter(models.Tool.is_public == True).all()

def get_tool_by_langchain_key(db: Session, key: str) -> models.Tool:
    return db.query(models.Tool).filter(models.Tool.langchain_key == key).first()