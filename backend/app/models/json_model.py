from sqlalchemy import Column, Integer, String, DateTime, JSON, BigInteger
from sqlalchemy.sql import func
from ..database import Base

class JsonFile(Base):
    __tablename__ = "json_files"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    content = Column(JSON)
    size = Column(BigInteger)
    # type = Column(String, default="default")  # Kaynak belirteci - DB'de henüz yok
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 