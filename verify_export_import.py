import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.all import Base, Mod, MCVersion, CompatibilityResult
from app.routers.mods import export_mods, import_mods
from fastapi import BackgroundTasks

# Setup in-memory database for testing
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

def test_export_import():
    db = SessionLocal()
    
    # Add dummy data
    v = MCVersion(version="1.21.1", is_current=True)
    db.add(v)
    
    m1 = Mod(slug="sodium", loader="fabric", side="both", mc_version="1.21.1")
    db.add(m1)
    
    # Mock compatibility result
    res = CompatibilityResult(
        mod_slug="sodium", 
        mc_version="1.21.1", 
        loader="fabric", 
        status="compatible", 
        mod_version_id="sodium-v1"
    )
    db.add(res)
    db.commit()
    
    # Test Export
    export_res = export_mods(db)
    yaml_str = export_res["yaml"]
    print("Exported YAML:")
    print(yaml_str)
    
    config = yaml.safe_load(yaml_str)
    projects = config["services"]["mc"]["environment"]["MODRINTH_PROJECTS"]
    assert "sodium:sodium-v1" in projects
    print("Export verification passed!")
    
    # Test Import
    # Delete mod first
    db.delete(m1)
    db.commit()
    
    background_tasks = BackgroundTasks()
    import_res = import_mods(background_tasks, db, {"yaml": yaml_str})
    print(f"Import results: {import_res}")
    
    imported_mod = db.query(Mod).filter(Mod.slug == "sodium").first()
    assert imported_mod is not None
    assert imported_mod.loader == "fabric"
    print("Import verification passed!")
    
    db.close()

if __name__ == "__main__":
    try:
        test_export_import()
    except Exception as e:
        print(f"Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
