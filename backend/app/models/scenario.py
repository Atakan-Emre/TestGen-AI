from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from ..database import Base
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class Scenario(Base):
    __tablename__ = "scenarios"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    file_path = Column(String)
    csv_file_id = Column(Integer, ForeignKey("csv_files.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ScenarioCreate(BaseModel):
    name: str
    description: str
    csv_file_id: Optional[int] = None

class ScenarioResponse(BaseModel):
    id: int
    name: str
    description: str
    file_path: str
    csv_file_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True) 