from typing import List, Optional

from pydantic import BaseModel

try:
    # Pydantic v2
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover - fallback for pydantic v1
    ConfigDict = None


def orm_config():
    """Return pydantic config compatible with v1/v2."""
    if ConfigDict:
        return {"model_config": ConfigDict(from_attributes=True)}

    class _Cfg:
        orm_mode = True

    return {"Config": _Cfg}


class StudyCreate(BaseModel):
    name: str


class StudyResponse(BaseModel):
    id: str
    name: str

    if orm_config().get("model_config"):
        model_config = orm_config()["model_config"]
    else:  # pragma: no cover
        Config = orm_config()["Config"]


class MoveCreate(BaseModel):
    move_index: int
    fen_before: str
    move_san: str


class MoveResponse(BaseModel):
    move_index: int
    fen_before: str
    move_san: str

    if orm_config().get("model_config"):
        model_config = orm_config()["model_config"]
    else:  # pragma: no cover
        Config = orm_config()["Config"]


class StudyDetailResponse(BaseModel):
    id: str
    name: str
    moves: List[MoveResponse]

    if orm_config().get("model_config"):
        model_config = orm_config()["model_config"]
    else:  # pragma: no cover
        Config = orm_config()["Config"]


class StudyListItem(BaseModel):
    id: str
    name: str
    move_count: int
    updated_at: Optional[str] = None

    if orm_config().get("model_config"):
        model_config = orm_config()["model_config"]
    else:  # pragma: no cover
        Config = orm_config()["Config"]
