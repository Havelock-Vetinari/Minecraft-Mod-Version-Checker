import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.modrinth import find_mod_version_for_mc

@pytest.mark.asyncio
async def test_find_mod_version_found():
    # Mock httpx client response
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"id": "ver_release_123", "version_number": "1.2.3", "version_type": "release", "date_published": "2023-01-02T00:00:00Z"},
        {"id": "ver_release_old", "version_number": "1.2.2", "version_type": "release", "date_published": "2023-01-01T00:00:00Z"},
        {"id": "ver_beta_123", "version_number": "1.2.4-beta", "version_type": "beta", "date_published": "2023-01-03T00:00:00Z"}
    ]
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        MockClient.return_value.__aenter__.return_value = mock_client_instance
        
        # Test finding latest release
        ver_data = await find_mod_version_for_mc("slug-123", "fabric", "1.21.1")
        
        assert ver_data == {"id": "ver_release_123", "version_number": "1.2.3"}
        print("\nSUCCESS: Found latest stable version dict")

@pytest.mark.asyncio
async def test_find_mod_version_fallback_beta():
    # Only beta versions available
    mock_response = MagicMock()
    mock_response.json.return_value = [
         {"id": "ver_beta_123", "version_number": "1.2.4-beta", "version_type": "beta", "date_published": "2023-01-03T00:00:00Z"}
    ]
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        MockClient.return_value.__aenter__.return_value = mock_client_instance
        
        # Should fallback to the beta version
        ver_data = await find_mod_version_for_mc("slug-123", "fabric", "1.21.1")
        
        assert ver_data == {"id": "ver_beta_123", "version_number": "1.2.4-beta"}
        print("\nSUCCESS: Fallback to beta version works")

@pytest.mark.asyncio
async def test_find_mod_version_none():
    # No versions found
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        MockClient.return_value.__aenter__.return_value = mock_client_instance
        
        version_id = await find_mod_version_for_mc("slug-123", "fabric", "1.21.1")
        
        assert version_id is None
        print("\nSUCCESS: Returns None when no versions found")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "tests/test_modrinth_version_check.py"]))
