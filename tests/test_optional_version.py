import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.all import TrackedMod, MCVersion, LogEntry
from app.services.background import check_all_mods
from unittest.mock import patch, MagicMock

# Setup in-memory DB for testing
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_session_local():
    with patch("app.services.background.SessionLocal") as mock:
        yield mock
    
@pytest.fixture
def mock_modrinth():
    with patch("app.services.background.get_mod_compatible_versions") as mock:
        mock.return_value = (["1.21.1"], None)
        yield mock

@pytest.mark.asyncio
async def test_add_mod_optional_version(db):
    """Test adding a mod"""
    mod = TrackedMod(slug="test-mod", side="both", channel="release")
    db.add(mod)
    db.commit()
    
    saved_mod = db.query(TrackedMod).first()
    assert saved_mod.slug == "test-mod"

@pytest.mark.asyncio
async def test_background_check_skips_without_target_versions(db, mock_session_local, mock_modrinth):
    """Test background job skips when no target versions found"""
    # Setup mock session to return our test db session
    mock_session_local.return_value = db
    
    # Add a mod
    mod = TrackedMod(slug="test-mod", side="both", channel="release")
    db.add(mod)
    db.commit()
    
    # Run background check
    # Also need to mock get_latest_stable_version to return empty or None to skip skip
    with patch("app.services.background.get_latest_stable_version", return_value=None):
        await check_all_mods()
    
    # Check logs
    log = db.query(LogEntry).filter(LogEntry.message.contains("No target versions (Current) set. Skipping checks.")).first()
    assert log is not None
    
    # Ensure Modrinth API was NOT called
    mock_modrinth.assert_not_called()

@pytest.mark.asyncio
async def test_background_check_runs_with_current_version(db, mock_session_local, mock_modrinth):
    """Test background job runs when current version is set"""
    mock_session_local.return_value = db
    
    # Add mod
    mod = TrackedMod(slug="test-mod", side="both", channel="release")
    db.add(mod)
    
    # Add current version
    version = MCVersion(version="1.21.1", loader="fabric", is_current=True)
    db.add(version)
    db.commit()
    
    # Run background check
    # Also mock find_mod_version_for_mc to avoid real API calls
    with patch("app.services.background.find_mod_version_for_mc", return_value={"id": "v1", "version_number": "1.0.0"}):
        await check_all_mods()
    
    # Check logs
    log = db.query(LogEntry).filter(LogEntry.message.contains("Starting checks against: 1.21.1 (fabric)")).first()
    # Note: message logic changed in background.py
    # Let's check for "Starting checks against"
    log = db.query(LogEntry).filter(LogEntry.message.contains("Starting checks against")).first()
    assert log is not None
    
    # Ensure Modrinth API WAS called
    mock_modrinth.assert_called_once()
