from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.token import Token
from app.schemas import user as user_schema  # Import the user schema module
from app.crud import crud_user
from app.core.security import create_access_token, verify_password
from app.api.deps import get_current_user
from app.db import models as db_models  # Import the database models module
from app.services.audit_service import log_activity  # ✅ NEW IMPORT

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = crud_user.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ✅ Log successful login
    log_activity(db, action="USER_LOGIN_PASSWORD", user_id=user.id)

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=user_schema.User)
def read_users_me(current_user: db_models.User = Depends(get_current_user)):
    return current_user
