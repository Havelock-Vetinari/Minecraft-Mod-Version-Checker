import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.all import Mod, CompatibilityResult, LogEntry, MCVersion
from app.services.modrinth import get_mod_compatible_versions, find_mod_version_for_mc
from app.services.mojang import get_all_versions, get_latest_stable_version, get_version_details

logger = logging.getLogger(__name__)


def add_log(db: Session, level: str, message: str):
    """Add a log entry to the database"""
    log = LogEntry(level=level, message=message)
    db.add(log)
    db.commit()


async def sync_versions(db: Session):
    """Sync official versions based on rules"""
    try:
        official_versions = await get_all_versions()
        existing_versions_map = {v.version: v for v in db.query(MCVersion).all()}
        
        current_db = db.query(MCVersion).filter(MCVersion.is_current == True).first()
        to_add = []

        # If DB is empty (no versions at all), import latest stable
        if not existing_versions_map:
            latest = await get_latest_stable_version()
            if latest:
                to_add.append(latest)
                add_log(db, "INFO", f"Database empty. Importing latest version: {latest['id']}")
        
        # If we have a current version, find/import newer releases
        elif current_db:
            # Ensure current DB version has a type/release_time if missing (migration fix)
            current_official = next((v for v in official_versions if v["id"] == current_db.version), None)
            
            if current_official:
                modified = False
                if not current_db.release_time:
                    current_db.release_time = current_official["release_dt"]
                    modified = True
                if not current_db.type:
                    current_db.type = current_official["type"]
                    modified = True
                
                if modified:
                    db.commit()
            
            # Now find newer releases
            if current_db.release_time:
                for v in official_versions:
                    # Filter for releases only, unless we decide to support snapshots later
                    if v["type"] == "release" and v["release_dt"] > current_db.release_time:
                        if v["id"] not in existing_versions_map:
                            to_add.append(v)

        for v_data in to_add:
            logger.info(f"Importing new version: {v_data['id']}")
            new_ver = MCVersion(
                version=v_data["id"],
                type=v_data["type"],
                release_time=v_data["release_dt"],
                url=v_data["url"],
                is_current=False
            )
            db.add(new_ver)
            add_log(db, "INFO", f"Imported new version: {v_data['id']}")
        
        if to_add:
            db.commit()

    except Exception as e:
        logger.error(f"Version sync failed: {e}")
        add_log(db, "ERROR", f"Version sync failed: {str(e)}")



async def get_target_versions(db: Session) -> List[str]:
    """Identify versions to check against (Current + Newer)"""
    current_version_obj = db.query(MCVersion).filter(MCVersion.is_current == True).first()
    
    target_versions = []
    if current_version_obj:
        # Add Current
        target_versions.append(current_version_obj.version)
        
        # Add Newer
        all_db_versions = db.query(MCVersion).all()
        for v in all_db_versions:
            if v.release_time and current_version_obj.release_time and v.release_time > current_version_obj.release_time:
                target_versions.append(v.version)
    else:
        # Fallback: check against latest stable ONLY if no current version set
        latest_stable = await get_latest_stable_version()
        if latest_stable and latest_stable.get("id"):
            target_versions.append(latest_stable["id"])
            
    # Remove duplicates and sort
    return sorted(list(set(target_versions)))


async def check_mod_against_targets(db: Session, mod: Mod, target_versions: List[str]):
    """Check a single mod against a list of target versions"""
    # Optimization: Fetch mod compatible versions ONCE
    mod_compatible_versions, error = await get_mod_compatible_versions(mod.slug, mod.loader)
    
    if error:
        add_log(db, "ERROR", f"Failed to check {mod.slug}: {error}")
        # Save checks as error for ALL targets
        for tv in target_versions:
            result = CompatibilityResult(
                mod_slug=mod.slug,
                mc_version=tv,
                loader=mod.loader,
                status="error",
                compatible_versions=[],
                error=error,
                checked_at=datetime.utcnow()
            )
            db.add(result)
        return
    
    # Check against each target
    for tv in target_versions:
        status = "compatible" if tv in mod_compatible_versions else "incompatible"
        
        # If compatible, find the specific mod version ID
        mod_version_id = None
        if status == "compatible":
            mod_version_id = await find_mod_version_for_mc(mod.slug, mod.loader, tv)
        
        result = CompatibilityResult(
            mod_slug=mod.slug,
            mc_version=tv,
            loader=mod.loader,
            status=status,
            compatible_versions=mod_compatible_versions,
            mod_version_id=mod_version_id,
            checked_at=datetime.utcnow()
        )
        db.add(result)
        
    add_log(db, "INFO", f"Checked {mod.slug} against {len(target_versions)} versions")


async def check_single_mod_task(mod_id: int):
    """Background task to check a single mod"""
    db = SessionLocal()
    try:
        # Ensure versions are synced first
        await sync_versions(db)
        
        target_versions = await get_target_versions(db)
        if not target_versions:
             add_log(db, "INFO", "No target versions set. Skipping check for new mod.")
             return

        mod = db.query(Mod).filter(Mod.id == mod_id).first()
        if not mod:
            add_log(db, "ERROR", f"Mod with ID {mod_id} not found for background check")
            return

        add_log(db, "INFO", f"Starting background check for {mod.slug}")
        await check_mod_against_targets(db, mod, target_versions)
        db.commit()

    except Exception as e:
        logger.error(f"Single mod check failed: {e}")
        add_log(db, "ERROR", f"Single mod check failed: {str(e)}")
    finally:
        db.close()


async def check_all_mods():
    """Background job to check mod compatibility against current and newer MC versions"""
    db = SessionLocal()

    try:
        # 1. Sync Versions
        await sync_versions(db)
        
        # 2. Identify Target Versions (Current + Newer)
        target_versions = await get_target_versions(db)

        if not target_versions:
            add_log(db, "INFO", "No target versions (Current) set. Skipping checks.")
            return

        add_log(db, "INFO", f"Starting checks against: {', '.join(target_versions)}")

        mods = db.query(Mod).all()
        if not mods:
            add_log(db, "INFO", "No mods to check")
            return

        # 3. Check Mods
        for mod in mods:
            await check_mod_against_targets(db, mod, target_versions)

        db.commit()
        add_log(db, "INFO", "Compatibility check completed")

    except Exception as e:
        logger.error(f"Background job error: {e}")
        add_log(db, "ERROR", f"Background job failed: {str(e)}")
    finally:
        db.close()


async def background_loop():
    """Run background checks every 5 minutes"""
    while True:
        try:
            await check_all_mods()
        except Exception as e:
            logger.error(f"Background loop error: {e}")


        # Wait 5 minutes (300 seconds)
        await asyncio.sleep(300)


async def enrich_and_check_version_task(version_id: str):
    """
    Background task to:
    1. Fetch official details (release time) for the manually added version.
    2. Check all mods against this new version.
    """
    db = SessionLocal()
    try:
        # 1. Enrich Version Details
        logger.info(f"Enriching version {version_id}...")
        details = await get_version_details(version_id)
        
        target_version_obj = db.query(MCVersion).filter(MCVersion.version == version_id).first()
        if not target_version_obj:
            logger.error(f"Version {version_id} not found in DB during background enrichment")
            return

        if details:
            target_version_obj.release_time = details["release_dt"]
            target_version_obj.type = details["type"]
            target_version_obj.url = details.get("url")
            db.commit()
            add_log(db, "INFO", f"Updated version {version_id} with official release time")
        else:
            add_log(db, "WARNING", f"Could not find official details for {version_id}. Using defaults.")

        # 2. Check All Mods
        mods = db.query(Mod).all()
        if not mods:
            return

        add_log(db, "INFO", f"Starting compatibility checks for {len(mods)} mods against {version_id}")
        
        for mod in mods:
            # Check against this SINGLE target version
            await check_mod_against_targets(db, mod, [version_id])
            
        db.commit()
        add_log(db, "INFO", f"Completed checks for new version {version_id}")

    except Exception as e:
        logger.error(f"Enrichment task failed: {e}")
        add_log(db, "ERROR", f"Enrichment task failed for {version_id}: {str(e)}")
    finally:
        db.close()

