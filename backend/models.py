from sqlalchemy import Column, String, DateTime, Boolean, JSON
from datetime import datetime
from nanoid import generate

from .db import Base

def generate_study_id():
    # 生成 Lichess 风格的短 ID，例如 a7F3kL90bC
    return generate(size=10)

class Study(Base):
    __tablename__ = "studies"

    id = Column(String, primary_key=True, index=True, default=generate_study_id)

    title = Column(String, nullable=True)
    owner_id = Column(String, nullable=True)
    is_public = Column(Boolean, default=True)

    data = Column(JSON, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
