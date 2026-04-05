from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ScenarioBase(BaseModel):
    name: str
    content: str
    size: int

class ScenarioCreate(ScenarioBase):
    pass

class ScenarioResponse(ScenarioBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 