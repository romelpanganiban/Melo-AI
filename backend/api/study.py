"""Study preferences and progress endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.errors import ValidationError
from core.validation import validate_uuid
from database.connection import get_db
from database.models import StudyProgress

router = APIRouter()


class StudyProgressRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=255)
    collection_id: Optional[str] = None
    completed_cards: int = Field(default=0, ge=0, le=100000)
    quiz_score: Optional[float] = Field(default=None, ge=0, le=100)


def _serialize(progress: StudyProgress) -> dict:
    return {
        "id": progress.id,
        "session_id": progress.session_id,
        "collection_id": progress.collection_id,
        "topic": progress.topic,
        "completed_cards": progress.completed_cards,
        "quiz_score": progress.quiz_score,
        "updated_at": progress.updated_at.isoformat(),
    }


@router.get("/study/progress/{session_id}", status_code=status.HTTP_200_OK)
def get_study_progress(session_id: str, collection_id: Optional[str] = None, db: Session = Depends(get_db)):
    session_id = validate_uuid(session_id, field_name="session_id")
    query = db.query(StudyProgress).filter(StudyProgress.session_id == session_id)
    if collection_id:
        collection_id = validate_uuid(collection_id, field_name="collection_id")
        query = query.filter(StudyProgress.collection_id == collection_id)
    return {"progress": [_serialize(item) for item in query.order_by(StudyProgress.updated_at.desc()).all()]}


@router.put("/study/progress/{session_id}", status_code=status.HTTP_200_OK)
def save_study_progress(session_id: str, request: StudyProgressRequest, db: Session = Depends(get_db)):
    session_id = validate_uuid(session_id, field_name="session_id")
    collection_id = validate_uuid(request.collection_id, field_name="collection_id") if request.collection_id else None
    progress = db.query(StudyProgress).filter(
        StudyProgress.session_id == session_id,
        StudyProgress.collection_id == collection_id,
        StudyProgress.topic == request.topic.strip(),
    ).first()
    if not progress:
        progress = StudyProgress(session_id=session_id, collection_id=collection_id, topic=request.topic.strip())
        db.add(progress)
    progress.completed_cards = request.completed_cards
    progress.quiz_score = request.quiz_score
    db.commit()
    db.refresh(progress)
    return _serialize(progress)