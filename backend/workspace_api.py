from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import uuid4

from .auth_api import get_current_user
from .auth_models import User
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
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
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
def get_workspace_snapshot(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    folders = db.query(Folder).filter(Folder.owner_id == current_user.id).all()
    studies = db.query(Study).filter(Study.owner_id == current_user.id).all()
    return WorkspaceSnapshot(folders=folders, studies=studies)


@router.post("/folders", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
def create_folder(
    payload: FolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        if payload.parent_id:
            parent = (
                db.query(Folder)
                .filter(Folder.id == payload.parent_id, Folder.owner_id == current_user.id)
                .first()
            )
            if not parent:
                raise HTTPException(status_code=404, detail="Parent folder not found")

        folder = Folder(
            id=str(uuid4()),
            name=payload.name,
            parent_id=payload.parent_id,
            color=payload.color,
            image_key=payload.image_key,
            owner_id=current_user.id,
        )
        db.add(folder)
        db.commit()
        db.refresh(folder)
        return folder
    except HTTPException:
        # let HTTP errors propagate
        raise
    except Exception as exc:  # surface server-side errors to help debugging
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create folder: {exc}")


@router.patch("/folders/{folder_id}", response_model=FolderOut)
def update_folder(
    folder_id: str,
    payload: FolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    folder = (
        db.query(Folder)
        .filter(Folder.id == folder_id, Folder.owner_id == current_user.id)
        .first()
    )
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    if payload.parent_id:
        parent = (
            db.query(Folder)
            .filter(Folder.id == payload.parent_id, Folder.owner_id == current_user.id)
            .first()
        )
        if not parent:
            raise HTTPException(status_code=404, detail="Parent folder not found")

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


class StudyCreate(BaseModel):
    name: str
    folder_id: Optional[str] = None


class StudyUpdate(BaseModel):
    name: Optional[str] = None
    folder_id: Optional[str] = None


@router.post("/studies", response_model=StudySummary, status_code=status.HTTP_201_CREATED)
def create_study(
    payload: StudyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new study"""
    try:
        # Validate folder_id if provided
        if payload.folder_id:
            folder = (
                db.query(Folder)
                .filter(Folder.id == payload.folder_id, Folder.owner_id == current_user.id)
                .first()
            )
            if not folder:
                raise HTTPException(status_code=404, detail="Folder not found")

        # Create new study
        study = Study(
            name=payload.name,
            folder_id=payload.folder_id,
            owner_id=current_user.id,
            data={},  # Initialize with empty data
            is_public=False,  # Default to private
        )
        db.add(study)
        db.commit()
        db.refresh(study)
        return study
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create study: {exc}")


@router.patch("/studies/{study_id}", response_model=StudySummary)
def update_study(
    study_id: str,
    payload: StudyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    study = (
        db.query(Study)
        .filter(Study.id == study_id, Study.owner_id == current_user.id)
        .first()
    )
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    if payload.folder_id:
        folder = (
            db.query(Folder)
            .filter(Folder.id == payload.folder_id, Folder.owner_id == current_user.id)
            .first()
        )
        if not folder:
            raise HTTPException(status_code=404, detail="Target folder not found")

    if payload.name is not None:
        study.name = payload.name
    if payload.folder_id is not None:
        study.folder_id = payload.folder_id

    db.commit()
    db.refresh(study)
    return study
