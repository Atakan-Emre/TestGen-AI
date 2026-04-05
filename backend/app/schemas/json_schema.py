from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class JsonFileBase(BaseModel):
    name: str
    content: Dict[str, Any]
    size: int

class JsonFileCreate(JsonFileBase):
    pass

class JsonFileResponse(JsonFileBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 