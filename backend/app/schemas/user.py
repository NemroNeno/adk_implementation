from pydantic import BaseModel, EmailStr
from app.db.models import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None

class UserCreate(UserBase):
    password: str
    email: EmailStr
    full_name: str | None = None

class AdminCreate(UserBase):
    password: str
    email: EmailStr
    full_name: str | None = None

class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None

class User(UserBase):
    id: int
    role: UserRole
    # --- ADD THESE TWO LINES ---
    plan: str
    token_usage_this_month: int

    class Config:
        from_attributes = True