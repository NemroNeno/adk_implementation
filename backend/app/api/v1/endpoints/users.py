from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from pydantic import EmailStr

from app.api.permissions import allow_admin_only # Import our new dependency
from typing import List  # <-- ADD THIS IMPORT (or add 'List' if 'typing' is already imported)


from app.db.base import get_db
from app.schemas import user as user_schema
from app.crud import crud_user
from app.db.models import UserRole
from app.db import models  # <-- ADD THIS LINE

router = APIRouter()

@router.post("/", response_model=user_schema.User, status_code=status.HTTP_201_CREATED)
def create_user_account(
    db: Session = Depends(get_db),
    # Explicitly define the expected body fields instead of using a model
    full_name: str = Body(...),
    email: EmailStr = Body(...),
    password: str = Body(...)
):
    db_user = crud_user.get_user_by_email(db, email=email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create the schema object manually from the body fields
    user_in = user_schema.UserCreate(full_name=full_name, email=email, password=password)
    return crud_user.create_user(db=db, user=user_in, role=UserRole.user)


@router.post("/admin", response_model=user_schema.User, status_code=status.HTTP_201_CREATED)
def create_admin_account(
    db: Session = Depends(get_db),
    # Also be explicit here
    full_name: str = Body(...),
    email: EmailStr = Body(...),
    password: str = Body(...)
):
    db_user = crud_user.get_user_by_email(db, email=email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    user_in = user_schema.AdminCreate(full_name=full_name, email=email, password=password)
    return crud_user.create_user(db=db, user=user_in, role=UserRole.admin)

# ... (existing imports) ...
from app.api.deps import get_current_user

# ... (existing user creation endpoints) ...

# We already have a "/me" endpoint in login.py, which is fine.
@router.put("/me", response_model=user_schema.User)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: user_schema.UserUpdate,
    current_user: models.User = Depends(get_current_user) # Now 'models' is defined
):
    user = crud_user.update_user(db=db, db_user=current_user, user_in=user_in)
    return user


@router.get("/", response_model=List[user_schema.User], dependencies=[Depends(allow_admin_only)])
def read_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve all users. Accessible only by admins.
    """
    users = crud_user.get_all_users(db, skip=skip, limit=limit)
    return users

@router.delete("/{user_id}", response_model=user_schema.User, dependencies=[Depends(allow_admin_only)])
def delete_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a user by ID. Accessible only by admins.
    """
    user = crud_user.delete_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ... (existing imports and other endpoints) ...

# --- ADD THIS NEW ENDPOINT ---
@router.post("/viewer", response_model=user_schema.User, status_code=status.HTTP_201_CREATED)
def create_viewer_account(
    user: user_schema.UserCreate, # We can reuse the standard UserCreate schema
    db: Session = Depends(get_db)
):
    """
    Creates a new user with the 'viewer' role.
    """
    db_user = crud_user.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Call the existing CRUD function, but explicitly pass the viewer role
    return crud_user.create_user(db=db, user=user, role=UserRole.viewer)