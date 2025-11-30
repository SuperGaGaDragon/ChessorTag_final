import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from .db import SessionLocal, engine
from .models import Base, Study, StudyMove
from .schemas import (
    MoveCreate,
    MoveResponse,
    StudyCreate,
    StudyDetailResponse,
    StudyListItem,
    StudyResponse,
)

# ensure tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Demo User Study API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Demo user backend running."}


@app.post("/api/studies", response_model=StudyResponse)
def create_study(payload: StudyCreate, db: Session = Depends(get_db)):
    """Create a new study."""
    study = Study(name=payload.name.strip() or "Untitled study")
    db.add(study)
    db.commit()
    db.refresh(study)
    return study


@app.get("/api/studies", response_model=List[StudyListItem])
def list_studies(db: Session = Depends(get_db)):
    """Return all studies for the demo user, newest first."""
    studies = db.query(Study).order_by(Study.updated_at.desc()).all()
    move_counts = {
        row.study_id: row.count
        for row in (
            db.query(StudyMove.study_id, func.count(StudyMove.id).label("count"))
            .group_by(StudyMove.study_id)
            .all()
        )
    }
    items: List[StudyListItem] = []
    for s in studies:
        items.append(
            StudyListItem(
                id=s.id,
                name=s.name,
                move_count=move_counts.get(s.id, 0),
                updated_at=s.updated_at.isoformat() if s.updated_at else None,
            )
        )
    return items


@app.post("/api/studies/{study_id}/moves")
def add_move(study_id: str, payload: MoveCreate, db: Session = Depends(get_db)):
    """Append a move to a study."""
    study = db.query(Study).filter_by(id=study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="study not found")

    move = StudyMove(
        study_id=study_id,
        move_index=payload.move_index,
        fen_before=payload.fen_before,
        move_san=payload.move_san,
    )
    db.add(move)
    study.updated_at = datetime.datetime.utcnow()
    db.commit()
    return {"ok": True}


@app.get("/api/studies/{study_id}", response_model=StudyDetailResponse)
def get_study(study_id: str, db: Session = Depends(get_db)):
    """Return a single study and its moves."""
    study = db.query(Study).filter_by(id=study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="study not found")

    moves = (
        db.query(StudyMove)
        .filter_by(study_id=study_id)
        .order_by(StudyMove.move_index.asc())
        .all()
    )
    return StudyDetailResponse(
        id=study.id,
        name=study.name,
        moves=[
            MoveResponse(
                move_index=m.move_index,
                fen_before=m.fen_before,
                move_san=m.move_san,
            )
            for m in moves
        ],
    )
