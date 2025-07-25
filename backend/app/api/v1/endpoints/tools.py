from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.base import get_db
from app.schemas import tool as tool_schema
from app.crud import crud_tool

router = APIRouter()

@router.get("/", response_model=List[tool_schema.Tool])
def read_public_tools(db: Session = Depends(get_db)):
    """
    Retrieve a list of all publicly available tools.
    """
    return crud_tool.get_public_tools(db)