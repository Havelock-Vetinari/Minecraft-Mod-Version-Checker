from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class VersionSchema(BaseModel):
    version: str
    type: Optional[str] = "release"
    release_time: Optional[datetime] = None
    is_current: bool = False


class ModSchema(BaseModel):
    slug: str
    mc_version: Optional[str] = None
    loader: str
    side: str


class VersionResponse(BaseModel):
    id: int
    version: str
    type: Optional[str] = None
    release_time: Optional[datetime] = None
    is_current: bool


class ModResponse(BaseModel):
    id: int
    slug: str
    mc_version: Optional[str] = None
    loader: str
    side: str
    supported_client_side: Optional[str] = None
    supported_server_side: Optional[str] = None


class ResultResponse(BaseModel):
    id: int
    mod_slug: str
    mc_version: str
    loader: str
    status: str
    compatible_versions: List[str]
    mod_version_id: Optional[str] = None
    mod_version_number: Optional[str] = None
    error: Optional[str]
    checked_at: datetime


class LogResponse(BaseModel):
    id: int
    level: str
    message: str
    created_at: datetime


class SummaryResponse(BaseModel):
    compatible: int
    total: int
    server_compatible: int
    server_total: int
    client_compatible: int
    client_total: int
