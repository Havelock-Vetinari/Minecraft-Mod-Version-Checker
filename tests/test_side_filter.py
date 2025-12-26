import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from app.models.all import Mod, CompatibilityResult, MCVersion
from datetime import datetime

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_side.db"
if os.path.exists("./test_side.db"):
    os.remove("./test_side.db")

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Add MC Version
    v = MCVersion(version="1.21.1", type="release", release_time=datetime.now())
    db.add(v)
    
    # Add mods with different sides
    m1 = Mod(slug="mod-both", loader="fabric", side="both")
    m2 = Mod(slug="mod-server", loader="fabric", side="server")
    m3 = Mod(slug="mod-client", loader="fabric", side="client")
    db.add_all([m1, m2, m3])
    
    # Add results
    r1 = CompatibilityResult(mod_slug="mod-both", loader="fabric", mc_version="1.21.1", status="compatible", checked_at=datetime.now())
    r2 = CompatibilityResult(mod_slug="mod-server", loader="fabric", mc_version="1.21.1", status="compatible", checked_at=datetime.now())
    r3 = CompatibilityResult(mod_slug="mod-client", loader="fabric", mc_version="1.21.1", status="compatible", checked_at=datetime.now())
    db.add_all([r1, r2, r3])
    
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_side.db"):
        os.remove("./test_side.db")

def test_filter_all():
    response = client.get("/api/results")
    assert response.status_code == 200
    assert len(response.json()) == 3

def test_filter_server():
    response = client.get("/api/results?side=server")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    slugs = [r["mod_slug"] for r in data]
    assert "mod-both" in slugs
    assert "mod-server" in slugs
    assert "mod-client" not in slugs

def test_filter_client():
    response = client.get("/api/results?side=client")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    slugs = [r["mod_slug"] for r in data]
    assert "mod-both" in slugs
    assert "mod-client" in slugs
    assert "mod-server" not in slugs

def test_filter_both_only():
    response = client.get("/api/results?side=both")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["mod_slug"] == "mod-both"
