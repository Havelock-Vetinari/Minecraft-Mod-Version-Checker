from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Minecraft Version Schemas
class VersionSchema(BaseModel):
    version: str
    loader: str
    type: Optional[str] = "release"
    release_time: Optional[datetime] = None
    is_current: bool = False


class VersionResponse(BaseModel):
    id: int
    version: str
    loader: str
    type: Optional[str] = None
    release_time: Optional[datetime] = None
    is_current: bool


# Tracked Mod Schemas
class TrackedModSchema(BaseModel):
    slug: str
    side: str  # client, server, both
    channel: str = "release"  # release, beta, alpha


class TrackedModResponse(BaseModel):
    slug: str
    side: str
    channel: str
    supported_client_side: Optional[str] = None
    supported_server_side: Optional[str] = None
    created_at: datetime


# Mod Version Schemas
class ModVersionResponse(BaseModel):
    id: int
    mod_slug: str
    version_id: str
    version_number: str
    mc_version_id: int
    loader: str
    channel: str
    created_at: datetime


# Compatibility Result Schemas
class ResultResponse(BaseModel):
    id: int
    mod_version_id: int
    mc_version_id: int
    status: str
    error: Optional[str]
    checked_at: datetime
    
    # Optional joined data
    mod_slug: Optional[str] = None
    mod_version_number: Optional[str] = None
    mc_version: Optional[str] = None
    loader: Optional[str] = None


# Log Schemas
class LogResponse(BaseModel):
    id: int
    level: str
    message: str
    created_at: datetime


# Summary Schemas
class SummaryResponse(BaseModel):
    compatible: int
    total: int
    server_compatible: int
    server_total: int
    client_compatible: int
    client_total: int


class StatusResponse(BaseModel):
    last_check: Optional[datetime] = None
    next_check: Optional[datetime] = None
