from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BusinessRuleBase(BaseModel):
    name: str
    content: str
    source: str = "manual"
    is_active: bool = True

class BusinessRuleCreate(BusinessRuleBase):
    pass

class BusinessRuleUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None

class BusinessRuleResponse(BusinessRuleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
