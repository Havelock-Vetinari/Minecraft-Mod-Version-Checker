import sqlite3
import os

DB_FILE = "mod_checker.db"  # Matches config.py

def migrate():
    if not os.path.exists(DB_FILE):
        print("Database not found, skipping migration.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(mc_versions)")
    columns = [row[1] for row in cursor.fetchall()]
    
    try:
        if "type" not in columns:
            print("Adding 'type' column...")
            cursor.execute("ALTER TABLE mc_versions ADD COLUMN type VARCHAR")
            
        if "url" not in columns:
            print("Adding 'url' column...")
            cursor.execute("ALTER TABLE mc_versions ADD COLUMN url VARCHAR")
            
        if "release_time" not in columns:
            print("Adding 'release_time' column...")
            cursor.execute("ALTER TABLE mc_versions ADD COLUMN release_time DATETIME")
            
        conn.commit()
        print("Migration complete.")
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
