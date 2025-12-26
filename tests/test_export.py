import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models.all import Mod, CompatibilityResult
import yaml

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_export.db"
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

def test_export_filtering():
    db = TestingSessionLocal()
    
    # 1. Add mods with different sides
    mod_server = Mod(slug="mod-server", mc_version="1.20.4", loader="fabric", side="server")
    mod_both = Mod(slug="mod-both", mc_version="1.20.4", loader="fabric", side="both")
    mod_client = Mod(slug="mod-client", mc_version="1.20.4", loader="fabric", side="client")
    
    db.add_all([mod_server, mod_both, mod_client])
    db.commit()

    # 2. Add compatibility results (only compatible ones)
    res_server = CompatibilityResult(mod_slug="mod-server", mc_version="1.20.4", loader="fabric", status="compatible", mod_version_id="v1")
    res_both = CompatibilityResult(mod_slug="mod-both", mc_version="1.20.4", loader="fabric", status="compatible", mod_version_id="v2")
    res_client = CompatibilityResult(mod_slug="mod-client", mc_version="1.20.4", loader="fabric", status="compatible", mod_version_id="v3")
    
    db.add_all([res_server, res_both, res_client])
    db.commit()

    # 3. Request export for 1.20.4
    response = client.get("/api/mods/export?mc_version=1.20.4")
    assert response.status_code == 200
    
    data = response.json()
    assert "yaml" in data
    
    yaml_content = yaml.safe_load(data["yaml"])
    env = yaml_content["services"]["mc"]["environment"]
    
    projects_str = env["MODRINTH_PROJECTS"]
    projects = [p.strip() for p in projects_str.split("\n") if p.strip()]
    
    # Verify that only server and both are present
    assert "mod-server:v1" in projects
    assert "mod-both:v2" in projects
    assert "mod-client:v3" not in projects
    assert len(projects) == 2

def test_export_no_server_mods():
    db = TestingSessionLocal()
    
    # Add only client mod
    mod_client = Mod(slug="mod-client", mc_version="1.20.4", loader="fabric", side="client")
    db.add(mod_client)
    db.commit()

    # Add compatibility result
    res_client = CompatibilityResult(mod_slug="mod-client", mc_version="1.20.4", loader="fabric", status="compatible", mod_version_id="v3")
    db.add(res_client)
    db.commit()

    # Request export - should fail as no server-side mods
    response = client.get("/api/mods/export?mc_version=1.20.4")
    assert response.status_code == 400
    assert "No server-side or 'both' mods found" in response.json()["detail"]
