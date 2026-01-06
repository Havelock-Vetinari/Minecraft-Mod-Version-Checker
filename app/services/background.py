import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.all import TrackedMod, MCVersion, ModVersion, CompatibilityResult, LogEntry
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
        
        # Get existing versions and loaders
        existing_versions = db.query(MCVersion).all()
        existing_map = {(v.version, v.loader): v for v in existing_versions}
        
        # Get all unique loaders from existing data
        existing_loaders = list(set(v.loader for v in existing_versions))
        if not existing_loaders:
            existing_loaders = ["fabric"]  # Default to fabric if none exist
        
        # Get current version(s)
        current_versions = db.query(MCVersion).filter(MCVersion.is_current == True).all()
        
        to_add = []

        # If DB is empty (no versions at all), import latest stable for each loader
        if not existing_versions:
            latest = await get_latest_stable_version()
            if latest:
                for loader in existing_loaders:
                    to_add.append({**latest, "loader": loader})
                    add_log(db, "INFO", f"Database empty. Importing latest version: {latest['id']} ({loader})")
        
        # If we have current version(s), find/import newer releases
        elif current_versions:
            # Use the first current version as reference for time comparison
            current_ref = current_versions[0]
            
            # Ensure current version has type/release_time if missing
            current_official = next((v for v in official_versions if v["id"] == current_ref.version), None)
            
            if current_official:
                modified = False
                if not current_ref.release_time:
                    current_ref.release_time = current_official["release_dt"]
                    modified = True
                if not current_ref.type:
                    current_ref.type = current_official["type"]
                    modified = True
                
                if modified:
                    db.commit()
            
            # Find newer releases
            if current_ref.release_time:
                for v in official_versions:
                    if v["type"] == "release" and v["release_dt"] > current_ref.release_time:
                        # Add for each existing loader
                        for loader in existing_loaders:
                            if (v["id"], loader) not in existing_map:
                                to_add.append({**v, "loader": loader})

        # Insert new versions
        for v_data in to_add:
            logger.info(f"Importing new version: {v_data['id']} ({v_data['loader']})")
            new_ver = MCVersion(
                version=v_data["id"],
                loader=v_data["loader"],
                type=v_data["type"],
                release_time=v_data["release_dt"],
                url=v_data["url"],
                is_current=False
            )
            db.add(new_ver)
            add_log(db, "INFO", f"Imported new version: {v_data['id']} ({v_data['loader']})")
        
        if to_add:
            db.commit()

    except Exception as e:
        logger.error(f"Version sync failed: {e}")
        add_log(db, "ERROR", f"Version sync failed: {str(e)}")


async def get_target_mc_versions(db: Session) -> List[MCVersion]:
    """
    Get list of MCVersion objects to check against (Current + Newer).
    Returns list of MCVersion instances with all loaders.
    """
    current_versions = db.query(MCVersion).filter(MCVersion.is_current == True).all()
    
    target_versions = []
    
    if current_versions:
        # Add all current versions (different loaders)
        target_versions.extend(current_versions)
        
        # Get reference time from first current version
        current_ref = current_versions[0]
        
        # Add newer versions (all loaders)
        if current_ref.release_time:
            newer = db.query(MCVersion).filter(
                MCVersion.release_time > current_ref.release_time
            ).all()
            target_versions.extend(newer)
    else:
        # Fallback: get latest stable for all loaders
        latest_stable = await get_latest_stable_version()
        if latest_stable:
            # Find all MC versions matching latest stable version
            target_versions = db.query(MCVersion).filter(
                MCVersion.version == latest_stable["id"]
            ).all()
    
    # Remove duplicates by ID
    seen_ids = set()
    unique_targets = []
    for tv in target_versions:
        if tv.id not in seen_ids:
            seen_ids.add(tv.id)
            unique_targets.append(tv)
    
    return unique_targets


async def check_mod_against_targets(db: Session, tracked_mod: TrackedMod, target_mc_versions: List[MCVersion]):
    """
    Check a single tracked mod against target MC versions with upsert logic.
    Creates ModVersion and CompatibilityResult records.
    """
    # Group targets by loader
    targets_by_loader = {}
    for mc_ver in target_mc_versions:
        if mc_ver.loader not in targets_by_loader:
            targets_by_loader[mc_ver.loader] = []
        targets_by_loader[mc_ver.loader].append(mc_ver)
    
    # Check each loader
    for loader, mc_versions in targets_by_loader.items():
        # Fetch compatible versions from Modrinth ONCE per loader
        compatible_versions, error = await get_mod_compatible_versions(tracked_mod.slug, loader)
        
        if error:
            # Create error results for all targets in this loader
            for mc_ver in mc_versions:
                # We can't create ModVersion without version info, so just log error
                add_log(db, "ERROR", f"Failed to check {tracked_mod.slug} ({loader}): {error}")
            continue
        
        # Check against each MC version for this loader
        for mc_ver in mc_versions:
            is_compatible = mc_ver.version in compatible_versions
            
            if is_compatible:
                # Find specific mod version
                ver_data = await find_mod_version_for_mc(
                    tracked_mod.slug, 
                    loader, 
                    mc_ver.version,
                    tracked_mod.channel
                )
                
                if ver_data:
                    # Upsert ModVersion
                    mod_version = db.query(ModVersion).filter_by(
                        mod_slug=tracked_mod.slug,
                        version_id=ver_data["id"],
                        mc_version_id=mc_ver.id
                    ).first()
                    
                    if mod_version:
                        # Update existing
                        mod_version.version_number = ver_data["version_number"]
                        mod_version.channel = ver_data.get("channel", "release")
                        mod_version.loader = loader
                    else:
                        # Create new
                        mod_version = ModVersion(
                            mod_slug=tracked_mod.slug,
                            version_id=ver_data["id"],
                            version_number=ver_data["version_number"],
                            mc_version_id=mc_ver.id,
                            loader=loader,
                            channel=ver_data.get("channel", "release")
                        )
                        db.add(mod_version)
                    
                    db.flush()  # Ensure mod_version.id is available
                    
                    # Upsert CompatibilityResult
                    compat_result = db.query(CompatibilityResult).filter_by(
                        mod_version_id=mod_version.id,
                        mc_version_id=mc_ver.id
                    ).first()
                    
                    if compat_result:
                        # Update existing
                        compat_result.status = "compatible"
                        compat_result.error = None
                        compat_result.checked_at = datetime.utcnow()
                    else:
                        # Create new
                        compat_result = CompatibilityResult(
                            mod_version_id=mod_version.id,
                            mc_version_id=mc_ver.id,
                            status="compatible",
                            checked_at=datetime.utcnow()
                        )
                        db.add(compat_result)
            else:
                # Incompatible - we don't create ModVersion, but could log it
                # For now, just skip (no record means incompatible)
                pass
    
    db.commit()
    add_log(db, "INFO", f"Checked {tracked_mod.slug} against {len(target_mc_versions)} MC versions")


async def check_single_mod_task(mod_slug: str):
    """Background task to check a single mod after it's added"""
    db = SessionLocal()
    try:
        await sync_versions(db)
        
        target_mc_versions = await get_target_mc_versions(db)
        if not target_mc_versions:
            add_log(db, "INFO", "No target versions set. Skipping check for new mod.")
            return

        tracked_mod = db.query(TrackedMod).filter(TrackedMod.slug == mod_slug).first()
        if not tracked_mod:
            add_log(db, "ERROR", f"Tracked mod '{mod_slug}' not found for background check")
            return

        add_log(db, "INFO", f"Starting background check for {tracked_mod.slug}")
        await check_mod_against_targets(db, tracked_mod, target_mc_versions)

    except Exception as e:
        logger.error(f"Single mod check failed: {e}")
        add_log(db, "ERROR", f"Single mod check failed: {str(e)}")
    finally:
        db.close()


async def check_all_mods():
    """Background job to check all tracked mods"""
    db = SessionLocal()

    try:
        # 1. Sync Versions
        await sync_versions(db)
        
        # 2. Get Target Versions
        target_mc_versions = await get_target_mc_versions(db)

        if not target_mc_versions:
            add_log(db, "INFO", "No target versions (Current) set. Skipping checks.")
            return

        add_log(db, "INFO", f"Starting checks against {len(target_mc_versions)} MC version+loader combinations")

        tracked_mods = db.query(TrackedMod).all()
        if not tracked_mods:
            add_log(db, "INFO", "No tracked mods to check")
            return

        # 3. Check Mods
        for tracked_mod in tracked_mods:
            await check_mod_against_targets(db, tracked_mod, target_mc_versions)

        add_log(db, "INFO", "Compatibility check completed")

    except Exception as e:
        logger.error(f"Background job error: {e}")
        add_log(db, "ERROR", f"Background job failed: {str(e)}")
    finally:
        db.close()


async def background_loop():
    """Run background checks every 1 hour"""
    while True:
        try:
            await check_all_mods()
        except Exception as e:
            logger.error(f"Background loop error: {e}")

        # Wait 1 hour (3600 seconds)
        await asyncio.sleep(3600)


async def enrich_and_check_version_task(version_id: str, loader: str):
    """
    Background task to:
    1. Fetch official details for the manually added version.
    2. Check all mods against this new version.
    """
    db = SessionLocal()
    try:
        logger.info(f"Enriching version {version_id} ({loader})...")
        details = await get_version_details(version_id)
        
        target_version_obj = db.query(MCVersion).filter_by(
            version=version_id,
            loader=loader
        ).first()
        
        if not target_version_obj:
            logger.error(f"Version {version_id} ({loader}) not found in DB during background enrichment")
            return

        if details:
            target_version_obj.release_time = details["release_dt"]
            target_version_obj.type = details["type"]
            target_version_obj.url = details.get("url")
            db.commit()
            add_log(db, "INFO", f"Updated version {version_id} ({loader}) with official release time")
        else:
            add_log(db, "WARNING", f"Could not find official details for {version_id}. Using defaults.")

        # Check all tracked mods against this version
        tracked_mods = db.query(TrackedMod).all()
        if not tracked_mods:
            return

        add_log(db, "INFO", f"Starting compatibility checks for {len(tracked_mods)} mods against {version_id} ({loader})")
        
        for tracked_mod in tracked_mods:
            await check_mod_against_targets(db, tracked_mod, [target_version_obj])
            
        add_log(db, "INFO", f"Completed checks for new version {version_id} ({loader})")

    except Exception as e:
        logger.error(f"Enrichment task failed: {e}")
        add_log(db, "ERROR", f"Enrichment task failed for {version_id}: {str(e)}")
    finally:
        db.close()
