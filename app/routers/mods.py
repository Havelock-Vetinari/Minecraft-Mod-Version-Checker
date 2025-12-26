import yaml
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Body, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.all import Mod, LogEntry, MCVersion, CompatibilityResult
from app.schemas.all import ModResponse, ModSchema
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

@router.get("", response_model=List[ModResponse])
def get_mods(db: Session = Depends(get_db)):
    """Get all tracked mods"""
    mods = db.query(Mod).all()
    return mods

@router.post("", response_model=ModResponse)
async def add_mod(data: ModSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Add a new mod to track"""
    # Fetch mod details to get supported sides
    details = await get_mod_details(data.slug)
    supported_client = details.get("client_side") if details else None
    supported_server = details.get("server_side") if details else None

    mod = Mod(
        slug=data.slug, 
        mc_version=data.mc_version, 
        loader=data.loader, 
        side=data.side,
        supported_client_side=supported_client,
        supported_server_side=supported_server
    )
    db.add(mod)
    db.commit()
    db.refresh(mod)

    add_log(db, "INFO", f"Mod {data.slug} ({data.loader}) added for tracking")
    
    # Trigger background check
    background_tasks.add_task(check_single_mod_task, mod.id)
    
    return mod

@router.delete("/{mod_id}")
def delete_mod(mod_id: int, db: Session = Depends(get_db)):
    """Remove a mod from tracking"""
    mod = db.query(Mod).filter(Mod.id == mod_id).first()
    if not mod:
        raise HTTPException(status_code=404, detail="Mod not found")

    slug = mod.slug
    loader = mod.loader
    
    # Delete associated compatibility results
    db.query(CompatibilityResult).filter(
        CompatibilityResult.mod_slug == slug,
        CompatibilityResult.loader == loader
    ).delete()
    
    db.delete(mod)
    db.commit()

    add_log(db, "INFO", f"Mod {slug} removed from tracking (including compatibility results)")
    return {"success": True}

@router.get("/export")
def export_mods(mc_version: str = Query(...), db: Session = Depends(get_db)):
    """Export mods in docker-compose format and ensure full compatibility"""
    # Get all tracked mods and filter by side
    # We only include server or both sides for docker-compose export
    all_mods = db.query(Mod).all()
    if not all_mods:
        raise HTTPException(status_code=400, detail="No mods tracked")

    # Filter: Only include mods that are NOT purely client-side
    mods_to_export = [m for m in all_mods if m.side in ["server", "both"]]
    
    if not mods_to_export:
        raise HTTPException(status_code=400, detail="No server-side or 'both' mods found to export")

    projects = []
    loader_type = mods_to_export[0].loader.upper()

    for mod in mods_to_export:
        # Verify full compatibility for mods being exported
        res = db.query(CompatibilityResult).filter(
            CompatibilityResult.mod_slug == mod.slug,
            CompatibilityResult.mc_version == mc_version,
            CompatibilityResult.loader == mod.loader,
            CompatibilityResult.status == "compatible"
        ).order_by(CompatibilityResult.checked_at.desc()).first()
        
        if not res:
            raise HTTPException(
                status_code=400, 
                detail=f"Mod {mod.slug} is not compatible with {mc_version} yet. Export only allowed for fully compatible versions."
            )
        
        version_id = f":{res.mod_version_id}" if res.mod_version_id else ""
        projects.append(f"{mod.slug}{version_id}")

    compose_data = {
        "services": {
            "mc": {
                "environment": {
                    "TYPE": loader_type,
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
        
        loader = env.get("TYPE", "FABRIC").lower()
        projects_str = env.get("MODRINTH_PROJECTS", "")
        
        if not projects_str:
            raise HTTPException(status_code=400, detail="No MODRINTH_PROJECTS found in YAML")
            
        lines = [line.strip() for line in projects_str.split("\n") if line.strip()]
        added_count = 0
        
        # Get current MC version if possible to set for new mods
        current_version = db.query(MCVersion).filter(MCVersion.is_current == True).first()
        mc_version = current_version.version if current_version else None

        for line in lines:
            slug = line.split(":")[0].strip()
            if not slug:
                continue
                
            # Check if mod already exists for this loader
            existing = db.query(Mod).filter(Mod.slug == slug, Mod.loader == loader).first()
            if not existing:
                # Fetch mod details for support info and default to 'server'
                details = await get_mod_details(slug)
                supported_client = details.get("client_side") if details else None
                supported_server = details.get("server_side") if details else None

                mod = Mod(
                    slug=slug, 
                    mc_version=mc_version, 
                    loader=loader, 
                    side="server",
                    supported_client_side=supported_client,
                    supported_server_side=supported_server
                )
                db.add(mod)
                db.commit()
                db.refresh(mod)
                background_tasks.add_task(check_single_mod_task, mod.id)
                added_count += 1
                
        add_log(db, "INFO", f"Imported {added_count} mods from YAML")
        return {"success": True, "added": added_count}
        
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.patch("/{mod_id}/side", response_model=ModResponse)
def update_mod_side(mod_id: int, side: str = Body(embed=True), db: Session = Depends(get_db)):
    """Update the side for a mod"""
    mod = db.query(Mod).filter(Mod.id == mod_id).first()
    if not mod:
        raise HTTPException(status_code=404, detail="Mod not found")
    
    if side not in ["client", "server", "both"]:
        raise HTTPException(status_code=400, detail="Invalid side value")
    
    mod.side = side
    db.commit()
    db.refresh(mod)
    
    add_log(db, "INFO", f"Mod {mod.slug} side updated to {side}")
    return mod
