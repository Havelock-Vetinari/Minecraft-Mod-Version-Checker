import httpx
import logging
from typing import List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODRINTH_BASE = "https://api.modrinth.com/v2"
USER_AGENT = "minecraft-mod-checker/1.0 (github.com)"


async def get_latest_minecraft_version() -> str:
    """Fetch the latest released Minecraft version from Modrinth"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{MODRINTH_BASE}/tag/game_version",
                headers={"User-Agent": USER_AGENT}
            )
            response.raise_for_status()
            versions = response.json()

            releases = [v for v in versions if v.get("version_type") == "release"]
            if releases:
                return releases[0]["version"]
            return versions[0]["version"] if versions else "1.21.1"
    except Exception as e:
        logger.error(f"Failed to fetch latest MC version: {e}")
        return "1.21.1"


async def get_mod_compatible_versions(slug: str, loader: str) -> Tuple[List[str], Optional[str]]:
    """
    Get all Minecraft versions this mod is compatible with.
    Returns (compatible_versions, error_message)
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            headers = {"User-Agent": USER_AGENT}

            project_url = f"{MODRINTH_BASE}/project/{slug}"
            try:
                project_response = await client.get(project_url, headers=headers, timeout=5)
                project_response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return [], f"Mod '{slug}' not found on Modrinth"
                raise

            versions_url = f"{MODRINTH_BASE}/project/{slug}/version"
            params = {
                "loaders": loader,
            }

            versions_response = await client.get(versions_url, params=params, headers=headers, timeout=10)
            versions_response.raise_for_status()

            versions = versions_response.json()
            if not isinstance(versions, list):
                versions = [versions]

            compatible_mc_versions = []

            for version in versions:
                game_versions = version.get("game_versions", [])
                compatible_mc_versions.extend(game_versions)

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
