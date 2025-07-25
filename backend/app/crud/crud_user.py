from sqlalchemy.orm import Session
from app.db import models
from app.schemas import user as user_schema
from app.core.security import get_password_hash

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# Update create_user to accept an optional role
def create_user(db: Session, user: user_schema.UserCreate, role: models.UserRole = models.UserRole.user):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=role # Set the role here
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ... (existing crud functions) ...
from app.schemas.user import UserUpdate

def update_user(db: Session, db_user: models.User, user_in: UserUpdate) -> models.User:
    update_data = user_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ... (existing imports and functions) ...
from typing import List

def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

def delete_user(db: Session, user_id: int) -> models.User:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return user