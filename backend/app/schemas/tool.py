from pydantic import BaseModel

class ToolBase(BaseModel):
    name: str
    description: str

class ToolCreate(ToolBase):
    langchain_key: str

class Tool(ToolBase):
    id: int
    langchain_key: str

    class Config:
        from_attributes = True