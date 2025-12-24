import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from app import app, get_db, Base, engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine_test = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

Base.metadata.create_all(bind=engine_test)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)

@pytest.mark.asyncio
async def test_get_latest_minecraft_version():
    with patch("httpx.AsyncClient", autospec=True) as MockClient:
        mock_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_instance
        
        # Mock response for /tag/game_version
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"version": "1.20.4", "version_type": "release"},
            {"version": "1.21.1", "version_type": "snapshot"}
        ]
        mock_response.raise_for_status.return_value = None
        mock_instance.get.return_value = mock_response

        from app import get_latest_minecraft_version
        version = await get_latest_minecraft_version()
        assert version == "1.20.4"

@pytest.mark.asyncio
async def test_get_mod_compatible_versions():
    with patch("httpx.AsyncClient", autospec=True) as MockClient:
        mock_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_instance

        # Mock project check
        mock_project_response = MagicMock()
        mock_project_response.status_code = 200
        mock_project_response.raise_for_status.return_value = None
        
        # Mock versions response
        mock_versions_response = MagicMock()
        mock_versions_response.json.return_value = [
            {"game_versions": ["1.20.4", "1.20.1"]},
            {"game_versions": ["1.19.4"]}
        ]
        mock_versions_response.raise_for_status.return_value = None
        
        # Setup side effects for get calls
        # First call is project check, second is versions
        mock_instance.get.side_effect = [mock_project_response, mock_versions_response]

        from app import get_mod_compatible_versions
        versions, error = await get_mod_compatible_versions("test-mod", "fabric")
        
        assert error is None
        assert "1.20.4" in versions
        assert "1.19.4" in versions

def test_api_create_version(test_db):
    response = client.post(
        "/api/versions",
        json={"version": "1.20.4", "is_current": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.20.4"
    assert data["is_current"] == True

    # Verify via get
    response = client.get("/api/versions/current")
    assert response.status_code == 200
    assert response.json()["version"] == "1.20.4"

def test_api_create_mod(test_db):
    response = client.post(
        "/api/mods",
        json={
            "slug": "fabric-api",
            "mc_version": "1.20.4",
            "loader": "fabric",
            "side": "both"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "fabric-api"
    
    # Verify via get
    response = client.get("/api/mods")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["slug"] == "fabric-api"

def test_api_get_results_empty(test_db):
    response = client.get("/api/results")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
