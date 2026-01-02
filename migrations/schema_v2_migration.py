"""
Database Migration Script - Schema V2
Migrates from old schema (Mod, CompatibilityResult) to new schema (TrackedMod, ModVersion, CompatibilityResult)
"""

import sqlite3
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mod_checker.db")


def backup_old_data(conn):
    """Backup existing mods table"""
    cursor = conn.cursor()
    
    # Create backup table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mods_backup AS 
        SELECT * FROM mods
    """)
    
    count = cursor.execute("SELECT COUNT(*) FROM mods_backup").fetchone()[0]
    logger.info(f"Backed up {count} records from mods table")
    
    conn.commit()


def get_unique_loaders(conn):
    """Get all unique loaders from old mods table"""
    cursor = conn.cursor()
    result = cursor.execute("SELECT DISTINCT loader FROM mods").fetchall()
    loaders = [row[0] for row in result if row[0]]
    logger.info(f"Found loaders: {loaders}")
    return loaders if loaders else ["fabric"]  # Default to fabric if none


def migrate_mc_versions(conn, loaders):
    """
    Migrate mc_versions table to include loader field.
    Duplicate each version for each loader found in old mods.
    """
    cursor = conn.cursor()
    
    # Get existing versions
    old_versions = cursor.execute("""
        SELECT version, type, url, release_time, is_current, created_at 
        FROM mc_versions
    """).fetchall()
    
    # Drop old table
    cursor.execute("DROP TABLE IF EXISTS mc_versions_old")
    cursor.execute("ALTER TABLE mc_versions RENAME TO mc_versions_old")
    
    # Create new table with loader field
    cursor.execute("""
        CREATE TABLE mc_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL,
            loader TEXT NOT NULL,
            type TEXT,
            url TEXT,
            release_time TIMESTAMP,
            is_current BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(version, loader)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX ix_mc_versions_version ON mc_versions(version)")
    cursor.execute("CREATE INDEX ix_mc_versions_loader ON mc_versions(loader)")
    
    # Insert duplicated versions for each loader
    inserted = 0
    for old_ver in old_versions:
        version, vtype, url, release_time, is_current, created_at = old_ver
        for loader in loaders:
            cursor.execute("""
                INSERT INTO mc_versions (version, loader, type, url, release_time, is_current, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (version, loader, vtype, url, release_time, is_current, created_at))
            inserted += 1
    
    logger.info(f"Migrated {len(old_versions)} versions into {inserted} version+loader combinations")
    conn.commit()


def migrate_tracked_mods(conn):
    """Migrate data from old mods table to new tracked_mods table"""
    cursor = conn.cursor()
    
    # Get unique mods (by slug) from old table
    old_mods = cursor.execute("""
        SELECT DISTINCT slug, side, supported_client_side, supported_server_side, MIN(created_at) as created_at
        FROM mods
        GROUP BY slug
    """).fetchall()
    
    # Create tracked_mods table
    cursor.execute("""
        CREATE TABLE tracked_mods (
            slug TEXT PRIMARY KEY,
            side TEXT NOT NULL,
            channel TEXT NOT NULL DEFAULT 'release',
            supported_client_side TEXT,
            supported_server_side TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert data with default channel='release'
    for mod in old_mods:
        slug, side, supp_client, supp_server, created_at = mod
        cursor.execute("""
            INSERT INTO tracked_mods (slug, side, channel, supported_client_side, supported_server_side, created_at)
            VALUES (?, ?, 'release', ?, ?, ?)
        """, (slug, side or 'both', supp_client, supp_server, created_at))
    
    logger.info(f"Migrated {len(old_mods)} unique mods to tracked_mods")
    conn.commit()


def create_new_tables(conn):
    """Create new mod_versions and compatibility_results tables"""
    cursor = conn.cursor()
    
    # Create mod_versions table
    cursor.execute("""
        CREATE TABLE mod_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mod_slug TEXT NOT NULL,
            version_id TEXT NOT NULL,
            version_number TEXT NOT NULL,
            mc_version_id INTEGER NOT NULL,
            loader TEXT NOT NULL,
            channel TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (mod_slug) REFERENCES tracked_mods(slug) ON DELETE CASCADE,
            FOREIGN KEY (mc_version_id) REFERENCES mc_versions(id),
            UNIQUE(mod_slug, version_id, mc_version_id)
        )
    """)
    
    # Create indexes for mod_versions
    cursor.execute("CREATE INDEX ix_mod_versions_mod_slug ON mod_versions(mod_slug)")
    cursor.execute("CREATE INDEX ix_mod_versions_mc_version_id ON mod_versions(mc_version_id)")
    cursor.execute("CREATE INDEX ix_mod_versions_loader ON mod_versions(loader)")
    
    # Drop old compatibility_results if exists
    cursor.execute("DROP TABLE IF EXISTS compatibility_results")
    
    # Create new compatibility_results table
    cursor.execute("""
        CREATE TABLE compatibility_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mod_version_id INTEGER NOT NULL,
            mc_version_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            error TEXT,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (mod_version_id) REFERENCES mod_versions(id) ON DELETE CASCADE,
            FOREIGN KEY (mc_version_id) REFERENCES mc_versions(id),
            UNIQUE(mod_version_id, mc_version_id)
        )
    """)
    
    # Create indexes for compatibility_results
    cursor.execute("CREATE INDEX ix_compatibility_results_mod_version_id ON compatibility_results(mod_version_id)")
    cursor.execute("CREATE INDEX ix_compatibility_results_mc_version_id ON compatibility_results(mc_version_id)")
    cursor.execute("CREATE INDEX ix_compatibility_results_status ON compatibility_results(status)")
    
    logger.info("Created new tables: mod_versions, compatibility_results")
    conn.commit()


def cleanup_old_tables(conn):
    """Drop old tables after successful migration"""
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS mods")
    cursor.execute("DROP TABLE IF EXISTS mc_versions_old")
    
    logger.info("Cleaned up old tables")
    conn.commit()


def run_migration():
    """Run the complete migration"""
    if not os.path.exists(DATABASE_PATH):
        logger.error(f"Database not found at {DATABASE_PATH}")
        return False
    
    logger.info(f"Starting migration for database: {DATABASE_PATH}")
    logger.info("=" * 60)
    
    conn = sqlite3.connect(DATABASE_PATH)
    
    try:
        # Step 1: Backup
        logger.info("Step 1: Backing up old data...")
        backup_old_data(conn)
        
        # Step 2: Get loaders
        logger.info("Step 2: Identifying loaders...")
        loaders = get_unique_loaders(conn)
        
        # Step 3: Migrate MC Versions
        logger.info("Step 3: Migrating mc_versions table...")
        migrate_mc_versions(conn, loaders)
        
        # Step 4: Migrate Tracked Mods
        logger.info("Step 4: Migrating to tracked_mods table...")
        migrate_tracked_mods(conn)
        
        # Step 5: Create new tables
        logger.info("Step 5: Creating new tables (mod_versions, compatibility_results)...")
        create_new_tables(conn)
        
        # Step 6: Cleanup
        logger.info("Step 6: Cleaning up old tables...")
        cleanup_old_tables(conn)
        
        logger.info("=" * 60)
        logger.info("Migration completed successfully!")
        logger.info("Note: Compatibility results have been cleared. Background service will rebuild them.")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
