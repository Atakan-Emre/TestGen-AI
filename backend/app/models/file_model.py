from sqlalchemy import Column, Integer, String, DateTime, JSON, BigInteger, Enum, Text, ForeignKey
from sqlalchemy.sql import func
from ..database import Base
import enum

class FileType(str, enum.Enum):
    json = "json"
    csv = "csv"
    txt = "txt"

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(FileType), nullable=False)
    content = Column(Text, nullable=True)
    json_content = Column(JSON, nullable=True)
    size = Column(BigInteger)
    hash = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

class NLPResult(Base):
    __tablename__ = "nlp_results"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"))
    model_name = Column(String, nullable=False)
    analysis_result = Column(JSON)
    processed_at = Column(DateTime(timezone=True), server_default=func.now()) 