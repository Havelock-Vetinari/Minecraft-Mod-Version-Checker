from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import httpx
import asyncio
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mod_checker.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Models
class MCVersion(Base):
    __tablename__ = "mc_versions"
    id = Column(Integer, primary_key=True)
    version = Column(String, unique=True)
    is_current = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Mod(Base):
    __tablename__ = "mods"
    id = Column(Integer, primary_key=True)
    slug = Column(String)
    mc_version = Column(String)  # Version mod was added for
    loader = Column(String)
    side = Column(String)  # client, server, both
    created_at = Column(DateTime, default=datetime.utcnow)


class CompatibilityResult(Base):
    __tablename__ = "compatibility_results"
    id = Column(Integer, primary_key=True)
    mod_slug = Column(String)
    mc_version = Column(String)  # Latest MC version checked against
    loader = Column(String)
    status = Column(String)  # compatible, incompatible, error
    compatible_versions = Column(JSON, default=list)  # Versions this mod supports
    error = Column(String, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow)


class LogEntry(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    level = Column(String)  # INFO, WARNING, ERROR
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


# Pydantic schemas
class VersionSchema(BaseModel):
    version: str
    is_current: bool = False


class ModSchema(BaseModel):
    slug: str
    mc_version: str
    loader: str
    side: str


class VersionResponse(BaseModel):
    id: int
    version: str
    is_current: bool


class ModResponse(BaseModel):
    id: int
    slug: str
    mc_version: str
    loader: str
    side: str


class ResultResponse(BaseModel):
    id: int
    mod_slug: str
    mc_version: str
    loader: str
    status: str
    compatible_versions: List[str]
    error: Optional[str]
    checked_at: datetime


class LogResponse(BaseModel):
    id: int
    level: str
    message: str
    created_at: datetime


# FastAPI app
app = FastAPI(title="Minecraft Mod Compatibility Checker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Modrinth API client
MODRINTH_BASE = "https://api.modrinth.com/v2"
USER_AGENT = "minecraft-mod-checker/1.0 (github.com)"


async def get_latest_minecraft_version() -> str:
    """Fetch the latest released Minecraft version from Modrinth"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Correct endpoint: /tag/game_version (singular)
            response = await client.get(
                f"{MODRINTH_BASE}/tag/game_version",
                headers={"User-Agent": USER_AGENT}
            )
            response.raise_for_status()
            versions = response.json()

            # Filter for release versions (not snapshots/pre-releases)
            releases = [v for v in versions if v.get("version_type") == "release"]
            if releases:
                # Return latest (first in list)
                return releases[0]["version"]
            return versions[0]["version"] if versions else "1.21.1"
    except Exception as e:
        logger.error(f"Failed to fetch latest MC version: {e}")
        return "1.21.1"  # Fallback


async def get_mod_compatible_versions(slug: str, loader: str) -> tuple[List[str], Optional[str]]:
    """
    Get all Minecraft versions this mod is compatible with.
    Returns (compatible_versions, error_message)
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            headers = {"User-Agent": USER_AGENT}

            # Get project info first to validate slug
            project_url = f"{MODRINTH_BASE}/project/{slug}"
            try:
                project_response = await client.get(project_url, headers=headers, timeout=5)
                project_response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return [], f"Mod '{slug}' not found on Modrinth"
                raise

            # Get all versions for this mod - endpoint returns array
            # Use /version (singular) endpoint which returns all versions for a project
            versions_url = f"{MODRINTH_BASE}/project/{slug}/version"
            params = {
                "loaders": loader,  # Pass as string, not JSON array
            }

            versions_response = await client.get(versions_url, params=params, headers=headers, timeout=10)
            versions_response.raise_for_status()

            versions = versions_response.json()
            if not isinstance(versions, list):
                versions = [versions]

            compatible_mc_versions = []

            # Collect all MC versions this mod supports
            for version in versions:
                game_versions = version.get("game_versions", [])
                compatible_mc_versions.extend(game_versions)

            # Return unique, sorted versions (latest first)
            unique_versions = sorted(set(compatible_mc_versions), reverse=True)
            return unique_versions, None

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        logger.error(f"Modrinth API error for {slug}: {error_msg}")
        return [], error_msg
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to check mod {slug}: {error_msg}")
        return [], error_msg


def add_log(db: Session, level: str, message: str):
    """Add a log entry to the database"""
    log = LogEntry(level=level, message=message)
    db.add(log)
    db.commit()


# Routes
@app.get("/api/versions", response_model=List[VersionResponse])
def get_versions(db: Session = Depends(get_db)):
    """Get all tracked Minecraft versions"""
    versions = db.query(MCVersion).order_by(MCVersion.version).all()
    return versions


@app.get("/api/versions/current")
def get_current_version(db: Session = Depends(get_db)):
    """Get the current/primary Minecraft version"""
    current = db.query(MCVersion).filter(MCVersion.is_current == True).first()
    return {"version": current.version if current else None}


@app.post("/api/versions", response_model=VersionResponse)
def add_version(data: VersionSchema, db: Session = Depends(get_db)):
    """Add a new Minecraft version"""
    # If setting as current, unset other current versions
    if data.is_current:
        db.query(MCVersion).update({MCVersion.is_current: False})

    version = MCVersion(version=data.version, is_current=data.is_current)
    db.add(version)
    db.commit()
    db.refresh(version)

    add_log(db, "INFO", f"Version {data.version} added" + (" (set as current)" if data.is_current else ""))
    return version


@app.put("/api/versions/{version_id}/set-current")
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


@app.delete("/api/versions/{version_id}")
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


@app.get("/api/mods", response_model=List[ModResponse])
def get_mods(db: Session = Depends(get_db)):
    """Get all tracked mods"""
    mods = db.query(Mod).all()
    return mods


@app.post("/api/mods", response_model=ModResponse)
def add_mod(data: ModSchema, db: Session = Depends(get_db)):
    """Add a new mod to track"""
    mod = Mod(slug=data.slug, mc_version=data.mc_version, loader=data.loader, side=data.side)
    db.add(mod)
    db.commit()
    db.refresh(mod)

    add_log(db, "INFO", f"Mod {data.slug} ({data.loader}) added for tracking")
    return mod


@app.delete("/api/mods/{mod_id}")
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


@app.get("/api/results", response_model=List[ResultResponse])
def get_results(db: Session = Depends(get_db)):
    """Get all compatibility check results"""
    results = db.query(CompatibilityResult).order_by(CompatibilityResult.checked_at.desc()).all()
    return results


@app.get("/api/logs", response_model=List[LogResponse])
def get_logs(db: Session = Depends(get_db)):
    """Get background job logs"""
    logs = db.query(LogEntry).order_by(LogEntry.created_at.desc()).limit(100).all()
    return logs


# Background job
async def check_all_mods():
    """Background job to check mod compatibility against latest MC version"""
    db = SessionLocal()

    try:
        # Get latest MC version
        latest_version = await get_latest_minecraft_version()
        add_log(db, "INFO", f"Starting compatibility check against MC {latest_version}")

        # Get all tracked mods
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
                # Check if latest version is in compatible versions
                status = "compatible" if latest_version in compatible_versions else "incompatible"
                add_log(db, "INFO", f"{mod.slug}: {status}")

            # Store result
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


@app.on_event("startup")
async def startup_event():
    """Start background job on app startup"""
    asyncio.create_task(background_loop())


# Serve static files
from fastapi.responses import FileResponse


@app.get("/")
def root():
    """Serve index.html"""
    return FileResponse("/app/static/index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)