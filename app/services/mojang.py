import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional

MOJANG_MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"

async def fetch_version_manifest() -> Dict[str, Any]:
    """Fetch the full version manifest from Mojang"""
    async with httpx.AsyncClient() as client:
        response = await client.get(MOJANG_MANIFEST_URL)
        response.raise_for_status()
        return response.json()

def parse_time(time_str: str) -> datetime:
    """Parse Mojang time string (ISO 8601) and return naive datetime"""
    # Example: "2023-12-05T10:00:00+00:00"
    try:
        dt = datetime.fromisoformat(time_str)
        return dt.replace(tzinfo=None)
    except ValueError:
        # Fallback
        return datetime.utcnow()

async def get_all_versions() -> List[Dict[str, Any]]:
    """
    Get all versions, parsed and sorted by release time (newest first).
    Returns list of dicts with: id, type, url, releaseTime, time
    """
    manifest = await fetch_version_manifest()
    versions = manifest.get("versions", [])
    
    # Sort just in case, though usually sorted in manifest
    # We want to ensure we have datetime objects
    for v in versions:
        v["release_dt"] = parse_time(v["releaseTime"])
        
    return versions

async def get_latest_stable_version() -> Optional[Dict[str, Any]]:
    """Get the latest release version"""
    manifest = await fetch_version_manifest()
    latest_id = manifest.get("latest", {}).get("release")
    versions = manifest.get("versions", [])
    
    for v in versions:
        if v["id"] == latest_id:
            v["release_dt"] = parse_time(v["releaseTime"])
            return v
    return None


async def get_version_details(version_id: str) -> Optional[Dict[str, Any]]:
    """Get details for a specific version from the manifest"""
    manifest = await fetch_version_manifest()
    versions = manifest.get("versions", [])
    
    for v in versions:
        if v["id"] == version_id:
            v["release_dt"] = parse_time(v["releaseTime"])
            return v
    return None

