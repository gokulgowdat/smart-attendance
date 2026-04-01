import os
import shutil
import sqlite3
import cv2
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime

# --- CONFIGURATION ---
DB_PATH = 'attendance_v2.db'
KNOWN_FACES_DIR = 'known_faces'

DEPARTMENTS = [
    "Computer Science & Engineering",
    "Artificial Intelligence & ML",
    "Information Science",
    "Electronics & Communication",
    "Electrical & Electronics",
    "Mechanical Engineering",
    "Civil Engineering",
    "Basic Sciences",
    "Mathematics",
    "Humanities & Social Sciences",
    "Business Administration"
]

# --- NEW: Master List of Subjects ---
PREDEFINED_SUBJECTS = [
    "Engineering Mathematics I", "Engineering Mathematics II", "Engineering Physics", "Engineering Chemistry",
    "Soft Skills & Communication", "Constitution of India", "Environmental Studies",
    "Data Structures & Algorithms", "Operating Systems", "Database Management Systems",
    "Artificial Intelligence", "Machine Learning", "Computer Networks", "Software Engineering",
    "Basic Electrical Engineering", "Digital Logic Design", "Thermodynamics", "Strength of Materials"
]

def sanitize_for_label(name: str) -> str:
    s = "".join(ch for ch in name.strip() if ch.isalnum() or ch == " ")
    s = "_".join(part for part in s.split() if part)
    return s.lower() if s else "person"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _ensure_db_schema():
    """Silently updates the database to add new Faculty columns if they don't exist yet."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(faculty)")
        cols = [row['name'] for row in cursor.fetchall()]
        
        if 'roll' not in cols: cursor.execute("ALTER TABLE faculty ADD COLUMN roll TEXT DEFAULT ''")
        if 'department' not in cols: cursor.execute("ALTER TABLE faculty ADD COLUMN department TEXT DEFAULT ''")
        if 'subjects' not in cols: cursor.execute("ALTER TABLE faculty ADD COLUMN subjects TEXT DEFAULT ''")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Schema Check Error (Safe to ignore if DB is empty): {e}")

class AdmissionAppV2:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Attendance V2 — Central Admission Desk")
        self.root.geometry("1300x750") 
        self.root.configure(bg="#f5f6fa") 
        
        _ensure_db_schema() # Upgrade DB seamlessly
        
        # Apply Light Theme Styling
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(".", background="#f5f6fa", foreground="#2f3640", font=("Segoe UI", 10))
        style.configure("TLabel", background="#f5f6fa", foreground="#2f3640")
        style.configure("TButton", background="#dcdde1", foreground="#2f3640", padding=5, borderwidth=1)
        style.map("TButton", background=[("active", "#c23616")], foreground=[("active", "white")])
        style.configure("TLabelframe", background="#f5f6fa", borderwidth=1, bordercolor="#dcdde1")
        style.configure("TLabelframe.Label", background="#f5f6fa", foreground="#0097e6", font=("Segoe UI", 10, "bold"))
        style.configure("TEntry", fieldbackground="#ffffff", foreground="#2f3640", borderwidth=1)
        style.configure("TCombobox", fieldbackground="#ffffff", foreground="#2f3640")
        style.configure("Treeview", background="#ffffff", foreground="#2f3640", fieldbackground="#ffffff", borderwidth=1)
        style.configure("Treeview.Heading", background="#e1b12c", foreground="white", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#0097e6")], foreground=[("selected", "white")])

        self.selected_image_paths = []
        self._build_ui()
        self._refresh_trees() 
        self._log("Admission V2 Initialized. Edit & Promote capabilities online.")

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)

    def _build_ui(self):
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill="both", expand=True, padx=15, pady=15)

        # ==========================================
        # LEFT PANEL: REGISTRATION & CAPTURE
        # ==========================================
        left_frame = tk.Frame(main_paned, bg="#f5f6fa", width=480)
        main_paned.add(left_frame, weight=1)

        form_frame = ttk.LabelFrame(left_frame, text=" REGISTRATION FORM ")
        form_frame.pack(fill="x", pady=(0, 15), ipady=5)

        # Row 0
        ttk.Label(form_frame, text="Full Name:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(form_frame, textvariable=self.name_var, width=22)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(form_frame, text="Role:").grid(row=0, column=2, padx=10, pady=10, sticky="e")
        self.role_var = tk.StringVar(value="student")
        self.role_combo = ttk.Combobox(form_frame, textvariable=self.role_var, values=["student", "faculty"], state="readonly", width=12)
        self.role_combo.grid(row=0, column=3, padx=10, pady=10, sticky="w")
        self.role_combo.bind("<<ComboboxSelected>>", self._on_role_change)

        # Row 1 (Student Specific)
        ttk.Label(form_frame, text="Year:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.year_var = tk.StringVar()
        self.year_combo = ttk.Combobox(form_frame, textvariable=self.year_var, values=["First Year", "Second Year", "Third Year", "Final Year"], state="readonly", width=20)
        self.year_combo.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(form_frame, text="Section:").grid(row=1, column=2, padx=10, pady=10, sticky="e")
        self.section_var = tk.StringVar()
        self.section_combo = ttk.Combobox(form_frame, textvariable=self.section_var, values=["A", "B", "C", "D", "E", "F"], state="readonly", width=12)
        self.section_combo.grid(row=1, column=3, padx=10, pady=10, sticky="w")

        # Row 2 (Shared Roll + Faculty Dept)
        ttk.Label(form_frame, text="Roll / Emp ID:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.roll_var = tk.StringVar()
        self.roll_entry = ttk.Entry(form_frame, textvariable=self.roll_var, width=22)
        self.roll_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(form_frame, text="Department:").grid(row=2, column=2, padx=10, pady=10, sticky="e")
        self.dept_var = tk.StringVar()
        self.dept_combo = ttk.Combobox(form_frame, textvariable=self.dept_var, values=DEPARTMENTS, state="disabled", width=12)
        self.dept_combo.grid(row=2, column=3, padx=10, pady=10, sticky="w")

        # --- UPDATED: Row 3 (Faculty Subjects + Label) ---
        ttk.Label(form_frame, text="Subjects:").grid(row=3, column=0, padx=10, pady=10, sticky="e")
        self.subs_var = tk.StringVar()
        
        sub_frame = tk.Frame(form_frame, bg="#f5f6fa")
        sub_frame.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        
        self.subs_entry = ttk.Entry(sub_frame, textvariable=self.subs_var, width=16, state="disabled")
        self.subs_entry.pack(side="left")
        self.subs_btn = ttk.Button(sub_frame, text="➕", width=3, state="disabled", command=lambda: self._open_subject_selector(self.subs_var))
        self.subs_btn.pack(side="left", padx=(5,0))
        
        ttk.Label(form_frame, text="System Label:").grid(row=3, column=2, padx=10, pady=10, sticky="e")
        self.label_var = tk.StringVar(value="(auto-generated)")
        ttk.Label(form_frame, textvariable=self.label_var, font=("Consolas", 10, "italic"), foreground="#44bd32").grid(row=3, column=3, sticky="w")

        # --- PHOTO CAPTURE FRAME ---
        photo_frame = ttk.LabelFrame(left_frame, text=" BIOMETRIC DATA (MULTIPLE PHOTOS) ")
        photo_frame.pack(fill="x", pady=(0, 15), ipady=5)

        self.photo_path_label = ttk.Label(photo_frame, text="0 photos selected.", foreground="#718093")
        self.photo_path_label.pack(side="top", pady=(5,0))

        btn_frame = tk.Frame(photo_frame, bg="#f5f6fa")
        btn_frame.pack(side="top", pady=10)

        ttk.Button(btn_frame, text="📁 Browse Photos", command=self._browse_photo, width=18).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="📷 Launch Webcam", command=self._capture_webcam, width=18).pack(side="left", padx=10)

        # --- ACTIONS ---
        action_frame = tk.Frame(left_frame, bg="#f5f6fa")
        action_frame.pack(fill="x", pady=(0, 15))

        ttk.Button(action_frame, text="✔ ENROLL & SAVE", command=self._save_record, width=20).pack(side="left", padx=5)
        ttk.Button(action_frame, text="✖ Clear Form", command=self._clear_form, width=15).pack(side="left", padx=5)

        # --- LOG TERMINAL ---
        log_frame = ttk.LabelFrame(left_frame, text=" SYSTEM LOG ")
        log_frame.pack(fill="both", expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, font=("Consolas", 9), bg="#ffffff", fg="#2f3640", borderwidth=1)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.name_entry.bind("<KeyRelease>", lambda e: self._update_label_preview())
        self.roll_entry.bind("<KeyRelease>", lambda e: self._update_label_preview())

        # ==========================================
        # RIGHT PANEL: DATABASE MANAGER
        # ==========================================
        right_frame = tk.Frame(main_paned, bg="#f5f6fa")
        main_paned.add(right_frame, weight=2)

        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill="both", expand=True)

        # --- Student Tab ---
        stu_frame = ttk.Frame(notebook)
        notebook.add(stu_frame, text=" Manage Students ")
        
        stu_cols = ("ID", "Roll", "Name", "Year", "Section", "Label")
        self.stu_tree = ttk.Treeview(stu_frame, columns=stu_cols, show="headings", height=20)
        for col in stu_cols: self.stu_tree.heading(col, text=col)
        self.stu_tree.column("ID", width=40); self.stu_tree.column("Roll", width=100); self.stu_tree.column("Section", width=60)
        self.stu_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        stu_action_frame = tk.Frame(stu_frame, bg="#f5f6fa")
        stu_action_frame.pack(pady=10)
        ttk.Button(stu_action_frame, text="✏ Edit Selected Student", command=self._edit_student).pack(side="left", padx=10)
        ttk.Button(stu_action_frame, text="🗑 Delete Selected Student", command=self._delete_student).pack(side="left", padx=10)

        # --- Faculty Tab ---
        fac_frame = ttk.Frame(notebook)
        notebook.add(fac_frame, text=" Manage Faculty ")

        fac_cols = ("ID", "Emp ID", "Name", "Department", "Subjects", "Username")
        self.fac_tree = ttk.Treeview(fac_frame, columns=fac_cols, show="headings", height=20)
        for col in fac_cols: self.fac_tree.heading(col, text=col)
        self.fac_tree.column("ID", width=40); self.fac_tree.column("Emp ID", width=80); self.fac_tree.column("Username", width=100)
        self.fac_tree.pack(fill="both", expand=True, padx=10, pady=10)

        fac_action_frame = tk.Frame(fac_frame, bg="#f5f6fa")
        fac_action_frame.pack(pady=10)
        ttk.Button(fac_action_frame, text="✏ Edit Selected Faculty", command=self._edit_faculty).pack(side="left", padx=10)
        ttk.Button(fac_action_frame, text="🗑 Delete Selected Faculty", command=self._delete_faculty).pack(side="left", padx=10)

    # ==========================================
    # CORE LOGIC FUNCTIONS
    # ==========================================

    # --- NEW: Subject Selector Popup ---
    def _open_subject_selector(self, target_var):
        top = tk.Toplevel(self.root)
        top.title("Select Subjects")
        top.geometry("350x400")
        top.configure(bg="#f5f6fa")
        
        ttk.Label(top, text="Select subjects taught by this faculty:", font=("Segoe UI", 10, "bold")).pack(pady=10)
        
        # Scrollable Frame for Checkboxes
        canvas = tk.Canvas(top, bg="#ffffff")
        scrollbar = ttk.Scrollbar(top, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#ffffff")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="top", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")

        # Create Checkboxes
        check_vars = {}
        current_selection = target_var.get().split(", ") if target_var.get() else []
        
        for sub in PREDEFINED_SUBJECTS:
            var = tk.BooleanVar(value=(sub in current_selection))
            check_vars[sub] = var
            tk.Checkbutton(scrollable_frame, text=sub, variable=var, bg="#ffffff").pack(anchor="w", padx=10, pady=2)

        def save_selection():
            selected = [sub for sub, var in check_vars.items() if var.get()]
            target_var.set(", ".join(selected))
            top.destroy()

        ttk.Button(top, text="💾 Confirm Subjects", command=save_selection).pack(pady=10)

    def _refresh_trees(self):
        for item in self.stu_tree.get_children(): self.stu_tree.delete(item)
        for item in self.fac_tree.get_children(): self.fac_tree.delete(item)

        try:
            conn = get_db_connection()
            for row in conn.execute("SELECT * FROM students"):
                self.stu_tree.insert("", "end", values=(row['id'], row['roll'], row['name'], row['year'], row['section'], row['label']))
            for row in conn.execute("SELECT id, roll, name, department, subjects, username FROM faculty"):
                self.fac_tree.insert("", "end", values=(row['id'], row['roll'], row['name'], row['department'], row['subjects'], row['username']))
            conn.close()
        except sqlite3.OperationalError:
            self._log("Notice: Database empty or not initialized yet.")

    def _on_role_change(self, event=None):
        role = self.role_var.get().strip().lower()
        if role == "faculty":
            self.year_combo.set(""); self.section_combo.set("")
            self.year_combo.config(state="disabled"); self.section_combo.config(state="disabled")
            self.dept_combo.config(state="readonly"); self.subs_btn.config(state="normal")
        else:
            self.dept_combo.set(""); self.subs_var.set("")
            self.year_combo.config(state="readonly"); self.section_combo.config(state="readonly")
            self.dept_combo.config(state="disabled"); self.subs_btn.config(state="disabled")
        self._update_label_preview()

    def _update_label_preview(self):
        name = self.name_var.get().strip()
        role = self.role_var.get().strip().lower()
        roll = self.roll_var.get().strip()
        
        safe_name = sanitize_for_label(name)
        if not name:
            self.label_var.set("(auto-generated)")
        elif role == "student" and roll:
            self.label_var.set(f"{roll}_{safe_name}")
        else:
            self.label_var.set(safe_name)

    def _browse_photo(self):
        paths = filedialog.askopenfilenames(title="Select face photo(s)", filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if paths:
            self.selected_image_paths.extend(paths)
            self.photo_path_label.config(text=f"{len(self.selected_image_paths)} photos queued.", foreground="#2f3640")
            self._log(f"Queued {len(paths)} local images.")

    def _capture_webcam(self):
        self._log("Starting Webcam. Press SPACE to snap a photo, ESC to finish.")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Camera Error", "Could not access the webcam.")
            return

        temp_dir = "temp_captures"
        os.makedirs(temp_dir, exist_ok=True)
        count = 0

        while True:
            ret, frame = cap.read()
            if not ret: break
            
            display_frame = frame.copy()
            cv2.putText(display_frame, "Press SPACE to Snap | ESC to Close", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Photos Taken: {count}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.imshow("Webcam Enrollment", display_frame)
            
            k = cv2.waitKey(1)
            if k % 256 == 27: break # ESC
            elif k % 256 == 32: # SPACE
                filepath = os.path.join(temp_dir, f"capture_{datetime.now().strftime('%H%M%S%f')}.jpg")
                cv2.imwrite(filepath, frame)
                self.selected_image_paths.append(filepath)
                count += 1
                self._log(f"Snapped photo {count}!")

        cap.release()
        cv2.destroyAllWindows()
        self.photo_path_label.config(text=f"{len(self.selected_image_paths)} photos queued.", foreground="#2f3640")

    def _save_record(self):
        name = self.name_var.get().strip()
        role = self.role_var.get().strip().lower()
        roll = self.roll_var.get().strip()
        label = self.label_var.get()

        if not name or not self.selected_image_paths:
            messagebox.showwarning("Incomplete", "Name and at least one Photo are required.")
            return

        role_dir = "students" if role == "student" else "faculty"
        dest_dir = os.path.join(KNOWN_FACES_DIR, role_dir, label)
        os.makedirs(dest_dir, exist_ok=True)

        saved_count = 0
        for i, src in enumerate(self.selected_image_paths):
            ext = os.path.splitext(src)[1]
            dest_path = os.path.join(dest_dir, f"{label}_{i+1}{ext}")
            try:
                shutil.copyfile(src, dest_path)
                saved_count += 1
            except Exception as e:
                self._log(f"Error saving image: {e}")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if role == "student":
                year = self.year_var.get().strip()
                section = self.section_var.get().strip()
                if not year or not section or not roll:
                    messagebox.showwarning("Incomplete", "Students require Year, Section, and Roll Number.")
                    return
                    
                cursor.execute("SELECT id FROM students WHERE label = ?", (label,))
                if cursor.fetchone():
                    cursor.execute("UPDATE students SET name=?, roll=?, year=?, section=? WHERE label=?", (name, roll, year, section, label))
                else:
                    cursor.execute("INSERT INTO students (name, label, roll, year, section) VALUES (?, ?, ?, ?, ?)", (name, label, roll, year, section))
            else:
                dept = self.dept_var.get().strip()
                subs = self.subs_var.get().strip()
                cursor.execute("SELECT id FROM faculty WHERE username = ?", (label,))
                if cursor.fetchone():
                    cursor.execute("UPDATE faculty SET name=?, roll=?, department=?, subjects=? WHERE username=?", (name, roll, dept, subs, label))
                else:
                    cursor.execute("INSERT INTO faculty (name, username, password, roll, department, subjects) VALUES (?, ?, ?, ?, ?, ?)", (name, label, "1234", roll, dept, subs))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"{name} enrolled successfully with {saved_count} photos!")
            self._clear_form()
            self._refresh_trees() 
            
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def _clear_form(self):
        self.name_var.set(""); self.roll_var.set(""); self.year_var.set(""); self.section_var.set("")
        self.dept_var.set(""); self.subs_var.set(""); self.label_var.set("(auto-generated)")
        self.selected_image_paths.clear()
        self.photo_path_label.config(text="0 photos selected.", foreground="#718093")

    # ==========================================
    # EDIT AND DELETE FUNCTIONS
    # ==========================================
    
    def _edit_student(self):
        sel = self.stu_tree.selection()
        if not sel: 
            messagebox.showwarning("Select", "Please select a student to edit.")
            return
        vals = self.stu_tree.item(sel[0])["values"]
        stu_id, current_roll, current_name, current_year, current_sec, label = vals

        edit_win = tk.Toplevel(self.root)
        edit_win.title(f"Edit Student: {current_name}")
        edit_win.geometry("400x350")
        edit_win.configure(bg="#f5f6fa")

        ttk.Label(edit_win, text="Name:").pack(pady=(15,2))
        name_ent = ttk.Entry(edit_win, width=30); name_ent.insert(0, current_name); name_ent.pack()
        
        ttk.Label(edit_win, text="Roll Number:").pack(pady=(10,2))
        roll_ent = ttk.Entry(edit_win, width=30); roll_ent.insert(0, current_roll); roll_ent.pack()

        ttk.Label(edit_win, text="Year (Promote):").pack(pady=(10,2))
        year_cb = ttk.Combobox(edit_win, values=["First Year", "Second Year", "Third Year", "Final Year"], state="readonly")
        year_cb.set(current_year); year_cb.pack()

        ttk.Label(edit_win, text="Section:").pack(pady=(10,2))
        sec_cb = ttk.Combobox(edit_win, values=["A", "B", "C", "D", "E", "F"], state="readonly")
        sec_cb.set(current_sec); sec_cb.pack()

        def save_edits():
            conn = get_db_connection()
            conn.execute("UPDATE students SET name=?, roll=?, year=?, section=? WHERE id=?", 
                         (name_ent.get(), roll_ent.get(), year_cb.get(), sec_cb.get(), stu_id))
            conn.commit()
            conn.close()
            self._refresh_trees()
            self._log(f"Updated Student ID {stu_id} details.")
            edit_win.destroy()

        ttk.Button(edit_win, text="💾 Save Changes", command=save_edits).pack(pady=20)

    def _edit_faculty(self):
        sel = self.fac_tree.selection()
        if not sel: 
            messagebox.showwarning("Select", "Please select a faculty member to edit.")
            return
        vals = self.fac_tree.item(sel[0])["values"]
        fac_id, current_roll, current_name, current_dept, current_subs, username = vals

        edit_win = tk.Toplevel(self.root)
        edit_win.title(f"Edit Faculty: {current_name}")
        edit_win.geometry("400x350")
        edit_win.configure(bg="#f5f6fa")

        ttk.Label(edit_win, text="Name:").pack(pady=(15,2))
        name_ent = ttk.Entry(edit_win, width=30); name_ent.insert(0, current_name); name_ent.pack()
        
        ttk.Label(edit_win, text="Employee ID:").pack(pady=(10,2))
        roll_ent = ttk.Entry(edit_win, width=30); roll_ent.insert(0, current_roll if current_roll else ""); roll_ent.pack()

        ttk.Label(edit_win, text="Department:").pack(pady=(10,2))
        dept_cb = ttk.Combobox(edit_win, values=DEPARTMENTS, state="readonly", width=28)
        dept_cb.set(current_dept if current_dept else ""); dept_cb.pack()

        # --- UPDATED: Subjects Edit with Popup ---
        ttk.Label(edit_win, text="Subjects Taught (comma separated):").pack(pady=(10,2))
        sub_var = tk.StringVar(value=current_subs if current_subs else "")
        sub_frame = tk.Frame(edit_win, bg="#f5f6fa")
        sub_frame.pack()
        ttk.Entry(sub_frame, textvariable=sub_var, width=25, state="disabled").pack(side="left")
        ttk.Button(sub_frame, text="➕", width=3, command=lambda: self._open_subject_selector(sub_var)).pack(side="left", padx=(5,0))

        def save_edits():
            conn = get_db_connection()
            conn.execute("UPDATE faculty SET name=?, roll=?, department=?, subjects=? WHERE id=?", 
                         (name_ent.get(), roll_ent.get(), dept_cb.get(), sub_var.get(), fac_id))
            conn.commit()
            conn.close()
            self._refresh_trees()
            self._log(f"Updated Faculty ID {fac_id} details.")
            edit_win.destroy()

        ttk.Button(edit_win, text="💾 Save Changes", command=save_edits).pack(pady=20)

    def _delete_student(self):
        sel = self.stu_tree.selection()
        if not sel: return
        vals = self.stu_tree.item(sel[0])["values"]
        stu_id, label = vals[0], vals[5]
        
        if messagebox.askyesno("Confirm Delete", f"Delete Student '{vals[2]}'?"):
            conn = get_db_connection()
            conn.execute("DELETE FROM attendance WHERE student_label = ?", (label,))
            conn.execute("DELETE FROM students WHERE id = ?", (stu_id,))
            conn.commit()
            conn.close()
            
            dir_path = os.path.join(KNOWN_FACES_DIR, "students", label)
            if os.path.exists(dir_path): shutil.rmtree(dir_path)
            
            self._log(f"Deleted student: {label}")
            self._refresh_trees()

    def _delete_faculty(self):
        sel = self.fac_tree.selection()
        if not sel: return
        vals = self.fac_tree.item(sel[0])["values"]
        fac_id, username = vals[0], vals[5]
        
        if messagebox.askyesno("Confirm Delete", f"Delete Faculty '{vals[2]}'?"):
            conn = get_db_connection()
            conn.execute("DELETE FROM faculty WHERE id = ?", (fac_id,))
            conn.commit()
            conn.close()

            dir_path = os.path.join(KNOWN_FACES_DIR, "faculty", username)
            if os.path.exists(dir_path): shutil.rmtree(dir_path)

            self._log(f"Deleted faculty: {username}")
            self._refresh_trees()

if __name__ == "__main__":
    root = tk.Tk()
    app = AdmissionAppV2(root)
    root.mainloop()