from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger
from sqlalchemy.sql import func
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from ..database import Base

class CsvFile(Base):
    __tablename__ = "csv_files"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    content = Column(Text)
    size = Column(BigInteger)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class CsvFileResponse(BaseModel):
    id: int
    name: str
    content: str
    size: int
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True) 