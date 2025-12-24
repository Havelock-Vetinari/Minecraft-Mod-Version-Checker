from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class VersionSchema(BaseModel):
    version: str
    is_current: bool = False


class ModSchema(BaseModel):
    slug: str
    mc_version: Optional[str] = None
    loader: str
    side: str


class VersionResponse(BaseModel):
    id: int
    version: str
    is_current: bool


class ModResponse(BaseModel):
    id: int
    slug: str
    mc_version: Optional[str] = None
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
