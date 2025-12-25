from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.all import MCVersion, LogEntry
from app.schemas.all import VersionResponse, VersionSchema
from app.services.background import enrich_and_check_version_task

router = APIRouter(
    prefix="/api/versions",
    tags=["versions"]
)

def add_log(db: Session, level: str, message: str):
    log = LogEntry(level=level, message=message)
    db.add(log)
    db.commit()

@router.get("", response_model=List[VersionResponse])
def get_versions(db: Session = Depends(get_db)):
    """Get all tracked Minecraft versions"""
    versions = db.query(MCVersion).order_by(MCVersion.version).all()
    return versions

@router.get("/current")
def get_current_version(db: Session = Depends(get_db)):
    """Get the current/primary Minecraft version"""
    current = db.query(MCVersion).filter(MCVersion.is_current == True).first()
    return {"version": current.version if current else None}

@router.post("", response_model=VersionResponse)
def add_version(data: VersionSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Add a new Minecraft version"""
    # If setting as current, unset other current versions
    if data.is_current:
        db.query(MCVersion).update({MCVersion.is_current: False})

    version = MCVersion(
        version=data.version,
        type=data.type,
        release_time=data.release_time,
        is_current=data.is_current
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    add_log(db, "INFO", f"Version {data.version} added" + (" (set as current)" if data.is_current else ""))
    
    # Schedule background enrichment and check
    background_tasks.add_task(enrich_and_check_version_task, data.version)
    
    return version

@router.put("/{version_id}/set-current")
def set_current_version(version_id: int, db: Session = Depends(get_db)):
    """Set a version as the current one"""
    version = db.query(MCVersion).filter(MCVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    db.query(MCVersion).update({MCVersion.is_current: False})
    version.is_current = True
    db.commit()

    add_log(db, "INFO", f"Current version set to {version.version}")
    return {"version": version.version}

@router.delete("/{version_id}")
def delete_version(version_id: int, db: Session = Depends(get_db)):
    """Delete a Minecraft version"""
    version = db.query(MCVersion).filter(MCVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    if version.is_current:
        raise HTTPException(status_code=400, detail="Cannot delete current version")

    db.delete(version)
    db.commit()
    add_log(db, "INFO", f"Version {version.version} deleted")
    return {"success": True}
