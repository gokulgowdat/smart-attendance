import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import sqlite3
import shutil
import os
import glob

DB_PATH = "attendance_v2.db"
FACES_DIR = "known_faces"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

class AdmissionAppV2:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Attendance - Admission Cell (V2)")
        self.root.geometry("750x650")
        self.root.configure(bg="#f3f4f6")
        
        os.makedirs(os.path.join(FACES_DIR, "students"), exist_ok=True)
        os.makedirs(os.path.join(FACES_DIR, "faculty"), exist_ok=True)
        
        self.build_ui()

    def build_ui(self):
        tk.Label(self.root, text="Administrative Admission Portal", font=("Segoe UI", 16, "bold"), bg="#f3f4f6", fg="#1f2937").pack(pady=10)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)

        # Tabs
        self.student_frame = tk.Frame(self.notebook, bg="white")
        self.faculty_frame = tk.Frame(self.notebook, bg="white")
        self.manage_frame = tk.Frame(self.notebook, bg="white")

        self.notebook.add(self.student_frame, text="  Register Student  ")
        self.notebook.add(self.faculty_frame, text="  Register Faculty  ")
        self.notebook.add(self.manage_frame, text="  Manage Database (View/Edit/Delete)  ")

        self.build_student_form(self.student_frame)
        self.build_faculty_form(self.faculty_frame)
        self.build_manage_tab(self.manage_frame)
        
        # Refresh tables when switching to Manage tab
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    # ================= REGISTRATION FORMS =================
    def build_student_form(self, frame):
        self.s_name = tk.StringVar()
        self.s_label = tk.StringVar()
        self.s_roll = tk.StringVar()
        self.s_year = tk.StringVar(value="1")
        self.s_section = tk.StringVar(value="A")
        self.s_photo_path = tk.StringVar()

        fields = [("Full Name:", self.s_name), ("Unique Label (e.g., firstname):", self.s_label), ("Roll Number:", self.s_roll)]
        for i, (label_text, var) in enumerate(fields):
            tk.Label(frame, text=label_text, bg="white", font=("Segoe UI", 10, "bold")).grid(row=i, column=0, sticky="w", padx=20, pady=10)
            tk.Entry(frame, textvariable=var, width=30).grid(row=i, column=1, padx=20, pady=10)

        tk.Label(frame, text="Year:", bg="white", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky="w", padx=20, pady=10)
        ttk.Combobox(frame, textvariable=self.s_year, values=["1", "2", "3", "4"], state="readonly", width=27).grid(row=3, column=1, padx=20, pady=10)

        tk.Label(frame, text="Section:", bg="white", font=("Segoe UI", 10, "bold")).grid(row=4, column=0, sticky="w", padx=20, pady=10)
        # Expanded to H
        ttk.Combobox(frame, textvariable=self.s_section, values=["A", "B", "C", "D", "E", "F", "G", "H"], state="readonly", width=27).grid(row=4, column=1, padx=20, pady=10)

        tk.Button(frame, text="Select ID Photo", command=lambda: self.select_photo(self.s_photo_path), bg="#e5e7eb").grid(row=5, column=0, padx=20, pady=20)
        tk.Label(frame, textvariable=self.s_photo_path, bg="white", fg="gray", wraplength=200).grid(row=5, column=1, sticky="w")

        tk.Button(frame, text="Register Student", command=self.register_student, bg="#10b981", fg="white", font=("Segoe UI", 11, "bold"), width=20).grid(row=6, column=0, columnspan=2, pady=20)

    def build_faculty_form(self, frame):
        self.f_name = tk.StringVar()
        self.f_username = tk.StringVar()
        self.f_password = tk.StringVar()
        self.f_photo_path = tk.StringVar()

        fields = [("Full Name:", self.f_name), ("Username:", self.f_username), ("Password:", self.f_password)]
        for i, (label_text, var) in enumerate(fields):
            tk.Label(frame, text=label_text, bg="white", font=("Segoe UI", 10, "bold")).grid(row=i, column=0, sticky="w", padx=20, pady=10)
            tk.Entry(frame, textvariable=var, width=30).grid(row=i, column=1, padx=20, pady=10)

        tk.Button(frame, text="Select ID Photo", command=lambda: self.select_photo(self.f_photo_path), bg="#e5e7eb").grid(row=3, column=0, padx=20, pady=20)
        tk.Label(frame, textvariable=self.f_photo_path, bg="white", fg="gray", wraplength=200).grid(row=3, column=1, sticky="w")

        tk.Button(frame, text="Register Faculty", command=self.register_faculty, bg="#3b82f6", fg="white", font=("Segoe UI", 11, "bold"), width=20).grid(row=4, column=0, columnspan=2, pady=20)

    def select_photo(self, var):
        filepath = filedialog.askopenfilename(title="Select Photo", filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if filepath: var.set(filepath)

    def register_student(self):
        name, label, roll, year, sec, photo = self.s_name.get(), self.s_label.get().lower(), self.s_roll.get(), self.s_year.get(), self.s_section.get(), self.s_photo_path.get()
        if not all([name, label, roll, photo]):
            messagebox.showerror("Error", "All fields and a photo are required!")
            return
        try:
            ext = os.path.splitext(photo)[1]
            new_photo_path = os.path.join(FACES_DIR, "students", f"{label}{ext}")
            shutil.copy(photo, new_photo_path)

            conn = get_db_connection()
            conn.execute("INSERT INTO students (name, label, roll, year, section) VALUES (?, ?, ?, ?, ?)", (name, label, roll, year, sec))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", f"Student {name} registered!")
            self.s_name.set(""); self.s_label.set(""); self.s_roll.set(""); self.s_photo_path.set("")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Label or Roll Number already exists!")

    def register_faculty(self):
        name, user, pw, photo = self.f_name.get(), self.f_username.get().lower(), self.f_password.get(), self.f_photo_path.get()
        if not all([name, user, pw, photo]):
            messagebox.showerror("Error", "All fields and a photo are required!")
            return
        try:
            ext = os.path.splitext(photo)[1]
            new_photo_path = os.path.join(FACES_DIR, "faculty", f"{user}{ext}")
            shutil.copy(photo, new_photo_path)

            conn = get_db_connection()
            conn.execute("INSERT INTO faculty (name, username, password) VALUES (?, ?, ?)", (name, user, pw))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", f"Faculty {name} registered!")
            self.f_name.set(""); self.f_username.set(""); self.f_password.set(""); self.f_photo_path.set("")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "This username is already taken!")

    # ================= MANAGE (VIEW/EDIT/DELETE) =================
    def build_manage_tab(self, frame):
        # View Selector
        top_frame = tk.Frame(frame, bg="white")
        top_frame.pack(fill="x", pady=10)
        self.view_var = tk.StringVar(value="students")
        tk.Radiobutton(top_frame, text="View Students", variable=self.view_var, value="students", command=self.load_table_data, bg="white").pack(side="left", padx=20)
        tk.Radiobutton(top_frame, text="View Faculty", variable=self.view_var, value="faculty", command=self.load_table_data, bg="white").pack(side="left")

        # Table
        columns = ("ID", "Name", "Identifier", "Extra 1", "Extra 2")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Identifier", text="Label/Username")
        self.tree.heading("Extra 1", text="Roll/Password")
        self.tree.heading("Extra 2", text="Yr & Sec / (None)")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        # Action Buttons
        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(fill="x", pady=10)
        tk.Button(btn_frame, text="Delete Selected", command=self.delete_record, bg="#ef4444", fg="white", width=15).pack(side="right", padx=20)
        tk.Button(btn_frame, text="Edit Selected (Basic)", command=self.edit_record, bg="#f59e0b", fg="white", width=20).pack(side="right")

    def on_tab_change(self, event):
        if self.notebook.index(self.notebook.select()) == 2:
            self.load_table_data()

    def load_table_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        conn = get_db_connection()
        view = self.view_var.get()
        if view == "students":
            records = conn.execute("SELECT id, name, label, roll, year, section FROM students").fetchall()
            for r in records:
                self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], f"Yr: {r[4]} Sec: {r[5]}"))
        else:
            records = conn.execute("SELECT id, name, username, password FROM faculty").fetchall()
            for r in records:
                self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], "N/A"))
        conn.close()

    def delete_record(self):
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        record_id = item['values'][0]
        identifier = item['values'][2] # Label or Username
        
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to permanently delete '{identifier}' and their photo?"):
            return

        view = self.view_var.get()
        conn = get_db_connection()
        
        # 1. Delete from DB
        if view == "students":
            conn.execute("DELETE FROM students WHERE id = ?", (record_id,))
            folder = "students"
        else:
            conn.execute("DELETE FROM faculty WHERE id = ?", (record_id,))
            folder = "faculty"
        conn.commit()
        conn.close()

        # 2. Delete the associated photo
        search_pattern = os.path.join(FACES_DIR, folder, f"{identifier}.*")
        for file in glob.glob(search_pattern):
            try:
                os.remove(file)
            except: pass

        self.load_table_data()
        messagebox.showinfo("Success", "Record and photo deleted.")

    def edit_record(self):
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected[0])
        record_id = item['values'][0]
        current_name = item['values'][1]
        
        view = self.view_var.get()
        new_name = simpledialog.askstring("Edit Record", "Enter new Full Name:", initialvalue=current_name)
        if new_name:
            conn = get_db_connection()
            if view == "students":
                conn.execute("UPDATE students SET name = ? WHERE id = ?", (new_name, record_id))
            else:
                conn.execute("UPDATE faculty SET name = ? WHERE id = ?", (new_name, record_id))
            conn.commit()
            conn.close()
            self.load_table_data()

if __name__ == "__main__":
    root = tk.Tk()
    app = AdmissionAppV2(root)
    root.mainloop()