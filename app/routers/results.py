from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func

from app.core.database import get_db
from app.models.all import CompatibilityResult, LogEntry, MCVersion
from app.schemas.all import ResultResponse, LogResponse, SummaryResponse

router = APIRouter(
    tags=["results"]
)

@router.get("/api/results", response_model=List[ResultResponse])
def get_results(
    mc_version: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get compatibility check results with filtering and sorting"""
    query = db.query(CompatibilityResult).join(
        MCVersion, CompatibilityResult.mc_version == MCVersion.version, isouter=True
    )
    
    if mc_version:
        query = query.filter(CompatibilityResult.mc_version == mc_version)
    
    # Sort by mod name (slug) ASC, then by MC version release time DESC, then by checked_at DESC
    results = query.order_by(
        CompatibilityResult.mod_slug.asc(),
        MCVersion.release_time.desc(),
        CompatibilityResult.checked_at.desc()
    ).all()
    
    return results

@router.get("/api/results/summary", response_model=SummaryResponse)
def get_summary(mc_version: str, db: Session = Depends(get_db)):
    """Get compatibility summary for a specific Minecraft version"""
    # We want latest result per mod/loader for this version
    # Since we don't have a direct "latest" flag, we can group by mod_slug and loader
    # For SQLite, it's a bit tricky to get the latest per group in one query with counts easily without subqueries
    
    # A simpler way (since data is small) is to fetch all for this version and filter in memory,
    # or use a subquery. 
    
    # Subquery to get max checked_at per mod/loader for this mc_version
    subq = db.query(
        CompatibilityResult.mod_slug,
        CompatibilityResult.loader,
        func.max(CompatibilityResult.checked_at).label("max_checked")
    ).filter(CompatibilityResult.mc_version == mc_version).group_by(
        CompatibilityResult.mod_slug,
        CompatibilityResult.loader
    ).subquery()
    
    latest_results = db.query(CompatibilityResult).join(
        subq,
        (CompatibilityResult.mod_slug == subq.c.mod_slug) & 
        (CompatibilityResult.loader == subq.c.loader) & 
        (CompatibilityResult.checked_at == subq.c.max_checked)
    ).all()
    
    compatible = sum(1 for r in latest_results if r.status == "compatible")
    total = len(latest_results)
    
    return SummaryResponse(compatible=compatible, total=total)

@router.get("/api/logs", response_model=List[LogResponse])
def get_logs(db: Session = Depends(get_db)):
    """Get background job logs"""
    logs = db.query(LogEntry).order_by(LogEntry.created_at.desc()).limit(100).all()
    return logs
