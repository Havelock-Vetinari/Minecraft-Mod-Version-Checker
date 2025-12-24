import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.all import Mod, CompatibilityResult, LogEntry
from app.services.modrinth import get_latest_minecraft_version, get_mod_compatible_versions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_log(db: Session, level: str, message: str):
    """Add a log entry to the database"""
    log = LogEntry(level=level, message=message)
    db.add(log)
    db.commit()


async def check_all_mods():
    """Background job to check mod compatibility against latest MC version"""
    db = SessionLocal()

    try:
        latest_version = await get_latest_minecraft_version()
        add_log(db, "INFO", f"Starting compatibility check against MC {latest_version}")

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
                status = "compatible" if latest_version in compatible_versions else "incompatible"
                add_log(db, "INFO", f"{mod.slug}: {status}")

            result = CompatibilityResult(
                mod_slug=mod.slug,
                mc_version=latest_version,
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
