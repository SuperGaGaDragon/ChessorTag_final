from uuid import uuid4

from sqlalchemy import Column, String, DateTime, func

# Reuse the shared Base so metadata.create_all picks up the users table.
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column("password_hash", String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
