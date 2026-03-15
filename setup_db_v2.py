import sqlite3

def setup_database():
    print("Building Centralized Smart Attendance V2 Database...")
    conn = sqlite3.connect("attendance_v2.db")
    c = conn.cursor()

    # 1. Faculty Table (Upgraded with Web App Login)
    c.execute("""
        CREATE TABLE IF NOT EXISTS faculty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # 2. Students Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            label TEXT UNIQUE,
            roll TEXT,
            year TEXT,
            section TEXT
        )
    """)

    # 3. Sessions Table (Upgraded for Planning & Multiple Sections)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty_id INTEGER,
            year TEXT,
            sections TEXT, 
            subject TEXT,
            period TEXT,
            room_number TEXT,
            block TEXT,
            start_time TEXT,
            end_time TEXT,
            status TEXT DEFAULT 'PLANNED' 
        )
    """)

    # 4. Attendance Table (Upgraded for Temporary Tracking)
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            student_label TEXT,
            status TEXT, 
            last_seen TEXT,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    """)

    # --- INSERT TEST DATA ---
    
    # Add a Pilot Professor (You!)
    c.execute("INSERT OR IGNORE INTO faculty (name, username, password) VALUES ('Prof. Gokul', 'gokul', 'password123')")

    # Add Group Mates as Students (Year 1, Section A & B to test multiple sections)
    students = [
        ('Gagan Gowda', 'gagan', '25EE042', '1', 'A'),
        ('Madhushree A', 'madhushree', '25ES015', '1', 'A'),
        ('Manasa M', 'manasa', '25ES009', '1', 'B'),
        ('Manaswi S Gowda', 'manaswi', '25ES008', '1', 'B'),
        ('Moinuddin M', 'moinuddin', '25ES017', '1', 'B')
    ]
    
    for s in students:
        try:
            c.execute("INSERT INTO students (name, label, roll, year, section) VALUES (?, ?, ?, ?, ?)", s)
        except sqlite3.IntegrityError:
            pass # Skips if they already exist

    conn.commit()
    conn.close()
    print("Success! 'attendance_v2.db' has been created and populated with test data.")

if __name__ == "__main__":
    setup_database()
