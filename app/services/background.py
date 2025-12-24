import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.all import Mod, CompatibilityResult, LogEntry, MCVersion
from app.services.modrinth import get_mod_compatible_versions

import logging
logger = logging.getLogger(__name__)


def add_log(db: Session, level: str, message: str):
    """Add a log entry to the database"""
    log = LogEntry(level=level, message=message)
    db.add(log)
    db.commit()


async def check_all_mods():
    """Background job to check mod compatibility against current MC version"""
    db = SessionLocal()

    try:
        # Get current version from DB
        current_version_obj = db.query(MCVersion).filter(MCVersion.is_current == True).first()
        
        if not current_version_obj:
            add_log(db, "INFO", "No current Minecraft version set. Skipping compatibility checks.")
            return

        target_version = current_version_obj.version
        add_log(db, "INFO", f"Starting compatibility check against MC {target_version}")

        mods = db.query(Mod).all()

        if not mods:
            add_log(db, "INFO", "No mods to check")
            return

        for mod in mods:
            logger.info(f"Checking {mod.slug} ({mod.loader})")
            compatible_versions, error = await get_mod_compatible_versions(mod.slug, mod.loader)

            if error:
                status = "error"
                add_log(db, "ERROR", f"Failed to check {mod.slug}: {error}")
            else:
                status = "compatible" if target_version in compatible_versions else "incompatible"
                add_log(db, "INFO", f"{mod.slug}: {status}")

            result = CompatibilityResult(
                mod_slug=mod.slug,
                mc_version=target_version,
                loader=mod.loader,
                status=status,
                compatible_versions=compatible_versions,
                error=error,
                checked_at=datetime.utcnow()
            )
            db.add(result)

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
