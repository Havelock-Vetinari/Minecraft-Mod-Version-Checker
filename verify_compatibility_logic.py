import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.background import get_target_versions
from app.models.all import MCVersion

@pytest.mark.asyncio
async def test_get_target_versions_fallback():
    # Mock DB session
    mock_db = MagicMock()
    
    # helper for async query (mocking sqlalchemy async-like behavior if needed, 
    # but here we mock sync query results as that's how the code is structured mostly, receiving DB session)
    # The code uses sync db.query() but async get_target_versions wrapper awaiting get_latest_stable_version
    
    # 1. Scenario: No current version set
    # Mock db.query(MCVersion).filter(...).first() -> None
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Mock get_latest_stable_version
    with patch('app.services.background.get_latest_stable_version', new_callable=AsyncMock) as mock_get_latest:
        mock_get_latest.return_value = {"id": "1.21.4", "type": "release"}
        
        targets = await get_target_versions(mock_db)
        
        assert targets == ["1.21.4"]
        print("\nSUCCESS: Fallback to latest stable version works!")

@pytest.mark.asyncio
async def test_get_target_versions_with_current():
    # Mock DB session
    mock_db = MagicMock()
    
    # 2. Scenario: Current version set (1.20)
    current_ver = MCVersion(version="1.20.1", is_current=True, release_time=100)
    newer_ver = MCVersion(version="1.20.2", is_current=False, release_time=200)
    older_ver = MCVersion(version="1.20", is_current=False, release_time=50)
    
    # Mock query returning current version
    mock_db.query.return_value.filter.return_value.first.return_value = current_ver
    
    # Mock query returning all versions
    mock_db.query.return_value.all.return_value = [current_ver, newer_ver, older_ver]
    
    targets = await get_target_versions(mock_db)
    
    # Should include current (1.20.1) and newer (1.20.2), but NOT older (1.20)
    assert "1.20.1" in targets
    assert "1.20.2" in targets
    assert "1.20" not in targets
    assert len(targets) == 2
    print("\nSUCCESS: Current + Newer versions logic works!")

if __name__ == "__main__":
    import sys
    # Run simple check without full pytest overhead for speed if desired, 
    # but using pytest.main is safer for async
    sys.exit(pytest.main(["-v", "verify_compatibility_logic.py"]))
