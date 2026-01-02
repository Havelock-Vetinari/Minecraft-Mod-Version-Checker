from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func

from app.core.database import get_db
from app.models.all import CompatibilityResult, LogEntry, MCVersion, TrackedMod, ModVersion
from app.schemas.all import ResultResponse, LogResponse, SummaryResponse, StatusResponse
from datetime import timedelta, timezone

router = APIRouter(
    tags=["results"]
)

@router.get("/api/status", response_model=StatusResponse)
def get_status(db: Session = Depends(get_db)):
    """Get background job status (last and next check)"""
    last_log = db.query(LogEntry).filter(
        LogEntry.message == "Compatibility check completed"
    ).order_by(LogEntry.created_at.desc()).first()
    
    last_check = last_log.created_at.replace(tzinfo=timezone.utc) if last_log else None
    next_check = last_check + timedelta(minutes=5) if last_check else None
    
    return StatusResponse(last_check=last_check, next_check=next_check)


@router.get("/api/results", response_model=List[ResultResponse])
def get_results(
    mc_version: Optional[str] = Query(None),
    loader: Optional[str] = Query(None),
    side: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get compatibility check results with filtering and sorting"""
    query = db.query(
        CompatibilityResult,
        ModVersion,
        MCVersion,
        TrackedMod
    ).join(
        ModVersion, CompatibilityResult.mod_version_id == ModVersion.id
    ).join(
        MCVersion, CompatibilityResult.mc_version_id == MCVersion.id
    ).join(
        TrackedMod, ModVersion.mod_slug == TrackedMod.slug
    )
    
    if mc_version:
        query = query.filter(MCVersion.version == mc_version)
    
    if loader:
        query = query.filter(MCVersion.loader == loader)
    
    if side:
        if side == "both":
            query = query.filter(TrackedMod.side == "both")
        elif side == "server":
            query = query.filter(TrackedMod.side.in_(["server", "both"]))
        elif side == "client":
            query = query.filter(TrackedMod.side.in_(["client", "both"]))

    # Sort by mod slug ASC, then by MC version release time DESC, then by checked_at DESC
    results = query.order_by(
        ModVersion.mod_slug.asc(),
        MCVersion.release_time.desc(),
        CompatibilityResult.checked_at.desc()
    ).all()
    
    # Build response with joined data
    response = []
    for compat_result, mod_version, mc_version, tracked_mod in results:
        result_dict = ResultResponse(
            id=compat_result.id,
            mod_version_id=compat_result.mod_version_id,
            mc_version_id=compat_result.mc_version_id,
            status=compat_result.status,
            error=compat_result.error,
            checked_at=compat_result.checked_at.replace(tzinfo=timezone.utc) if compat_result.checked_at else None,
            # Add joined data
            mod_slug=mod_version.mod_slug,
            mod_version_number=mod_version.version_number,
            mc_version=mc_version.version,
            loader=mc_version.loader
        )
        response.append(result_dict)

    return response

@router.get("/api/results/summary", response_model=SummaryResponse)
def get_summary(mc_version: str, loader: str, db: Session = Depends(get_db)):
    """Get compatibility summary for a specific Minecraft version and loader"""
    # Get the MC version object
    mc_ver_obj = db.query(MCVersion).filter_by(version=mc_version, loader=loader).first()
    if not mc_ver_obj:
        return SummaryResponse(
            compatible=0, total=0, 
            server_compatible=0, server_total=0,
            client_compatible=0, client_total=0
        )
    
    # Get all compatibility results for this MC version (through ModVersion)
    results = db.query(
        CompatibilityResult,
        ModVersion,
        TrackedMod
    ).join(
        ModVersion, CompatibilityResult.mod_version_id == ModVersion.id
    ).join(
        TrackedMod, ModVersion.mod_slug == TrackedMod.slug
    ).filter(
        CompatibilityResult.mc_version_id == mc_ver_obj.id
    ).all()
    
    # Group by mod_slug to get latest result per mod
    mod_results = {}
    for compat_result, mod_version, tracked_mod in results:
        if tracked_mod.slug not in mod_results:
            mod_results[tracked_mod.slug] = (compat_result, tracked_mod)
        else:
            # Keep the most recent check
            existing_compat, _ = mod_results[tracked_mod.slug]
            if compat_result.checked_at > existing_compat.checked_at:
                mod_results[tracked_mod.slug] = (compat_result, tracked_mod)
    
    compatible = sum(1 for compat, mod in mod_results.values() if compat.status == "compatible")
    total = len(mod_results)
    
    server_compatible = sum(1 for compat, mod in mod_results.values() if compat.status == "compatible" and mod.side in ["server", "both"])
    server_total = sum(1 for compat, mod in mod_results.values() if mod.side in ["server", "both"])
    
    client_compatible = sum(1 for compat, mod in mod_results.values() if compat.status == "compatible" and mod.side in ["client", "both"])
    client_total = sum(1 for compat, mod in mod_results.values() if mod.side in ["client", "both"])
    
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
    
    for log in logs:
        if log.created_at:
            log.created_at = log.created_at.replace(tzinfo=timezone.utc)
            
    return logs
