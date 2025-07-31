from pydantic import BaseModel

class ToolBase(BaseModel):
    name: str
    description: str
    # --- FIX: Add the function_name field that exists in your DB model ---
    function_name: str

class ToolCreate(ToolBase):
    pass # No changes needed here

class Tool(ToolBase):
    id: int
    is_public: bool # Add this field as well to match the DB

    class Config:
        from_attributes = True