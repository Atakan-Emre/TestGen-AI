from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Any
from ..database import Base

class JsonFile(Base):
    __tablename__ = "json_files"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    content = Column(JSONB)
    size = Column(BigInteger)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class JsonFileResponse(BaseModel):
    id: int
    name: str
    content: Any
    size: int
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True) 