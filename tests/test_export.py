import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models.all import TrackedMod, ModVersion, MCVersion, CompatibilityResult, LogEntry
import yaml
from datetime import datetime

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
    
    # 1. Setup MC Version
    mc_ver = MCVersion(version="1.20.4", loader="fabric", type="release", release_time=datetime.utcnow())
    db.add(mc_ver)
    db.commit()
    
    # 2. Add mods with different sides
    mod_server = TrackedMod(slug="mod-server", side="server", channel="release")
    mod_both = TrackedMod(slug="mod-both", side="both", channel="release")
    mod_client = TrackedMod(slug="mod-client", side="client", channel="release")
    
    db.add_all([mod_server, mod_both, mod_client])
    db.commit()

    # 3. Add mod versions and compatibility results
    for mod_slug, ver_id in [("mod-server", "v1"), ("mod-both", "v2"), ("mod-client", "v3")]:
        mv = ModVersion(
            mod_slug=mod_slug,
            version_id=ver_id,
            version_number="1.0.0",
            mc_version_id=mc_ver.id,
            loader="fabric",
            channel="release"
        )
        db.add(mv)
        db.flush()
        
        cr = CompatibilityResult(
            mod_version_id=mv.id,
            mc_version_id=mc_ver.id,
            status="compatible"
        )
        db.add(cr)
    
    db.commit()

    # 4. Request export for 1.20.4 (fabric)
    response = client.get("/api/mods/export?mc_version=1.20.4&loader=fabric")
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
    assert "mod-client:v3" not in " ".join(projects)
    assert len(projects) == 2

def test_export_no_server_mods():
    db = TestingSessionLocal()
    
    # Setup MC Version
    mc_ver = MCVersion(version="1.20.4", loader="fabric", type="release", release_time=datetime.utcnow())
    db.add(mc_ver)
    db.commit()
    
    # Add only client mod
    mod_client = TrackedMod(slug="mod-client", side="client", channel="release")
    db.add(mod_client)
    db.commit()

    # Add version and result
    mv = ModVersion(mod_slug="mod-client", version_id="v3", version_number="1.0.0", mc_version_id=mc_ver.id, loader="fabric", channel="release")
    db.add(mv)
    db.flush()
    db.add(CompatibilityResult(mod_version_id=mv.id, mc_version_id=mc_ver.id, status="compatible"))
    db.commit()

    # Request export - should fail as no server-side mods
    response = client.get("/api/mods/export?mc_version=1.20.4&loader=fabric")
    assert response.status_code == 400
    assert "No server-side or 'both' mods found" in response.json()["detail"]

def test_export_with_incompatible_client_mods():
    """Test that incompatible client-side mods don't block export when server/both mods are compatible"""
    db = TestingSessionLocal()
    
    # Setup MC Version
    mc_ver = MCVersion(version="1.20.4", loader="fabric", type="release", release_time=datetime.utcnow())
    db.add(mc_ver)
    db.commit()
    
    # 1. Add mods with different sides
    mod_server = TrackedMod(slug="mod-server", side="server", channel="release")
    mod_both = TrackedMod(slug="mod-both", side="both", channel="release")
    mod_client = TrackedMod(slug="mod-client", side="client", channel="release")
    
    db.add_all([mod_server, mod_both, mod_client])
    db.commit()

    # 2. Add sub-components
    # Server/Both compatible
    for mod_slug, ver_id in [("mod-server", "v1"), ("mod-both", "v2")]:
        mv = ModVersion(mod_slug=mod_slug, version_id=ver_id, version_number="1.0.0", mc_version_id=mc_ver.id, loader="fabric", channel="release")
        db.add(mv)
        db.flush()
        db.add(CompatibilityResult(mod_version_id=mv.id, mc_version_id=mc_ver.id, status="compatible"))
    
    # Client INCOMPATIBLE (no version record or status="incompatible")
    # Actually, in our new logic, no record means incompatible, but we can have an "incompatible" status too if error
    # Let's just not add a compatible result for client
    
    db.commit()

    # 3. Request export for 1.20.4 - should SUCCEED despite incompatible client mod
    response = client.get("/api/mods/export?mc_version=1.20.4&loader=fabric")
    assert response.status_code == 200
    
    data = response.json()
    assert "yaml" in data
    
    yaml_content = yaml.safe_load(data["yaml"])
    env = yaml_content["services"]["mc"]["environment"]
    
    projects_str = env["MODRINTH_PROJECTS"]
    projects = [p.strip() for p in projects_str.split("\n") if p.strip()]
    
    # Verify that only compatible server and both mods are present
    assert "mod-server:v1" in projects
    assert "mod-both:v2" in projects
    assert "mod-client" not in " ".join(projects)
    assert len(projects) == 2
