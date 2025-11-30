from sqlalchemy import Column, String, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship, synonym
from datetime import datetime
from nanoid import generate

from .db import Base

def generate_study_id():
    # 生成 Lichess 风格的短 ID，例如 a7F3kL90bC
    return generate(size=10)

class Study(Base):
    __tablename__ = "studies"

    id = Column(String, primary_key=True, index=True, default=generate_study_id)
    name = Column(String, nullable=True)
    folder_id = Column(String, ForeignKey("folders.id"), nullable=True)

    payload = Column("data", JSON, nullable=False)
    data = synonym("payload")

    title = Column(String, nullable=True)
    owner_id = Column(String, nullable=True)
    is_public = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    folder = relationship("Folder", back_populates="studies", lazy="joined")


class Folder(Base):
    __tablename__ = "folders"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)

    parent_id = Column(String, ForeignKey("folders.id"), nullable=True)
    color = Column(String, nullable=True)
    image_key = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = relationship("Folder", remote_side=[id], backref="children", lazy="selectin")
    studies = relationship("Study", back_populates="folder", lazy="selectin")
