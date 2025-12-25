import asyncio
import httpx
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.all import MCVersion, CompatibilityResult, Mod
from app.services.background import enrich_and_check_version_task

# 1. Setup: Clear test version if it exists
def cleanup_version(version: str):
    db: Session = SessionLocal()
    try:
        ver = db.query(MCVersion).filter(MCVersion.version == version).first()
        if ver:
            db.delete(ver)
            
        # Also cleanup results for this version
        results = db.query(CompatibilityResult).filter(CompatibilityResult.mc_version == version).all()
        for r in results:
            db.delete(r)
            
        db.commit()
    finally:
        db.close()

# 2. Main Verification
async def verify_manual_add():
    TEST_VERSION = "1.20.2"
    
    print(f"--- Cleaning up {TEST_VERSION} ---")
    cleanup_version(TEST_VERSION)
    
    # Simulate API Request (we can't easily mock BackgroundTasks in a script without running the whole app, 
    # so we'll simulate the component steps: Add DB Entry -> Run Task)
    
    print(f"\n--- Adding Version {TEST_VERSION} to DB (Simulating API) ---")
    db = SessionLocal()
    try:
        # Mock what the API does immediately
        version = MCVersion(
            version=TEST_VERSION,
            type="release",
            release_time=None, # Should be filled by background
            is_current=False
        )
        db.add(version)
        db.commit()
        print("Version added to DB.")
        
        # Ensure we have at least one mod (create dummy if needed for test?)
        mod = db.query(Mod).first()
        if not mod:
            print("No mods found. Creating dummy mod for test.")
            mod = Mod(slug="fabric-api", loader="fabric", side="both")
            db.add(mod)
            db.commit()

    finally:
        db.close()

    print(f"\n--- Running Background Task for {TEST_VERSION} ---")
    await enrich_and_check_version_task(TEST_VERSION)
    
    print(f"\n--- Verifying Results ---")
    db = SessionLocal()
    try:
        # Check Version details
        ver = db.query(MCVersion).filter(MCVersion.version == TEST_VERSION).first()
        if ver and ver.release_time:
            print(f"[PASS] Version {TEST_VERSION} enriched with release_time: {ver.release_time}")
        else:
            print(f"[FAIL] Version {TEST_VERSION} NOT enriched properly. Release time: {ver.release_time if ver else 'None'}")
            
        # Check Compatibility Results
        results = db.query(CompatibilityResult).filter(CompatibilityResult.mc_version == TEST_VERSION).all()
        if results:
            print(f"[PASS] Found {len(results)} compatibility checks for {TEST_VERSION}.")
            for r in results:
                print(f"  - {r.mod_slug}: {r.status}")
        else:
            print(f"[FAIL] No compatibility checks found for {TEST_VERSION}.")
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(verify_manual_add())
