from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class MCVersion(Base):
    """Minecraft versions with loader support"""
    __tablename__ = "mc_versions"
    
    id = Column(Integer, primary_key=True)
    version = Column(String, nullable=False, index=True)  # e.g., "1.21.1"
    loader = Column(String, nullable=False, index=True)   # fabric, forge, quilt
    type = Column(String)  # release, snapshot
    url = Column(String)
    release_time = Column(DateTime)
    is_current = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('version', 'loader', name='uix_version_loader'),
    )


class TrackedMod(Base):
    """Mods to be checked for compatibility"""
    __tablename__ = "tracked_mods"
    
    slug = Column(String, primary_key=True)  # Mod slug is unique identifier
    side = Column(String, nullable=False)  # client, server, both
    channel = Column(String, default="release", nullable=False)  # release, beta, alpha
    supported_client_side = Column(String, nullable=True)  # required, optional, unsupported
    supported_server_side = Column(String, nullable=True)  # required, optional, unsupported
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to mod versions
    mod_versions = relationship("ModVersion", back_populates="tracked_mod", cascade="all, delete-orphan")


class ModVersion(Base):
    """Specific mod versions compatible with MC versions"""
    __tablename__ = "mod_versions"
    
    id = Column(Integer, primary_key=True)
    mod_slug = Column(String, ForeignKey('tracked_mods.slug', ondelete='CASCADE'), nullable=False, index=True)
    version_id = Column(String, nullable=False)      # Modrinth version ID
    version_number = Column(String, nullable=False)  # Human-readable version
    mc_version_id = Column(Integer, ForeignKey('mc_versions.id'), nullable=False, index=True)
    loader = Column(String, nullable=False, index=True)  # fabric, forge, quilt
    channel = Column(String, nullable=False)  # release, beta, alpha
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tracked_mod = relationship("TrackedMod", back_populates="mod_versions")
    mc_version = relationship("MCVersion")
    compatibility_results = relationship("CompatibilityResult", back_populates="mod_version", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('mod_slug', 'version_id', 'mc_version_id', name='uix_mod_version_mc'),
    )


class CompatibilityResult(Base):
    """Compatibility check results"""
    __tablename__ = "compatibility_results"
    
    id = Column(Integer, primary_key=True)
    mod_version_id = Column(Integer, ForeignKey('mod_versions.id', ondelete='CASCADE'), nullable=False, index=True)
    mc_version_id = Column(Integer, ForeignKey('mc_versions.id'), nullable=False, index=True)
    status = Column(String, nullable=False, index=True)  # compatible, incompatible, error
    error = Column(String, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    mod_version = relationship("ModVersion", back_populates="compatibility_results")
    mc_version = relationship("MCVersion")
    
    __table_args__ = (
        UniqueConstraint('mod_version_id', 'mc_version_id', name='uix_modver_mcver'),
    )


class LogEntry(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    level = Column(String)  # INFO, WARNING, ERROR
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
