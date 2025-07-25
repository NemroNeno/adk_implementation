from sqlalchemy.orm import Session
from typing import List

from app.db import models
from app.schemas import integration as integration_schema
from app.services.encryption_service import encrypt_token

def create_user_integration(db: Session, integration: integration_schema.UserIntegrationCreate, owner_id: int) -> models.UserIntegration:
    """
    Encrypts the user's token and saves the integration to the database.
    """
    encrypted_token = encrypt_token(integration.token)
    
    db_integration = models.UserIntegration(
        service_name=integration.service_name.upper(),
        encrypted_token=encrypted_token,
        owner_id=owner_id
    )
    db.add(db_integration)
    db.commit()
    db.refresh(db_integration)
    return db_integration

def get_integrations_by_owner(db: Session, owner_id: int) -> List[models.UserIntegration]:
    """
    Retrieves all integrations for a specific user.
    """
    return db.query(models.UserIntegration).filter(models.UserIntegration.owner_id == owner_id).all()

def delete_integration(db: Session, integration_id: int, owner_id: int) -> models.UserIntegration:
    """
    Deletes an integration, ensuring it belongs to the correct owner.
    """
    db_integration = db.query(models.UserIntegration).filter(
        models.UserIntegration.id == integration_id,
        models.UserIntegration.owner_id == owner_id
    ).first()
    
    if db_integration:
        db.delete(db_integration)
        db.commit()
    
    return db_integration