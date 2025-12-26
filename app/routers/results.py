from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func

from app.core.database import get_db
from app.models.all import CompatibilityResult, LogEntry, MCVersion, Mod
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
    ).join(
        Mod, (CompatibilityResult.mod_slug == Mod.slug) & (CompatibilityResult.loader == Mod.loader)
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
    # Subquery to get max checked_at per mod/loader for this mc_version
    subq = db.query(
        CompatibilityResult.mod_slug,
        CompatibilityResult.loader,
        func.max(CompatibilityResult.checked_at).label("max_checked")
    ).filter(CompatibilityResult.mc_version == mc_version).group_by(
        CompatibilityResult.mod_slug,
        CompatibilityResult.loader
    ).subquery()
    
    latest_results = db.query(CompatibilityResult, Mod).join(
        subq,
        (CompatibilityResult.mod_slug == subq.c.mod_slug) & 
        (CompatibilityResult.loader == subq.c.loader) & 
        (CompatibilityResult.checked_at == subq.c.max_checked)
    ).join(
        Mod, (CompatibilityResult.mod_slug == Mod.slug) & (CompatibilityResult.loader == Mod.loader)
    ).all()
    
    compatible = sum(1 for r, m in latest_results if r.status == "compatible")
    total = len(latest_results)
    
    server_compatible = sum(1 for r, m in latest_results if r.status == "compatible" and m.side in ["server", "both"])
    server_total = sum(1 for r, m in latest_results if m.side in ["server", "both"])
    
    client_compatible = sum(1 for r, m in latest_results if r.status == "compatible" and m.side in ["client", "both"])
    client_total = sum(1 for r, m in latest_results if m.side in ["client", "both"])
    
    return SummaryResponse(
        compatible=compatible, 
        total=total,
        server_compatible=server_compatible,
        server_total=server_total,
        client_compatible=client_compatible,
        client_total=client_total
    )

@router.get("/api/logs", response_model=List[LogResponse])
def get_logs(db: Session = Depends(get_db)):
    """Get background job logs"""
    logs = db.query(LogEntry).order_by(LogEntry.created_at.desc()).limit(100).all()
    return logs
