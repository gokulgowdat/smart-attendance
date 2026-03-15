import sqlite3

def upgrade_database():
    conn = sqlite3.connect('attendance_v2.db')
    try:
        # Add a new column to store the classes/subjects the professor teaches
        conn.execute("ALTER TABLE faculty ADD COLUMN subjects TEXT DEFAULT 'No subjects listed yet.'")
        print("Success: 'subjects' column added to faculty table!")
    except sqlite3.OperationalError:
        print("Note: The column already exists. Ready to go!")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    upgrade_database()