import sqlite3
import os
import shutil

DB_PATH = "attendance_v2.db"
FACES_DIR = "known_faces"

def factory_reset():
    print("WARNING: This will delete ALL data and ALL images.")
    confirm = input("Type 'YES' to proceed: ")
    
    if confirm != "YES":
        print("Reset cancelled.")
        return

    # 1. Wipe Database Tables
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM students")
        c.execute("DELETE FROM faculty")
        c.execute("DELETE FROM sessions")
        c.execute("DELETE FROM attendance")
        # Reset the auto-increment counters back to 1
        c.execute("DELETE FROM sqlite_sequence")
        conn.commit()
        conn.close()
        print("✓ Database tables cleared and IDs reset.")
    except Exception as e:
        print(f"Database error: {e}")

    # 2. Wipe Image Folders
    for subdir in ["students", "faculty"]:
        path = os.path.join(FACES_DIR, subdir)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)
    print("✓ Image folders completely wiped and recreated.")
    
    print("\nFACTORY RESET COMPLETE. You have a completely clean slate.")

if __name__ == "__main__":
    factory_reset()