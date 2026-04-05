from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CsvFileBase(BaseModel):
    name: str
    content: str
    size: int

class CsvFileCreate(CsvFileBase):
    pass

class CsvFileResponse(CsvFileBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 