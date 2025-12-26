from fastapi.testclient import TestClient
from app.main import app
from app.models.all import LogEntry
from app.core.database import SessionLocal
import pytest

client = TestClient(app)

def test_api_status():
    db = SessionLocal()
    try:
        # Clear logs to ensure deterministic test
        db.query(LogEntry).delete()
        db.commit()
        
        # Test 1: Empty logs
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["last_check"] is None
        assert data["next_check"] is None
        
        # Test 2: With check log
        import datetime
        log = LogEntry(level="INFO", message="Compatibility check completed", created_at=datetime.datetime.utcnow())
        db.add(log)
        db.commit()
        
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["last_check"] is not None
        assert data["next_check"] is not None
        
        # Verify timezone indicator (ISO format with +00:00 or Z)
        assert "+00:00" in data["last_check"] or "Z" in data["last_check"]
        assert "+00:00" in data["next_check"] or "Z" in data["next_check"]
        
        # Verify delta is 5 minutes
        last = datetime.datetime.fromisoformat(data["last_check"])
        next_val = datetime.datetime.fromisoformat(data["next_check"])
        diff = next_val - last
        assert diff.total_seconds() == 300
        
    finally:
        db.close()

if __name__ == "__main__":
    pytest.main([__file__])
