from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.all import Mod, LogEntry
from app.schemas.all import ModResponse, ModSchema

router = APIRouter(
    prefix="/api/mods",
    tags=["mods"]
)

def add_log(db: Session, level: str, message: str):
    log = LogEntry(level=level, message=message)
    db.add(log)
    db.commit()

@router.get("", response_model=List[ModResponse])
def get_mods(db: Session = Depends(get_db)):
    """Get all tracked mods"""
    mods = db.query(Mod).all()
    return mods

@router.post("", response_model=ModResponse)
def add_mod(data: ModSchema, db: Session = Depends(get_db)):
    """Add a new mod to track"""
    mod = Mod(slug=data.slug, mc_version=data.mc_version, loader=data.loader, side=data.side)
    db.add(mod)
    db.commit()
    db.refresh(mod)

    add_log(db, "INFO", f"Mod {data.slug} ({data.loader}) added for tracking")
    return mod

@router.delete("/{mod_id}")
def delete_mod(mod_id: int, db: Session = Depends(get_db)):
    """Remove a mod from tracking"""
    mod = db.query(Mod).filter(Mod.id == mod_id).first()
    if not mod:
        raise HTTPException(status_code=404, detail="Mod not found")

    slug = mod.slug
    db.delete(mod)
    db.commit()

    add_log(db, "INFO", f"Mod {slug} removed from tracking")
    return {"success": True}
