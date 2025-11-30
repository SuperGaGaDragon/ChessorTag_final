import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


def gen_id() -> str:
    """Generate a lichess-like unique id for a Study."""
    return str(uuid.uuid4())


class Study(Base):
    __tablename__ = "studies"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    # TODO: add folder_id / owner_id when multi-user support is needed


class StudyMove(Base):
    __tablename__ = "study_moves"

    id = Column(Integer, primary_key=True, autoincrement=True)
    study_id = Column(String, ForeignKey("studies.id"), index=True)
    move_index = Column(Integer)  # 第几步
    fen_before = Column(Text)  # 这步之前的 FEN
    move_san = Column(String)  # SAN 或 UCI
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    study = relationship("Study")
