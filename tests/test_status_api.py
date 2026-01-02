from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models.all import LogEntry, Base
from app.core.database import get_db
import pytest
import datetime
import os

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_status.db"
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

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)
    if os.path.exists("./test_status.db"):
        os.remove("./test_status.db")

def test_api_status():
    db = TestingSessionLocal()
    try:
        # Test 1: Empty logs
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["last_check"] is None
        assert data["next_check"] is None
        
        # Test 2: With check log
        log = LogEntry(level="INFO", message="Compatibility check completed", created_at=datetime.datetime.utcnow())
        db.add(log)
        db.commit()
        
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["last_check"] is not None
        assert data["next_check"] is not None
        
        # Verify delta is 5 minutes
        last = datetime.datetime.fromisoformat(data["last_check"].replace("Z", "+00:00"))
        next_val = datetime.datetime.fromisoformat(data["next_check"].replace("Z", "+00:00"))
        diff = next_val - last
        assert diff.total_seconds() == 300
        
    finally:
        db.close()

if __name__ == "__main__":
    pytest.main([__file__])
