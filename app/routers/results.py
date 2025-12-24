from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.all import CompatibilityResult, LogEntry
from app.schemas.all import ResultResponse, LogResponse

router = APIRouter(
    tags=["results"]
)

@router.get("/api/results", response_model=List[ResultResponse])
def get_results(db: Session = Depends(get_db)):
    """Get all compatibility check results"""
    results = db.query(CompatibilityResult).order_by(CompatibilityResult.checked_at.desc()).all()
    return results

@router.get("/api/logs", response_model=List[LogResponse])
def get_logs(db: Session = Depends(get_db)):
    """Get background job logs"""
    logs = db.query(LogEntry).order_by(LogEntry.created_at.desc()).limit(100).all()
    return logs
