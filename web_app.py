from flask import Flask, render_template, request, redirect, session, flash, jsonify
import sqlite3
from datetime import datetime
import threading
import time
import cv2
import os
from werkzeug.utils import secure_filename
from face_engine_v2 import FaceEngineV2

# Static folder mapping so Profile photos load correctly
app = Flask(__name__, static_url_path='/static', static_folder='.')
app.secret_key = "smart_attendance_super_secret"

# --- CONFIGURATION ---
CAMERA_URL = "http://YOUR_CAMERA_IP:8080/video"  # UPDATE THIS TO YOUR CAMERA IP
SCAN_INTERVAL = 15  
FACES_DIR = "known_faces/faculty"
active_threads = {} 

os.makedirs(FACES_DIR, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect('attendance_v2.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- AI SCANNER (WITH RESTORED LOGS) ---
def background_scanner(session_id):
    print(f"\n[AI Scanner] Booting up for Session {session_id}...")
    engine = FaceEngineV2()
    
    while active_threads.get(session_id, False):
        print(f"\n[AI Scanner] Connecting to camera at {CAMERA_URL}...")
        cap = cv2.VideoCapture(CAMERA_URL)
        
        if cap.isOpened():
            print("[AI Scanner] Warming up sensor for 2.5 seconds...")
            start_time = time.time()
            while time.time() - start_time < 3.5: 
                cap.read() 
                
            print("[AI Scanner] Snapping final adjusted photo...")
            ret, frame = cap.read()
            if ret:
                _, recognized_labels = engine.process_frame(frame)
                
                # THIS WILL TELL US IF YOLO IS SEEING GHOSTS
                print(f"[AI Scanner] YOLOv8 Detected exactly: {recognized_labels}")
                
                if recognized_labels:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    current_time = datetime.now().strftime("%H:%M:%S")
                    for label in recognized_labels:
                        existing = cursor.execute("SELECT id FROM attendance WHERE session_id = ? AND student_label = ?", (session_id, label)).fetchone()
                        if existing:
                            cursor.execute("UPDATE attendance SET last_seen = ?, status = 'Present' WHERE id = ?", (current_time, existing['id']))
                        else:
                            cursor.execute("INSERT INTO attendance (session_id, student_label, status, last_seen) VALUES (?, ?, 'Present', ?)", (session_id, label, current_time))
                    conn.commit()
                    conn.close()
            else:
                print("[AI Scanner] Error: Failed to grab frame.")
            cap.release()
        else:
            print("[AI Scanner] Error: Could not connect to PoE Camera.")
            
        print(f"[AI Scanner] Sleeping for {SCAN_INTERVAL} seconds...")
        for _ in range(SCAN_INTERVAL):
            if not active_threads.get(session_id, False): break
            time.sleep(1)
            
    print(f"\n[AI Scanner] Session {session_id} terminated. Shutting down engine.")

# --- CORE ROUTES ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        prof = conn.execute('SELECT * FROM faculty WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        
        if prof:
            session['faculty_id'] = prof['id']
            session['faculty_name'] = prof['name']
            session['faculty_username'] = prof['username']
            if 'theme' not in session: session['theme'] = 'light'
            return redirect('/dashboard')
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username').lower()
        password = request.form.get('password')
        photo = request.files.get('photo')

        if not photo or photo.filename == '':
            flash('ID Photo is required!')
            return redirect('/register')

        try:
            ext = os.path.splitext(photo.filename)[1]
            filename = secure_filename(f"{username}{ext}")
            photo.save(os.path.join(FACES_DIR, filename))

            conn = get_db_connection()
            conn.execute("INSERT INTO faculty (name, username, password) VALUES (?, ?, ?)", (name, username, password))
            conn.commit()
            conn.close()
            flash('Account created successfully! You may now log in.')
            return redirect('/')
        except sqlite3.IntegrityError:
            flash('Username already exists!')
            
    return render_template('register.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'faculty_id' not in session: return redirect('/')
    conn = get_db_connection()
    if request.method == 'POST':
        new_name = request.form.get('name')
        new_username = request.form.get('username')
        new_password = request.form.get('password')
        new_subjects = request.form.get('subjects')
        
        conn.execute("UPDATE faculty SET name=?, username=?, password=?, subjects=? WHERE id=?", 
                     (new_name, new_username, new_password, new_subjects, session['faculty_id']))
        conn.commit()
        session['faculty_name'] = new_name
        flash("Profile updated successfully!")

    prof = conn.execute('SELECT * FROM faculty WHERE id = ?', (session['faculty_id'],)).fetchone()
    conn.close()
    return render_template('profile.html', prof=prof, theme=session.get('theme', 'light'))

# --- NEW FEATURE: INDIVIDUAL STUDENT SEARCH ---
@app.route('/student_history', methods=['GET', 'POST'])
def student_history():
    if 'faculty_id' not in session: return redirect('/')
    
    student_data = None
    records = []

    if request.method == 'POST':
        search_query = request.form.get('search_query').strip()
        conn = get_db_connection()

        # Find the student by Roll Number
        student = conn.execute("SELECT * FROM students WHERE roll = ?", (search_query,)).fetchone()

        if student:
            student_data = student
            section_query = f"%{student['section']}%"

            # Find all completed sessions that belong to this student's year and section
            all_sessions = conn.execute("""
                SELECT id, subject, start_time, room_number 
                FROM sessions 
                WHERE year = ? AND sections LIKE ? AND status = 'COMPLETED'
                ORDER BY start_time DESC
            """, (student['year'], section_query)).fetchall()

            # Check if they were marked present in those sessions
            for sess in all_sessions:
                att = conn.execute("SELECT status FROM attendance WHERE session_id = ? AND student_label = ?", (sess['id'], student['label'])).fetchone()
                status = att['status'] if att else "Absent"
                records.append({
                    'subject': sess['subject'],
                    'date': sess['start_time'],
                    'room': sess['room_number'],
                    'status': status
                })
        else:
            flash("Student not found. Please ensure the Roll Number is correct.")

        conn.close()

    return render_template('student_history.html', student=student_data, records=records, theme=session.get('theme', 'light'))

@app.route('/history', methods=['GET', 'POST'])
def history():
    if 'faculty_id' not in session: return redirect('/')
    conn = get_db_connection()
    selected_date = datetime.now().strftime("%Y-%m-%d")
    if request.method == 'POST': selected_date = request.form.get('query_date')

    query = """
        SELECT id, year, sections, subject, room_number, period, start_time, end_time, status,
        (SELECT COUNT(*) FROM attendance WHERE session_id = sessions.id AND status = 'Present') as present_count
        FROM sessions 
        WHERE faculty_id = ? AND date(start_time) = ?
        ORDER BY start_time DESC
    """
    sessions_data = conn.execute(query, (session['faculty_id'], selected_date)).fetchall()
    conn.close()
    return render_template('history.html', sessions=sessions_data, selected_date=selected_date, theme=session.get('theme', 'light'))

@app.route('/history/session/<int:session_id>')
def view_past_session(session_id):
    if 'faculty_id' not in session: return redirect('/')
    conn = get_db_connection()
    sess = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    year = sess['year']
    sections = sess['sections'].split(', ')
    placeholders = ', '.join(['?'] * len(sections))
    
    students = conn.execute(f"SELECT name, label, roll FROM students WHERE year = ? AND section IN ({placeholders}) ORDER BY roll ASC", [year] + sections).fetchall()
    attendance_records = conn.execute("SELECT student_label, status FROM attendance WHERE session_id = ?", (session_id,)).fetchall()
    
    status_map = {row['student_label']: row['status'] for row in attendance_records}
    final_list = [{'name': s['name'], 'roll': s['roll'], 'status': status_map.get(s['label'], 'Absent')} for s in students]
        
    conn.close()
    return render_template('view_past_session.html', sess=sess, students=final_list, theme=session.get('theme', 'light'))

@app.route('/toggle_theme')
def toggle_theme():
    if 'theme' in session: session['theme'] = 'dark' if session['theme'] == 'light' else 'light'
    return redirect(request.referrer or '/')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'faculty_id' not in session: return redirect('/')
    if request.method == 'POST':
        year = request.form.get('year')
        sections_str = ", ".join(request.form.getlist('section')) 
        subject = request.form.get('subject')
        room = request.form.get('room')
        block = request.form.get('block')
        period = request.form.get('period')
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (faculty_id, year, sections, subject, period, room_number, block, start_time, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ONGOING')", 
                       (session['faculty_id'], year, sections_str, subject, period, room, block, start_time))
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()

        session['current_session_id'] = session_id
        session['class_details'] = f"Year {year}, Sec {sections_str} | Room {room}"
        session['active_year'] = year
        session['active_sections'] = request.form.getlist('section')
        
        active_threads[session_id] = True
        threading.Thread(target=background_scanner, args=(session_id,), daemon=True).start()
        return redirect('/active_session')

    return render_template('dashboard.html', faculty_name=session['faculty_name'], theme=session.get('theme', 'light'))

@app.route('/active_session')
def active_session():
    if 'current_session_id' not in session: return redirect('/dashboard')
    return render_template('active_session.html', details=session.get('class_details', 'Unknown Class'), theme=session.get('theme', 'light'))

@app.route('/stop_session', methods=['POST'])
def stop_session():
    session_id = session.get('current_session_id')
    if session_id in active_threads: active_threads[session_id] = False 
    time.sleep(1.5)
        
    conn = get_db_connection()
    year = session.get('active_year')
    sections = session.get('active_sections', [])
    placeholders = ', '.join(['?'] * len(sections))
    all_students = conn.execute(f"SELECT name, label, roll FROM students WHERE year = ? AND section IN ({placeholders}) ORDER BY roll ASC", [year] + sections).fetchall()
    present_records = conn.execute("SELECT student_label, last_seen FROM attendance WHERE session_id = ? AND status = 'Present'", (session_id,)).fetchall()
    present_labels = {row['student_label']: row['last_seen'] for row in present_records}
    
    attendance_data = [{'label': s['label'], 'name': s['name'], 'roll': s['roll'], 'status': "Present" if s['label'] in present_labels else "Absent", 'last_seen': present_labels.get(s['label'], "N/A")} for s in all_students]
    conn.close()
    return render_template('verify_session.html', attendance_data=attendance_data, theme=session.get('theme', 'light'))

@app.route('/finalize_session', methods=['POST'])
def finalize_session():
    session_id = session.get('current_session_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    final_present = request.form.getlist('present_students')
    cursor.execute("UPDATE attendance SET status = 'Absent' WHERE session_id = ?", (session_id,))
    
    for label in final_present:
        existing = cursor.execute("SELECT id FROM attendance WHERE session_id = ? AND student_label = ?", (session_id, label)).fetchone()
        if existing: cursor.execute("UPDATE attendance SET status = 'Present' WHERE id = ?", (existing['id'],))
        else: cursor.execute("INSERT INTO attendance (session_id, student_label, status, last_seen) VALUES (?, ?, 'Present', 'Manual Override')", (session_id, label))
            
    cursor.execute("UPDATE sessions SET status = 'COMPLETED', end_time = ? WHERE id = ?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), session_id))
    conn.commit()
    conn.close()
    session.pop('current_session_id', None)
    return redirect('/dashboard')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)