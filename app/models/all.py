from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from datetime import datetime
from app.core.database import Base

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
    mc_version = Column(String, nullable=True)  # Version mod was added for
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
