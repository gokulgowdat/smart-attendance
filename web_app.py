from flask import Flask, render_template, request, redirect, session, flash, jsonify
import sqlite3
from datetime import datetime
import cv2
import os
import base64
import numpy as np
import re # <-- REQUIRED FOR FIXING THE YOLO LABELS
from werkzeug.utils import secure_filename
from face_engine_v2 import FaceEngineV2
import glob  # 

# Static folder mapping so Profile photos load correctly
app = Flask(__name__, static_url_path='/static', static_folder='.')
app.secret_key = "smart_attendance_super_secret"

# --- CONFIGURATION ---
FACES_DIR = "known_faces/faculty"
os.makedirs(FACES_DIR, exist_ok=True)

# 🚀 GLOBAL AI ENGINE INITIALIZATION
print("[System] Loading YOLOv8 Face Engine into memory...")
engine = FaceEngineV2()
print("[System] Engine Online. Awaiting Sensor Node connections.")

def get_db_connection():
    conn = sqlite3.connect('attendance_v2.db')
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================
# 📱 IOT SENSOR NODE ROUTES (WebRTC Architecture)
# ==========================================

@app.route('/sensor')
def sensor_node():
    return render_template('sensor.html')

@app.route('/process_sensor_frame', methods=['POST'])
def process_sensor_frame():
    try:
        data = request.json['image']
        header, encoded = data.split(",", 1)
        decoded = base64.b64decode(encoded)
        np_arr = np.frombuffer(decoded, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Fix the BGR to RGB color inversion
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # --- NEW: CLAHE Auto-Lighting Enhancement ---
        # Convert to LAB color space to isolate the lightness channel
        lab = cv2.cvtColor(frame, cv2.COLOR_RGB2LAB)
        l_channel, a, b = cv2.split(lab)
        
        # Apply CLAHE to dramatically improve contrast in shadows without blowing out bright spots
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl = clahe.apply(l_channel)
        
        # Merge back and convert to RGB
        limg = cv2.merge((cl,a,b))
        frame_enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
        # --------------------------------------------

        # Use the ENHANCED frame for processing, not the original dark one
        processed_frame, recognized_labels = engine.process_frame(frame_enhanced)
        
        # Auto-Rotation Fallback if phone is sideways (using enhanced frame)
        if not recognized_labels:
            rotated_frame_cw = cv2.rotate(frame_enhanced, cv2.ROTATE_90_CLOCKWISE)
            processed_frame, recognized_labels = engine.process_frame(rotated_frame_cw)
            if not recognized_labels:
                rotated_frame_ccw = cv2.rotate(frame_enhanced, cv2.ROTATE_90_COUNTERCLOCKWISE)
                processed_frame, recognized_labels = engine.process_frame(rotated_frame_ccw)

        print(f"[Sensor Node] YOLOv8 Detected: {recognized_labels}")

        conn = get_db_connection()
        active_session = conn.execute("SELECT id FROM sessions WHERE status = 'ONGOING' ORDER BY id DESC LIMIT 1").fetchone()
        
        if active_session and recognized_labels:
            session_id = active_session['id']
            cursor = conn.cursor()
            current_time = datetime.now().strftime("%H:%M:%S")
            
            for label in recognized_labels:
                # FIX: Strip the _1, _2 from the YOLO label so it matches the DB perfectly!
                clean_label = str(label).strip()
                clean_label = re.sub(r'_\d+$', '', clean_label) 
                
                if clean_label.lower() == 'unknown':
                    continue

                existing = cursor.execute("SELECT id FROM attendance WHERE session_id = ? AND LOWER(student_label) = ?", (session_id, clean_label.lower())).fetchone()
                if existing:
                    cursor.execute("UPDATE attendance SET last_seen = ?, status = 'Present' WHERE id = ?", (current_time, existing['id']))
                else:
                    cursor.execute("INSERT INTO attendance (session_id, student_label, status, last_seen) VALUES (?, ?, 'Present', ?)", (session_id, clean_label, current_time))
            conn.commit()
        conn.close()

        _, buffer = cv2.imencode('.jpg', processed_frame)
        result_b64 = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            "status": "success", 
            "recognized": recognized_labels,
            "result_image": result_b64 
        })
        
    except Exception as e:
        print(f"[Sensor Error]: {e}")
        return jsonify({"error": str(e)}), 400

# ==========================================
# 🎓 CORE FACULTY ROUTES 
# ==========================================

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
            # Fetch subjects to build the dynamic dropdown!
            session['faculty_subjects'] = prof['subjects'] if 'subjects' in prof.keys() and prof['subjects'] else ""
            
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
        name = request.form.get('name').strip()
        username = request.form.get('username').strip().lower()
        password = request.form.get('password')
        roll = request.form.get('roll', '').strip()
        department = request.form.get('department', '').strip()
        subjects = request.form.get('subjects', '').strip()
        
        # Accept MULTIPLE photos
        photos = request.files.getlist('photos')

        if not photos or photos[0].filename == '':
            flash('At least one ID Photo is required!')
            return redirect('/register')

        try:
            conn = get_db_connection()
            existing = conn.execute("SELECT id FROM faculty WHERE username = ?", (username,)).fetchone()
            if existing:
                flash('Username already exists!')
                conn.close()
                return redirect('/register')
                
            conn.execute(
                "INSERT INTO faculty (name, username, password, roll, department, subjects) VALUES (?, ?, ?, ?, ?, ?)", 
                (name, username, password, roll, department, subjects)
            )
            conn.commit()
            conn.close()

            # Create individual folder for multiple selfies
            dest_dir = os.path.join(FACES_DIR, username)
            os.makedirs(dest_dir, exist_ok=True)

            saved_count = 0
            for i, photo in enumerate(photos):
                if photo and photo.filename:
                    ext = os.path.splitext(photo.filename)[1]
                    filename = secure_filename(f"{username}_{i+1}{ext}")
                    photo.save(os.path.join(dest_dir, filename))
                    saved_count += 1

            flash(f'Account created! AI trained with {saved_count} photos. You may now log in.')
            return redirect('/')
            
        except Exception as e:
            print(f"Registration Error: {e}")
            flash('An error occurred during registration. Please check the logs.')
            return redirect('/register')
            
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
        
        # --- NEW: Handle Profile Image Upload / Update ---
        new_img = request.files.get('profile_img')
        if new_img and new_img.filename:
            ext = os.path.splitext(new_img.filename)[1]
            dest_dir = os.path.join(FACES_DIR, new_username)
            os.makedirs(dest_dir, exist_ok=True)
            # Save and overwrite the primary photo (_1)
            save_path = os.path.join(dest_dir, f"{new_username}_1{ext}")
            new_img.save(save_path)
        
        conn.execute("UPDATE faculty SET name=?, username=?, password=?, subjects=? WHERE id=?", 
                     (new_name, new_username, new_password, new_subjects, session['faculty_id']))
        conn.commit()
        session['faculty_name'] = new_name
        session['faculty_subjects'] = new_subjects
        flash("Profile updated successfully!")

    prof = conn.execute('SELECT * FROM faculty WHERE id = ?', (session['faculty_id'],)).fetchone()
    
    # --- NEW: Dynamically fetch the profile picture from the folder ---
    username = prof['username']
    search_path = os.path.join(FACES_DIR, username, f"{username}_1.*")
    found_images = glob.glob(search_path)
    
    # Format path so the browser can read it through Flask's static folder routing
    profile_img = f"/static/{FACES_DIR}/{username}/{os.path.basename(found_images[0])}" if found_images else None

    conn.close()
    return render_template('profile.html', prof=prof, profile_img=profile_img, theme=session.get('theme', 'light'))

@app.route('/student_history', methods=['GET', 'POST'])
def student_history():
    if 'faculty_id' not in session: return redirect('/')
    student_data = None
    records = []
    if request.method == 'POST':
        search_query = request.form.get('search_query').strip()
        conn = get_db_connection()
        student = conn.execute("SELECT * FROM students WHERE roll = ?", (search_query,)).fetchone()
        if student:
            student_data = student
            section_query = f"%{student['section']}%"
            all_sessions = conn.execute("""
                SELECT id, subject, start_time, room_number 
                FROM sessions 
                WHERE year = ? AND sections LIKE ? AND status = 'COMPLETED'
                ORDER BY start_time DESC
            """, (student['year'], section_query)).fetchall()
            for sess in all_sessions:
                att = conn.execute("SELECT status FROM attendance WHERE session_id = ? AND LOWER(student_label) = ?", (sess['id'], str(student['label']).strip().lower())).fetchone()
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
    raw_sessions = conn.execute(query, (session['faculty_id'], selected_date)).fetchall()
    
    # Calculate Total Students and Absent Students
    sessions_data = []
    for sess in raw_sessions:
        sess_dict = dict(sess)
        year = sess_dict['year']
        sections = [s.strip() for s in sess_dict['sections'].split(',') if s.strip()]
        
        if sections:
            placeholders = ', '.join(['?'] * len(sections))
            total_query = f"SELECT COUNT(*) FROM students WHERE year = ? AND section IN ({placeholders})"
            total_students = conn.execute(total_query, [year] + sections).fetchone()[0]
        else:
            total_students = 0
            
        sess_dict['total_students'] = total_students
        sess_dict['absent_count'] = total_students - sess_dict['present_count']
        sessions_data.append(sess_dict)

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
    
    status_map = {str(row['student_label']).strip().lower(): row['status'] for row in attendance_records}
    final_list = [{'name': s['name'], 'roll': s['roll'], 'status': status_map.get(str(s['label']).strip().lower(), 'Absent')} for s in students]
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
        session['class_details'] = f"{subject} | Sec {sections_str} | Room {room}"
        session['active_year'] = year
        session['active_sections'] = request.form.getlist('section')
        
        return redirect('/active_session')

    # Parse the subjects string into a list to pass to the HTML dropdown
    my_subjects = []
    if session.get('faculty_subjects'):
        my_subjects = [sub.strip() for sub in session['faculty_subjects'].split(',')]

    return render_template('dashboard.html', 
                           faculty_name=session['faculty_name'], 
                           my_subjects=my_subjects, 
                           theme=session.get('theme', 'light'))

@app.route('/active_session')
def active_session():
    if 'current_session_id' not in session: return redirect('/dashboard')
    return render_template('active_session.html', details=session.get('class_details', 'Unknown Class'), theme=session.get('theme', 'light'))

@app.route('/stop_session', methods=['POST'])
def stop_session():
    session_id = session.get('current_session_id')
    conn = get_db_connection()
    year = session.get('active_year')
    sections = session.get('active_sections', [])
    placeholders = ', '.join(['?'] * len(sections))
    all_students = conn.execute(f"SELECT name, label, roll FROM students WHERE year = ? AND section IN ({placeholders}) ORDER BY roll ASC", [year] + sections).fetchall()
    
    present_records = conn.execute("SELECT student_label, last_seen FROM attendance WHERE session_id = ? AND status = 'Present'", (session_id,)).fetchall()
    
    present_labels = {str(row['student_label']).strip().lower(): row['last_seen'] for row in present_records}
    
    attendance_data = []
    for s in all_students:
        clean_label = str(s['label']).strip().lower()
        is_present = clean_label in present_labels
        attendance_data.append({
            'label': s['label'],  
            'name': s['name'],
            'roll': s['roll'],
            'status': "Present" if is_present else "Absent",
            'last_seen': present_labels.get(clean_label, "N/A")
        })

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
        clean_label = str(label).strip()
        existing = cursor.execute("SELECT id FROM attendance WHERE session_id = ? AND LOWER(student_label) = ?", (session_id, clean_label.lower())).fetchone()
        if existing: 
            cursor.execute("UPDATE attendance SET status = 'Present' WHERE id = ?", (existing['id'],))
        else: 
            cursor.execute("INSERT INTO attendance (session_id, student_label, status, last_seen) VALUES (?, ?, 'Present', 'Manual Override')", (session_id, clean_label))
            
    cursor.execute("UPDATE sessions SET status = 'COMPLETED', end_time = ? WHERE id = ?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), session_id))
    conn.commit()
    conn.close()
    session.pop('current_session_id', None)
    return redirect('/dashboard')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)