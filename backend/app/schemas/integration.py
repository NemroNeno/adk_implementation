from pydantic import BaseModel
from datetime import datetime

class UserIntegrationBase(BaseModel):
    service_name: str

class UserIntegrationCreate(UserIntegrationBase):
    token: str # The raw, unencrypted token from the user

class UserIntegration(UserIntegrationBase):
    id: int
    created_at: datetime
    # We never expose the token back to the client, even in encrypted form
    
    class Config:
        from_attributes = True