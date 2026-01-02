import yaml
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Body, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.all import TrackedMod, LogEntry, MCVersion, ModVersion, CompatibilityResult
from app.schemas.all import TrackedModResponse, TrackedModSchema
from app.services.background import check_single_mod_task
from app.services.modrinth import get_mod_details

class LiteralString(str):
    pass

def literal_string_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

yaml.add_representer(LiteralString, literal_string_representer)

router = APIRouter(
    prefix="/api/mods",
    tags=["mods"]
)

def add_log(db: Session, level: str, message: str):
    log = LogEntry(level=level, message=message)
    db.add(log)
    db.commit()

@router.get("", response_model=List[TrackedModResponse])
def get_mods(db: Session = Depends(get_db)):
    """Get all tracked mods"""
    mods = db.query(TrackedMod).all()
    return mods

@router.post("", response_model=TrackedModResponse)
async def add_mod(data: TrackedModSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Add a new mod to track"""
    # Check if already exists
    existing = db.query(TrackedMod).filter(TrackedMod.slug == data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Mod {data.slug} is already tracked")
    
    # Fetch mod details to get supported sides
    details = await get_mod_details(data.slug)
    supported_client = details.get("client_side") if details else None
    supported_server = details.get("server_side") if details else None

    tracked_mod = TrackedMod(
        slug=data.slug, 
        side=data.side,
        channel=data.channel,
        supported_client_side=supported_client,
        supported_server_side=supported_server
    )
    db.add(tracked_mod)
    db.commit()
    db.refresh(tracked_mod)

    add_log(db, "INFO", f"Mod {data.slug} added for tracking (channel: {data.channel})")
    
    # Trigger background check
    background_tasks.add_task(check_single_mod_task, tracked_mod.slug)
    
    return tracked_mod

@router.delete("/{mod_slug}")
def delete_mod(mod_slug: str, db: Session = Depends(get_db)):
    """Remove a mod from tracking"""
    tracked_mod = db.query(TrackedMod).filter(TrackedMod.slug == mod_slug).first()
    if not tracked_mod:
        raise HTTPException(status_code=404, detail="Mod not found")
    
    # Cascade delete will handle mod_versions and compatibility_results
    db.delete(tracked_mod)
    db.commit()

    add_log(db, "INFO", f"Mod {mod_slug} removed from tracking (including all versions and results)")
    return {"success": True}

@router.get("/export")
def export_mods(mc_version: str = Query(...), loader: str = Query(...), db: Session = Depends(get_db)):
    """Export mods in docker-compose format ensuring full server-side compatibility"""
    # Get the specific MC version+loader
    mc_ver_obj = db.query(MCVersion).filter_by(version=mc_version, loader=loader).first()
    if not mc_ver_obj:
        raise HTTPException(status_code=404, detail=f"MC version {mc_version} ({loader}) not found")
    
    # Get all tracked mods that are server-side or both
    all_mods = db.query(TrackedMod).all()
    mods_to_export = [m for m in all_mods if m.side in ["server", "both"]]
    
    if not mods_to_export:
        raise HTTPException(status_code=400, detail="No server-side or 'both' mods found to export")

    projects = []
    
    for tracked_mod in mods_to_export:
        # Find compatible mod version for this MC version
        mod_version = db.query(ModVersion).filter_by(
            mod_slug=tracked_mod.slug,
            mc_version_id=mc_ver_obj.id,
            loader=loader
        ).join(CompatibilityResult).filter(
            CompatibilityResult.status == "compatible"
        ).first()
        
        if not mod_version:
            raise HTTPException(
                status_code=400, 
                detail=f"Server-side mod {tracked_mod.slug} is not compatible with {mc_version} ({loader}). Export only allowed when all server/both mods are compatible."
            )
        
        projects.append(f"{tracked_mod.slug}:{mod_version.version_id}")

    compose_data = {
        "services": {
            "mc": {
                "environment": {
                    "TYPE": loader.upper(),
                    "VERSION": mc_version,
                    "MODRINTH_PROJECTS": LiteralString("\n".join(projects) + "\n")
                }
            }
        }
    }
    
    return {"yaml": yaml.dump(compose_data, sort_keys=False, default_flow_style=False)}

@router.post("/import")
async def import_mods(background_tasks: BackgroundTasks, db: Session = Depends(get_db), data: dict = Body(...)):
    """Import mods from docker-compose YAML"""
    yaml_content = data.get("yaml")
    if not yaml_content:
        raise HTTPException(status_code=400, detail="No YAML content provided")
        
    try:
        config = yaml.safe_load(yaml_content)
        services = config.get("services", {})
        mc_service = next(iter(services.values())) if services else {}
        env = mc_service.get("environment", {})
        
        projects_str = env.get("MODRINTH_PROJECTS", "")
        
        if not projects_str:
            raise HTTPException(status_code=400, detail="No MODRINTH_PROJECTS found in YAML")
            
        lines = [line.strip() for line in projects_str.split("\n") if line.strip()]
        added_count = 0

        for line in lines:
            slug = line.split(":")[0].strip()
            if not slug:
                continue
                
            # Check if mod already tracked
            existing = db.query(TrackedMod).filter(TrackedMod.slug == slug).first()
            if not existing:
                # Fetch mod details for support info and default to 'server' side
                details = await get_mod_details(slug)
                supported_client = details.get("client_side") if details else None
                supported_server = details.get("server_side") if details else None

                tracked_mod = TrackedMod(
                    slug=slug, 
                    side="server",  # Default to server for imported mods
                    channel="release",  # Default to release channel
                    supported_client_side=supported_client,
                    supported_server_side=supported_server
                )
                db.add(tracked_mod)
                db.commit()
                db.refresh(tracked_mod)
                background_tasks.add_task(check_single_mod_task, tracked_mod.slug)
                added_count += 1
                
        add_log(db, "INFO", f"Imported {added_count} mods from YAML")
        return {"success": True, "added": added_count}
        
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.patch("/{mod_slug}/side", response_model=TrackedModResponse)
def update_mod_side(mod_slug: str, side: str = Body(embed=True), db: Session = Depends(get_db)):
    """Update the side for a tracked mod"""
    tracked_mod = db.query(TrackedMod).filter(TrackedMod.slug == mod_slug).first()
    if not tracked_mod:
        raise HTTPException(status_code=404, detail="Mod not found")
    
    if side not in ["client", "server", "both"]:
        raise HTTPException(status_code=400, detail="Invalid side value")
    
    tracked_mod.side = side
    db.commit()
    db.refresh(tracked_mod)
    
    add_log(db, "INFO", f"Mod {tracked_mod.slug} side updated to {side}")
    return tracked_mod


@router.patch("/{mod_slug}/channel", response_model=TrackedModResponse)
def update_mod_channel(mod_slug: str, channel: str = Body(embed=True), db: Session = Depends(get_db)):
    """Update the channel for a tracked mod"""
    tracked_mod = db.query(TrackedMod).filter(TrackedMod.slug == mod_slug).first()
    if not tracked_mod:
        raise HTTPException(status_code=404, detail="Mod not found")
    
    if channel not in ["release", "beta", "alpha"]:
        raise HTTPException(status_code=400, detail="Invalid channel value")
    
    tracked_mod.channel = channel
    db.commit()
    db.refresh(tracked_mod)
    
    add_log(db, "INFO", f"Mod {tracked_mod.slug} channel updated to {channel}")
    return tracked_mod
