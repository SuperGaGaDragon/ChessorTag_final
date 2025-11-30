from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from nanoid import generate
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .db import get_db
from .models import Folder, Study

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


# ---------- Pydantic Schemas ----------

class FolderBase(BaseModel):
    name: str
    parent_id: Optional[str] = None
    color: Optional[str] = None
    image_key: Optional[str] = None


class FolderCreate(FolderBase):
    pass


class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[str] = None
    color: Optional[str] = None
    image_key: Optional[str] = None


class FolderOut(FolderBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StudySummary(BaseModel):
    id: str
    name: Optional[str] = None
    folder_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkspaceSnapshot(BaseModel):
    folders: List[FolderOut]
    studies: List[StudySummary]


@router.get("/snapshot", response_model=WorkspaceSnapshot)
def get_workspace_snapshot(db: Session = Depends(get_db)):
    folders = db.query(Folder).all()
    studies = db.query(Study).all()
    return WorkspaceSnapshot(folders=folders, studies=studies)


@router.post("/folders", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
def create_folder(payload: FolderCreate, db: Session = Depends(get_db)):
    folder = Folder(
        id=generate(),
        name=payload.name,
        parent_id=payload.parent_id,
        color=payload.color,
        image_key=payload.image_key,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.patch("/folders/{folder_id}", response_model=FolderOut)
def update_folder(folder_id: str, payload: FolderUpdate, db: Session = Depends(get_db)):
    folder = db.query(Folder).filter(Folder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    if payload.name is not None:
        folder.name = payload.name
    if payload.parent_id is not None:
        folder.parent_id = payload.parent_id
    if payload.color is not None:
        folder.color = payload.color
    if payload.image_key is not None:
        folder.image_key = payload.image_key

    db.commit()
    db.refresh(folder)
    return folder


class StudyUpdate(BaseModel):
    name: Optional[str] = None
    folder_id: Optional[str] = None


@router.patch("/studies/{study_id}", response_model=StudySummary)
def update_study(study_id: str, payload: StudyUpdate, db: Session = Depends(get_db)):
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    if payload.name is not None:
        study.name = payload.name
    if payload.folder_id is not None:
        study.folder_id = payload.folder_id

    db.commit()
    db.refresh(study)
    return study
