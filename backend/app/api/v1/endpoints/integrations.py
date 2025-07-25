from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.base import get_db
from app.schemas import integration as integration_schema
from app.crud import crud_integration
from app.api.deps import get_current_user
from app.db.models import User

router = APIRouter()

@router.post("/", response_model=integration_schema.UserIntegration, status_code=status.HTTP_201_CREATED)
def create_integration(
    integration_in: integration_schema.UserIntegrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new integration for the current user, storing an encrypted token.
    """
    return crud_integration.create_user_integration(db=db, integration=integration_in, owner_id=current_user.id)

@router.get("/", response_model=List[integration_schema.UserIntegration])
def read_user_integrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all integrations for the current user.
    """
    return crud_integration.get_integrations_by_owner(db=db, owner_id=current_user.id)

@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Revoke/delete an integration for the current user.
    """
    deleted_integration = crud_integration.delete_integration(db=db, integration_id=integration_id, owner_id=current_user.id)
    if not deleted_integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return