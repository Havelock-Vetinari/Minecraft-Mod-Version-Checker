import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.all import LogEntry, TrackedMod, ModVersion, MCVersion, CompatibilityResult

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_bg_trigger.db"
engine_test = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)

def test_add_mod_triggers_background_task(test_db):
    # Mock the background task function
    with patch("app.routers.mods.check_single_mod_task") as mock_task:
        response = client.post(
            "/api/mods",
            json={
                "slug": "fabric-api",
                "side": "both",
                "channel": "release"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "fabric-api"
        
        # Verify background task was called
        mock_task.assert_called_once()
        # Verify it was called with slug
        mock_task.assert_called_with("fabric-api")

def test_add_version_triggers_background_task(test_db):
    # Mock the background task function
    with patch("app.routers.versions.enrich_and_check_version_task") as mock_task:
        response = client.post(
            "/api/versions",
            json={
                "version": "1.21.1",
                "loader": "fabric",
                "type": "release",
                "is_current": True
            }
        )
        assert response.status_code == 200
        mock_task.assert_called_once()
        mock_task.assert_called_with("1.21.1", "fabric")
