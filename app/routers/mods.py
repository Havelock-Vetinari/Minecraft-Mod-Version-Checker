import yaml
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Body, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.all import Mod, LogEntry, MCVersion, CompatibilityResult
from app.schemas.all import ModResponse, ModSchema
from app.services.background import check_single_mod_task

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
def add_mod(data: ModSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Add a new mod to track"""
    mod = Mod(slug=data.slug, mc_version=data.mc_version, loader=data.loader, side=data.side)
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
    # Verify full compatibility
    mods = db.query(Mod).all()
    if not mods:
        raise HTTPException(status_code=400, detail="No mods tracked")

    for mod in mods:
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

    projects = []
    loader_type = mods[0].loader.upper() if mods else "FABRIC"

    for mod in mods:
        # We already checked compatibility above, so we know 'res' exists
        res = db.query(CompatibilityResult).filter(
            CompatibilityResult.mod_slug == mod.slug,
            CompatibilityResult.mc_version == mc_version,
            CompatibilityResult.loader == mod.loader,
            CompatibilityResult.status == "compatible"
        ).order_by(CompatibilityResult.checked_at.desc()).first()
        
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
def import_mods(background_tasks: BackgroundTasks, db: Session = Depends(get_db), data: dict = Body(...)):
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
            
        # Parse projects
        # Format can be: 
        # slug
        # slug:version_id
        # slug:version_id (on new line)
        
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
                mod = Mod(slug=slug, mc_version=mc_version, loader=loader, side="both")
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
