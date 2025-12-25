
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_bg.db"
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

def test_add_mod_triggers_background_task(test_db):
    # Mock the background task function
    with patch("app.routers.mods.check_single_mod_task") as mock_task:
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
        
        # Verify background task was added
        # Note: TestClient with BackgroundTasks runs them appropriately, 
        # but we are mocking the function passed to add_task, so we check if add_task received it.
        # Actually, TestClient executes background tasks synchronously by default.
        # So we can check if our mock was called.
        
        mock_task.assert_called_once()
        # You might want to check call args if possible, typically (mod_id)
        # mod_id = data["id"]
        # mock_task.assert_called_with(mod_id)
