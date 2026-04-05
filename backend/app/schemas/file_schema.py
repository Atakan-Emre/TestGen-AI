from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from ..models.file_model import FileType

class FileBase(BaseModel):
    name: str
    type: FileType
    size: int
    hash: str

class FileCreate(FileBase):
    content: Optional[str] = None
    json_content: Optional[Dict[str, Any]] = None

class FileResponse(FileBase):
    id: int
    content: Optional[str] = None
    json_content: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True 