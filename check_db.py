import sqlite3
import time

DB_FILE = "mods_checker.db" # Check if it's mods_checker or mod_checker. Directory list showed mod_checker.db? 
# Wait, list_dir showed "mod_checker.db". 
# But `app/core/database.py` likely uses `mods_checker.db` (plural). 
# Let's check Main.py -> core.database.
# I'll check both.

def check():
    for f in ["mods_checker.db", "mod_checker.db"]:
        try:
            conn = sqlite3.connect(f)
            c = conn.cursor()
            c.execute("SELECT count(*) FROM mc_versions")
            count = c.fetchone()[0]
            print(f"File {f}: Count = {count}")
            if count > 0:
                c.execute("SELECT version, type, release_time FROM mc_versions ORDER BY release_time DESC LIMIT 3")
                print("Latest 3:", c.fetchall())
        except Exception as e:
            print(f"File {f}: Error {e}")

if __name__ == "__main__":
    check()
