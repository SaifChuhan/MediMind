import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime, timedelta
import threading
import joblib
import time
import winsound
import sqlite3
import hashlib
import uuid
import pandas as pd

try:
    import pandas as pd
    import joblib
    from sklearn.preprocessing import LabelEncoder  # Needed for encoders
    HAS_ML_LIBRARIES = True
except ImportError as e:
    print(f"⚠️ ML dependencies missing: {e}")
    print("Please install required ML libraries: pip install scikit-learn pandas joblib")
    HAS_ML_LIBRARIES = False
    pd = None
    joblib = None
    LabelEncoder = None

class User:
    def __init__(self, username, password_hash, role="user", approved=False, user_id=None):
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.approved = approved
        self.user_id = user_id if user_id else str(uuid.uuid4())

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Medicine Reminder - Login")
        self.root.geometry("400x350")
        self.root.configure(bg="#f0f0f0")
        
        self.current_user = None
        self.conn = sqlite3.connect('medicine_reminder.db')
        self.create_tables()
        self.setup_default_superadmin()
        self.setup_ui()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                role TEXT,
                approved BOOLEAN
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                age INTEGER,
                gender TEXT,
                medical_history TEXT,
                chronic_diseases TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medicines (
                medicine_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                name TEXT,
                dosage TEXT,
                time_str TEXT,
                disease TEXT,
                is_diabetic BOOLEAN,
                category TEXT,
                meal_timing TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        ''')
        self.conn.commit()

    def setup_default_superadmin(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'superadmin'")
        if cursor.fetchone()[0] == 0:
            default_hash = hashlib.sha256("your_secure_password_2025".encode()).hexdigest()
            cursor.execute('''
                INSERT INTO users (user_id, username, password_hash, role, approved)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), "Saifi", default_hash, "superadmin", True))
            self.conn.commit()

    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg="#f0f0f0", padx=20, pady=20)
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        title_label = tk.Label(main_frame, text="Medicine Reminder Pro", font=("Arial", 18, "bold"), bg="#f0f0f0", fg="#333")
        title_label.pack(pady=(0, 20))
        
        login_frame = tk.Frame(main_frame, bg="#f0f0f0")
        login_frame.pack(pady=10)
        
        tk.Label(login_frame, text="Username:", bg="#f0f0f0", font=("Arial", 10)).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.username_entry = tk.Entry(login_frame, font=("Arial", 10))
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(login_frame, text="Password:", bg="#f0f0f0", font=("Arial", 10)).grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.password_entry = tk.Entry(login_frame, show="*", font=("Arial", 10))
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(pady=10)
        
        login_btn = tk.Button(button_frame, text="Login", command=self.login, bg="#4CAF50", fg="white", 
                             font=("Arial", 10, "bold"), width=10)
        login_btn.pack(side=tk.LEFT, padx=5)
        
        signup_btn = tk.Button(button_frame, text="Sign Up", command=self.show_signup, bg="#2196F3", fg="white", 
                              font=("Arial", 10, "bold"), width=10)
        signup_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(main_frame, text="Request Admin Access", command=self.show_admin_request, 
                 bg="#FF9800", fg="white", font=("Arial", 9)).pack(pady=5)
        
        footer_label = tk.Label(main_frame, text="© 2023 Medicine Reminder Pro", bg="#f0f0f0", fg="#666", font=("Arial", 8))
        footer_label.pack(side=tk.BOTTOM, pady=(20, 0))

    def show_admin_request(self):
        request_window = tk.Toplevel(self.root)
        request_window.title("Admin Access Request")
        request_window.geometry("400x200")
        
        tk.Label(request_window, text="Request Admin Privileges", font=("Arial", 12)).pack(pady=10)
        
        tk.Label(request_window, text="Username:").pack()
        username_entry = tk.Entry(request_window)
        username_entry.pack()
        
        tk.Label(request_window, text="Password:").pack()
        password_entry = tk.Entry(request_window, show="*")
        password_entry.pack()
        
        reason_frame = tk.Frame(request_window)
        reason_frame.pack(pady=5)
        tk.Label(reason_frame, text="Reason for request:").pack()
        reason_entry = tk.Text(reason_frame, height=3, width=30)
        reason_entry.pack()
        
        def submit_request():
            username = username_entry.get()
            password = password_entry.get()
            reason = reason_entry.get("1.0", tk.END).strip()
            
            if not username or not password:
                messagebox.showerror("Error", "Please enter both username and password")
                return
                
            cursor = self.conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            
            if not user:
                messagebox.showerror("Error", "User not found")
                return
                
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if user[0] != password_hash:
                messagebox.showerror("Error", "Invalid password")
                return
                
            messagebox.showinfo("Submitted", 
                              "Your request has been submitted to the superadmin for approval.")
            request_window.destroy()
        
        tk.Button(request_window, text="Submit Request", command=submit_request).pack(pady=10)

    def show_signup(self):
        signup_window = tk.Toplevel(self.root)
        signup_window.title("Sign Up")
        signup_window.geometry("350x250")
        signup_window.configure(bg="#f0f0f0")
        
        form_frame = tk.Frame(signup_window, bg="#f0f0f0")
        form_frame.pack(pady=10)
        
        tk.Label(form_frame, text="Username:", bg="#f0f0f0").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        new_user_entry = tk.Entry(form_frame)
        new_user_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="Password:", bg="#f0f0f0").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        new_pass_entry = tk.Entry(form_frame, show="*")
        new_pass_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="Confirm Password:", bg="#f0f0f0").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        confirm_pass_entry = tk.Entry(form_frame, show="*")
        confirm_pass_entry.grid(row=2, column=1, padx=5, pady=5)
        
        btn_frame = tk.Frame(signup_window, bg="#f0f0f0")
        btn_frame.pack(pady=10)
        
        def create_account():
            username = new_user_entry.get()
            password = new_pass_entry.get()
            confirm_pass = confirm_pass_entry.get()
            
            if not username or not password:
                messagebox.showerror("Error", "Please enter both username and password")
                return
                
            if password != confirm_pass:
                messagebox.showerror("Error", "Passwords do not match")
                return
                
            cursor = self.conn.cursor()
            cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                messagebox.showerror("Error", "Username already exists")
                return
                
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            approved_status = True if self.current_user and self.current_user.role in ["admin", "superadmin"] else False
            
            cursor.execute('''
                INSERT INTO users (user_id, username, password_hash, role, approved)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), username, password_hash, "user", approved_status))
            self.conn.commit()
            
            messagebox.showinfo("Success", "Account created successfully!")
            signup_window.destroy()
        
        tk.Button(btn_frame, text="Create Account", command=create_account, bg="#4CAF50", fg="white").pack(pady=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id, username, password_hash, role, approved FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        
        if not user_data or user_data[2] != password_hash:
            messagebox.showerror("Error", "Invalid username or password")
            return
            
        if not user_data[4]:
            messagebox.showwarning("Pending Approval", 
                                 "Your account is pending approval by an administrator.")
            return
            
        self.current_user = User(user_data[1], user_data[2], user_data[3], user_data[4], user_data[0])
        self.root.destroy()
        self.launch_main_app()
    
    def launch_main_app(self):
        root = tk.Tk()
        app = MedicineReminderApp(root, self.current_user, self.conn)
        root.mainloop()
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

class Patient:
    def __init__(self, name, age, gender, medical_history, chronic_diseases, patient_id=None):
        self.name = name
        self.age = age
        self.gender = gender
        self.medical_history = medical_history
        self.chronic_diseases = chronic_diseases
        self.patient_id = patient_id
        self.medicines = []

class Medicine:
    def __init__(self, name, dosage, time_str, disease, is_diabetic, patient, category, meal_timing, medicine_id=None):
        self.name = name
        self.dosage = dosage
        self.time_str = time_str
        self.disease = disease
        self.is_diabetic = is_diabetic
        self.patient = patient
        self.category = category
        self.meal_timing = meal_timing
        self.medicine_id = medicine_id
        self.time_obj = datetime.strptime(time_str, "%I:%M %p").time()

class MedicineReminderApp:
    def __init__(self, root, current_user, conn):
        self.root = root
        self.root.title("Smart Medicine Reminder Pro")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        self.current_user = current_user
        self.conn = conn
        self.patients = []
        self.reminder_history = []
        self.current_patient = None
        self.load_data()
        
        try:
            self.ml_model = joblib.load("medicine_model/medicine_predictor.pkl")
            self.disease_encoder = joblib.load("medicine_model/disease_encoder.pkl")
            self.category_encoder = joblib.load("medicine_model/category_encoder.pkl")
            self.disease_predictor = joblib.load("medicine_model/disease_predictor.pkl")
            self.symptom_encoder = joblib.load("medicine_model/symptom_encoder.pkl")
            print("✅ ML models loaded successfully.")
        except Exception as e:
            print(f"⚠️ ML Model loading failed: {e}")
            self.ml_model = None
            self.disease_encoder = None
            self.category_encoder = None
            self.disease_predictor = None
            self.symptom_encoder = None
            messagebox.showwarning("Warning", "ML models could not be loaded. Disease prediction features will be disabled.")

        self.setup_ui()
        
        self.stop_thread = False
        self.reminder_thread = threading.Thread(target=self.check_reminders)
        self.reminder_thread.daemon = True
        self.reminder_thread.start()

    def setup_ui(self):
        style = ttk.Style()
        style.configure('TFrame', background="#f0f0f0")
        style.configure('TLabel', background="#f0f0f0", font=("Arial", 10))
        style.configure('TButton', font=("Arial", 10), padding=5)
        style.configure('Header.TLabel', font=("Arial", 12, "bold"))
        style.configure('Danger.TButton', foreground='white', background='#dc3545')
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        role_display = "Super Admin" if self.current_user.role == "superadmin" else \
                     "Admin" if self.current_user.role == "admin" else "User"
        role_color = "#d32f2f" if self.current_user.role == "superadmin" else \
                    "#1976d2" if self.current_user.role == "admin" else "#388e3c"
        
        ttk.Label(header_frame, 
                 text=f"Welcome, {self.current_user.username} ({role_display})", 
                 style='Header.TLabel',
                 foreground=role_color).pack(side=tk.LEFT)
        
        ttk.Label(header_frame, text="Smart Medicine Reminder Pro", style='Header.TLabel').pack(side=tk.LEFT, padx=20)
        
        self.time_label = ttk.Label(header_frame, text="", style='Header.TLabel')
        self.time_label.pack(side=tk.RIGHT)
        self.update_time()
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        patient_btn_frame = ttk.LabelFrame(button_frame, text="Patient Management", padding=10)
        patient_btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(patient_btn_frame, text="Add New Patient", command=self.add_patient_info).pack(fill=tk.X, pady=2)
        ttk.Button(patient_btn_frame, text="Select Patient", command=self.select_existing_patient).pack(fill=tk.X, pady=2)
        
        if self.current_user.role in ["admin", "superadmin"]:
            ttk.Button(patient_btn_frame, text="Delete Patient", command=self.delete_patient).pack(fill=tk.X, pady=2)
        
        medicine_btn_frame = ttk.LabelFrame(button_frame, text="Medicine Management", padding=10)
        medicine_btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        self.medicine_button = ttk.Button(medicine_btn_frame, text="Add Medicine", command=self.add_medicine_info, state="disabled")
        self.medicine_button.pack(fill=tk.X, pady=2)
        
        delete_med_btn = ttk.Button(medicine_btn_frame, text="Delete Medicine", command=self.delete_medicine, state="disabled")
        delete_med_btn.pack(fill=tk.X, pady=2)
        
        other_btn_frame = ttk.LabelFrame(button_frame, text="Tools", padding=10)
        other_btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(other_btn_frame, text="Dashboard", command=self.show_dashboard).pack(fill=tk.X, pady=2)
        ttk.Button(other_btn_frame, text="Predict Disease", command=self.predict_disease_from_symptoms).pack(fill=tk.X, pady=2)
        
        if self.current_user.role in ["admin", "superadmin"]:
            admin_btn_frame = ttk.LabelFrame(button_frame, text="Admin Tools", padding=10)
            admin_btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
            
            ttk.Button(admin_btn_frame, text="Manage Users", command=self.show_user_management).pack(fill=tk.X, pady=2)
            ttk.Button(admin_btn_frame, text="Backup Data", command=self.backup_data).pack(fill=tk.X, pady=2)
            
            if self.current_user.role == "superadmin":
                ttk.Button(admin_btn_frame, text="Admin Requests", command=self.show_admin_requests).pack(fill=tk.X, pady=2)
                ttk.Button(admin_btn_frame, text="System Settings", command=self.show_system_settings).pack(fill=tk.X, pady=2)
        
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="Reminder system is active", foreground="green")
        self.status_label.pack(side=tk.LEFT)
        
        self.dark_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(status_frame, text="Dark Mode", variable=self.dark_mode, command=self.toggle_dark_mode).pack(side=tk.RIGHT)
        
        activity_frame = ttk.LabelFrame(main_frame, text="Recent Activity", padding=10)
        activity_frame.pack(fill=tk.BOTH, expand=True)
        
        self.activity_text = tk.Text(activity_frame, height=10, state="disabled", wrap=tk.WORD)
        self.activity_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(activity_frame, orient=tk.VERTICAL, command=self.activity_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.activity_text.config(yscrollcommand=scrollbar.set)
        
        self.add_activity("Application started")
        self.add_activity(f"Logged in as {self.current_user.role}")

    def load_data(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM patients")
        for row in cursor.fetchall():
            patient = Patient(
                name=row[1],
                age=row[2],
                gender=row[3],
                medical_history=row[4],
                chronic_diseases=row[5].split(',') if row[5] else [],
                patient_id=row[0]
            )
            
            cursor.execute("SELECT * FROM medicines WHERE patient_id = ?", (patient.patient_id,))
            for med_row in cursor.fetchall():
                try:
                    time_str = med_row[4]
                    if ' ' not in time_str:
                        hour, minute = map(int, time_str.split(':'))
                        am_pm = "AM" if hour < 12 else "PM"
                        if hour > 12:
                            hour -= 12
                        elif hour == 0:
                            hour = 12
                        time_str = f"{hour}:{minute:02d} {am_pm}"
                    
                    medicine = Medicine(
                        name=med_row[2],
                        dosage=med_row[3],
                        time_str=time_str,
                        disease=med_row[5],
                        is_diabetic=bool(med_row[6]),
                        patient=patient,
                        category=med_row[7],
                        meal_timing=med_row[8],
                        medicine_id=med_row[0]
                    )
                    patient.medicines.append(medicine)
                except Exception as e:
                    print(f"Error loading medicine {med_row[2]}: {e}")
            
            self.patients.append(patient)

    def save_patient(self, patient):
        cursor = self.conn.cursor()
        if patient.patient_id:
            cursor.execute('''
                UPDATE patients SET name = ?, age = ?, gender = ?, medical_history = ?, chronic_diseases = ?
                WHERE patient_id = ?
            ''', (patient.name, patient.age, patient.gender, patient.medical_history,
                  ','.join(patient.chronic_diseases), patient.patient_id))
        else:
            cursor.execute('''
                INSERT INTO patients (name, age, gender, medical_history, chronic_diseases)
                VALUES (?, ?, ?, ?, ?)
            ''', (patient.name, patient.age, patient.gender, patient.medical_history,
                  ','.join(patient.chronic_diseases)))
            patient.patient_id = cursor.lastrowid
        
        for medicine in patient.medicines:
            if medicine.medicine_id:
                cursor.execute('''
                    UPDATE medicines SET name = ?, dosage = ?, time_str = ?, disease = ?, 
                    is_diabetic = ?, category = ?, meal_timing = ?
                    WHERE medicine_id = ?
                ''', (medicine.name, medicine.dosage, medicine.time_str, medicine.disease,
                      medicine.is_diabetic, medicine.category, medicine.meal_timing, medicine.medicine_id))
            else:
                cursor.execute('''
                    INSERT INTO medicines (patient_id, name, dosage, time_str, disease, is_diabetic, category, meal_timing)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (patient.patient_id, medicine.name, medicine.dosage, medicine.time_str,
                      medicine.disease, medicine.is_diabetic, medicine.category, medicine.meal_timing))
                medicine.medicine_id = cursor.lastrowid
        
        self.conn.commit()

    def update_time(self):
        current_time = datetime.now().strftime("%I:%M:%S %p")
        self.time_label.config(text=f"Current Time: {current_time}")
        self.root.after(1000, self.update_time)
    
    def add_activity(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_text.config(state="normal")
        self.activity_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.activity_text.config(state="disabled")
        self.activity_text.see(tk.END)
    
    def toggle_dark_mode(self):
        if self.dark_mode.get():
            bg_color = "#121212"
            fg_color = "#ffffff"
            entry_bg = "#333333"
            entry_fg = "#ffffff"
        else:
            bg_color = "#f0f0f0"
            fg_color = "#000000"
            entry_bg = "#ffffff"
            entry_fg = "#000000"
        
        self.root.configure(bg=bg_color)
        
        for widget in self.root.winfo_children():
            self.update_widget_colors(widget, bg_color, fg_color, entry_bg, entry_fg)
    
    def update_widget_colors(self, widget, bg_color, fg_color, entry_bg, entry_fg):
        if isinstance(widget, (tk.Frame, ttk.Frame, ttk.LabelFrame)):
            widget.configure(style='TFrame')
        
        if isinstance(widget, (tk.Label, ttk.Label)):
            widget.configure(foreground=fg_color, background=bg_color)
        
        if isinstance(widget, tk.Entry):
            widget.configure(background=entry_bg, foreground=entry_fg, insertbackground=fg_color)
        
        if isinstance(widget, tk.Text):
            widget.configure(background=entry_bg, foreground=fg_color, insertbackground=fg_color)
        
        if isinstance(widget, tk.Listbox):
            widget.configure(background=entry_bg, foreground=fg_color)
        
        for child in widget.winfo_children():
            self.update_widget_colors(child, bg_color, fg_color, entry_bg, entry_fg)

    def add_patient_info(self):
        patient_window = tk.Toplevel(self.root)
        patient_window.title("Add New Patient")
        patient_window.geometry("400x400")
        
        form_frame = ttk.Frame(patient_window, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(form_frame, text="Patient Name:").grid(row=0, column=0, sticky="e", pady=5)
        name_entry = ttk.Entry(form_frame)
        name_entry.grid(row=0, column=1, pady=5, sticky="ew")
        
        ttk.Label(form_frame, text="Age:").grid(row=1, column=0, sticky="e", pady=5)
        age_entry = ttk.Entry(form_frame)
        age_entry.grid(row=1, column=1, pady=5, sticky="ew")
        
        ttk.Label(form_frame, text="Gender:").grid(row=2, column=0, sticky="e", pady=5)
        gender_var = tk.StringVar()
        gender_choices = ["Male", "Female", "Other", "Prefer not to say"]
        gender_dropdown = ttk.Combobox(form_frame, textvariable=gender_var, values=gender_choices)
        gender_dropdown.current(0)
        gender_dropdown.grid(row=2, column=1, pady=5, sticky="ew")
        
        ttk.Label(form_frame, text="Medical History:").grid(row=3, column=0, sticky="e", pady=5)
        medical_history_entry = tk.Text(form_frame, height=4, width=30)
        medical_history_entry.grid(row=3, column=1, pady=5, sticky="ew")
        
        ttk.Label(form_frame, text="Chronic Diseases (comma-separated):").grid(row=4, column=0, sticky="e", pady=5)
        chronic_diseases_entry = ttk.Entry(form_frame)
        chronic_diseases_entry.grid(row=4, column=1, pady=5, sticky="ew")
        
        button_frame = ttk.Frame(patient_window, padding=10)
        button_frame.pack(fill=tk.X)
        
        def save_patient_info():
            name = name_entry.get()
            age = age_entry.get()
            gender = gender_var.get()
            medical_history = medical_history_entry.get("1.0", tk.END).strip()
            chronic_diseases = [disease.strip() for disease in chronic_diseases_entry.get().split(",")] if chronic_diseases_entry.get() else []

            if not name or not age or not medical_history or not gender:
                messagebox.showerror("Error", "Please fill all required fields")
                return

            if not age.isdigit() or int(age) <= 0:
                messagebox.showerror("Error", "Please enter a valid age")
                return

            self.current_patient = Patient(name, int(age), gender, medical_history, chronic_diseases)
            self.save_patient(self.current_patient)
            self.patients.append(self.current_patient)
            self.medicine_button.config(state="normal")
            
            patient_window.destroy()
            self.add_activity(f"Added new patient: {name}")
            messagebox.showinfo("Success", "Patient info saved successfully!")
        
        ttk.Button(button_frame, text="Save", command=save_patient_info).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=patient_window.destroy).pack(side=tk.RIGHT)

    def select_existing_patient(self):
        if not self.patients:
            messagebox.showinfo("No Patients", "There are no patients in the system. Please add a patient first.")
            return
            
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Select Patient")
        selection_window.geometry("500x400")
        
        search_frame = ttk.Frame(selection_window, padding=10)
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        list_frame = ttk.Frame(selection_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("ID", "Name", "Age", "Gender", "Chronic Diseases")
        self.patient_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        
        for col in columns:
            self.patient_tree.heading(col, text=col)
            self.patient_tree.column(col, width=100)
        
        for patient in self.patients:
            self.patient_tree.insert("", tk.END, values=(
                patient.patient_id,
                patient.name,
                patient.age,
                patient.gender,
                ", ".join(patient.chronic_diseases) if patient.chronic_diseases else "None"
            ))
        
        self.patient_tree.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.patient_tree.yview)
        self.patient_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        button_frame = ttk.Frame(selection_window, padding=10)
        button_frame.pack(fill=tk.X)
        
        def on_select():
            selected_item = self.patient_tree.selection()
            if not selected_item:
                messagebox.showerror("Error", "Please select a patient")
                return
                
            selected_id = int(self.patient_tree.item(selected_item, "values")[0])
            self.current_patient = next((p for p in self.patients if p.patient_id == selected_id), None)
            self.medicine_button.config(state="normal")
            
            selection_window.destroy()
            self.add_activity(f"Selected patient: {self.current_patient.name}")
            messagebox.showinfo("Selected", f"Selected patient: {self.current_patient.name}")
        
        ttk.Button(button_frame, text="Select", command=on_select).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=selection_window.destroy).pack(side=tk.RIGHT)
        
        def update_search(*args):
            search_term = search_entry.get().lower()
            for item in self.patient_tree.get_children():
                values = self.patient_tree.item(item, "values")
                if any(search_term in str(value).lower() for value in values):
                    self.patient_tree.item(item, tags=('match',))
                    self.patient_tree.detach(item)
                    self.patient_tree.reattach(item, '', 'end')
                else:
                    self.patient_tree.detach(item)
        
        search_entry.bind("<KeyRelease>", update_search)

    def delete_patient(self):
        if not self.patients:
            messagebox.showinfo("No Patients", "There are no patients to delete.")
            return
        
        delete_window = tk.Toplevel(self.root)
        delete_window.title("Delete Patient")
        delete_window.geometry("500x400")
        
        columns = ("ID", "Name", "Age", "Gender")
        tree = ttk.Treeview(delete_window, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        for patient in self.patients:
            tree.insert("", tk.END, values=(
                patient.patient_id,
                patient.name,
                patient.age,
                patient.gender
            ))
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        button_frame = ttk.Frame(delete_window, padding=10)
        button_frame.pack(fill=tk.X)
        
        def on_delete():
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showerror("Error", "Please select a patient to delete")
                return
                
            selected_id = int(tree.item(selected_item, "values")[0])
            patient_to_delete = next((p for p in self.patients if p.patient_id == selected_id), None)
            
            if not patient_to_delete:
                messagebox.showerror("Error", "Selected patient not found")
                return
                
            confirm = messagebox.askyesno("Confirm Delete", 
                                         f"Are you sure you want to delete patient {patient_to_delete.name} and all their medicines?")
            if confirm:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM medicines WHERE patient_id = ?", (selected_id,))
                cursor.execute("DELETE FROM patients WHERE patient_id = ?", (selected_id,))
                self.conn.commit()
                
                self.patients = [p for p in self.patients if p.patient_id != selected_id]
                self.add_activity(f"Deleted patient: {patient_to_delete.name}")
                messagebox.showinfo("Success", "Patient deleted successfully")
                delete_window.destroy()
                
                if self.current_patient and self.current_patient.patient_id == selected_id:
                    self.current_patient = None
                    self.medicine_button.config(state="disabled")
        
        ttk.Button(button_frame, text="Delete", command=on_delete, style='Danger.TButton').pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=delete_window.destroy).pack(side=tk.RIGHT)

    def add_medicine_info(self):
        if not self.current_patient:
            messagebox.showerror("Error", "No patient selected")
            return
        
        medicine_window = tk.Toplevel(self.root)
        medicine_window.title(f"Add Medicine for {self.current_patient.name}")
        medicine_window.geometry("500x600")
        
        form_frame = ttk.Frame(medicine_window, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(form_frame, text="Medicine Name:").grid(row=0, column=0, sticky="e", pady=5)
        medicine_name_entry = ttk.Entry(form_frame)
        medicine_name_entry.grid(row=0, column=1, pady=5, sticky="ew")
        
        ttk.Label(form_frame, text="Dosage:").grid(row=1, column=0, sticky="e", pady=5)
        dosage_entry = ttk.Entry(form_frame)
        dosage_entry.grid(row=1, column=1, pady=5, sticky="ew")
        
        ttk.Label(form_frame, text="Time:").grid(row=2, column=0, sticky="e", pady=5)
        time_frame = ttk.Frame(form_frame)
        time_frame.grid(row=2, column=1, pady=5, sticky="ew")
        
        hour_var = tk.StringVar(value="08")
        ttk.Combobox(time_frame, textvariable=hour_var, values=[f"{i:02d}" for i in range(1, 13)], width=3).pack(side=tk.LEFT)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        
        minute_var = tk.StringVar(value="00")
        ttk.Combobox(time_frame, textvariable=minute_var, values=[f"{i:02d}" for i in range(0, 60, 5)], width=3).pack(side=tk.LEFT)
        
        am_pm_var = tk.StringVar(value="AM")
        ttk.Combobox(time_frame, textvariable=am_pm_var, values=["AM", "PM"], width=3).pack(side=tk.LEFT)
        
        ttk.Label(form_frame, text="Disease/Condition:").grid(row=3, column=0, sticky="e", pady=5)
        disease_frame = ttk.Frame(form_frame)
        disease_frame.grid(row=3, column=1, pady=5, sticky="ew")
        
        disease_entry = ttk.Entry(disease_frame)
        disease_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(form_frame, text="Options:").grid(row=4, column=0, sticky="e", pady=5)
        options_frame = ttk.Frame(form_frame)
        options_frame.grid(row=4, column=1, pady=5, sticky="w")
        
        is_diabetic_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="For Diabetes", variable=is_diabetic_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(form_frame, text="Category:").grid(row=5, column=0, sticky="e", pady=5)
        category_var = tk.StringVar(value="Oral")
        category_dropdown = ttk.Combobox(form_frame, textvariable=category_var, 
                                       values=["Oral", "Injection", "Topical", "Inhaler", "Other"])
        category_dropdown.grid(row=5, column=1, pady=5, sticky="ew")
        
        ttk.Label(form_frame, text="Meal Timing:").grid(row=6, column=0, sticky="e", pady=5)
        meal_timing_var = tk.StringVar(value="After meal")
        meal_timing_dropdown = ttk.Combobox(form_frame, textvariable=meal_timing_var, 
                                          values=["Before meal", "After meal", "With meal", "Independent of meal"])
        meal_timing_dropdown.grid(row=6, column=1, pady=5, sticky="ew")
        
        ttk.Label(form_frame, text="Notes:").grid(row=7, column=0, sticky="ne", pady=5)
        notes_entry = tk.Text(form_frame, height=4, width=30)
        notes_entry.grid(row=7, column=1, pady=5, sticky="ew")
        
        button_frame = ttk.Frame(medicine_window, padding=10)
        button_frame.pack(fill=tk.X)
        
        def predict_disease_from_symptoms():
            if not self.disease_predictor or not self.symptom_encoder:
                messagebox.showerror("Error", 
                               "Disease prediction model not loaded.\n"
                               "Please make sure all model files exist in the medicine_model directory.")
                return
            
            symptoms = simpledialog.askstring("Symptoms", "Enter symptoms (comma separated):")
            if not symptoms:
                return
            
            try:
                symptoms_list = [s.strip().lower() for s in symptoms.split(",")]
                symptom_vector = self.symptom_encoder.transform(symptoms_list)
                predicted_disease = self.disease_predictor.predict([symptom_vector])[0]
                
                disease_entry.delete(0, tk.END)
                disease_entry.insert(0, predicted_disease)
                
                if self.ml_model:
                    try:
                        age = self.current_patient.age
                        is_diabetic_flag = int(is_diabetic_var.get())
                        has_hypertension = int("hypertension" in [d.lower() for d in self.current_patient.chronic_diseases])
                        
                        if predicted_disease.lower() in self.disease_encoder.classes_:
                            disease_encoded = self.disease_encoder.transform([predicted_disease.lower()])[0]
                            
                            input_df = pd.DataFrame([{
                                "age": age,
                                "is_diabetic": is_diabetic_flag,
                                "has_hypertension": has_hypertension,
                                "disease_encoded": disease_encoded
                            }])
                            
                            pred_encoded = self.ml_model.predict(input_df)[0]
                            predicted_category = self.category_encoder.inverse_transform([pred_encoded])[0]
                            
                            category_var.set(predicted_category)
                            self.add_activity(f"Predicted disease: {predicted_disease}, suggested category: {predicted_category}")
                    except Exception as e:
                        print(f"Error in category prediction: {e}")
                
                messagebox.showinfo("Prediction Result", 
                                  f"Predicted Disease: {predicted_disease}\n"
                                  f"Based on symptoms: {symptoms}")
            except Exception as e:
                messagebox.showerror("Prediction Error", f"Failed to predict disease: {str(e)}")
        
        def save_medicine_info():
            medicine_name = medicine_name_entry.get()
            dosage = dosage_entry.get()
            hour = hour_var.get()
            minute = minute_var.get()
            am_pm = am_pm_var.get()
            time_str = f"{hour}:{minute} {am_pm}"
            disease = disease_entry.get()
            is_diabetic = is_diabetic_var.get()
            category = category_var.get()
            meal_timing = meal_timing_var.get()
            
            if not medicine_name or not dosage or not disease:
                messagebox.showerror("Error", "Please fill all required fields")
                return
                
            try:
                datetime.strptime(time_str, "%I:%M %p")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid time")
                return
                
            medicine = Medicine(
                name=medicine_name,
                dosage=dosage,
                time_str=time_str,
                disease=disease,
                is_diabetic=is_diabetic,
                patient=self.current_patient,
                category=category,
                meal_timing=meal_timing
            )
            
            self.current_patient.medicines.append(medicine)
            self.save_patient(self.current_patient)
            self.add_activity(f"Added medicine {medicine_name} for {self.current_patient.name}")
            messagebox.showinfo("Success", "Medicine saved successfully!")
            medicine_window.destroy()
        
        ttk.Button(button_frame, text="Predict from Symptoms", command=predict_disease_from_symptoms).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save", command=save_medicine_info).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=medicine_window.destroy).pack(side=tk.RIGHT)

    def delete_medicine(self):
        if not self.current_patient or not self.current_patient.medicines:
            messagebox.showinfo("No Medicines", "No medicines to delete for the selected patient")
            return
            
        delete_window = tk.Toplevel(self.root)
        delete_window.title(f"Delete Medicine for {self.current_patient.name}")
        delete_window.geometry("600x400")
        
        list_frame = ttk.Frame(delete_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("ID", "Name", "Dosage", "Time", "Disease", "Category")
        medicine_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        
        for col in columns:
            medicine_tree.heading(col, text=col)
            medicine_tree.column(col, width=100)
        
        for med in self.current_patient.medicines:
            medicine_tree.insert("", tk.END, values=(
                med.medicine_id,
                med.name,
                med.dosage,
                med.time_str,
                med.disease,
                med.category
            ))
        
        medicine_tree.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=medicine_tree.yview)
        medicine_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        button_frame = ttk.Frame(delete_window, padding=10)
        button_frame.pack(fill=tk.X)
        
        def on_delete():
            selected_item = medicine_tree.selection()
            if not selected_item:
                messagebox.showerror("Error", "Please select a medicine to delete")
                return
                
            selected_id = int(medicine_tree.item(selected_item, "values")[0])
            medicine_to_delete = next((m for m in self.current_patient.medicines if m.medicine_id == selected_id), None)
            
            if not medicine_to_delete:
                messagebox.showerror("Error", "Selected medicine not found")
                return
                
            confirm = messagebox.askyesno("Confirm Delete", 
                                         f"Are you sure you want to delete {medicine_to_delete.name}?")
            if confirm:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM medicines WHERE medicine_id = ?", (selected_id,))
                self.conn.commit()
                
                self.current_patient.medicines = [m for m in self.current_patient.medicines if m.medicine_id != selected_id]
                self.add_activity(f"Deleted medicine {medicine_to_delete.name} for {self.current_patient.name}")
                messagebox.showinfo("Success", "Medicine deleted successfully")
                delete_window.destroy()
        
        ttk.Button(button_frame, text="Delete", command=on_delete, style='Danger.TButton').pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=delete_window.destroy).pack(side=tk.RIGHT)

    def predict_disease_from_symptoms(self):
        if not self.disease_predictor:
            messagebox.showerror("Error", "Disease prediction model not loaded")
            return
            
        predict_window = tk.Toplevel(self.root)
        predict_window.title("Disease Prediction")
        predict_window.geometry("400x300")
        
        form_frame = ttk.Frame(predict_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(form_frame, text="Enter Symptoms (comma separated):", font=("Arial", 10, "bold")).pack(pady=10)
        
        symptoms_entry = tk.Text(form_frame, height=8, width=40)
        symptoms_entry.pack(fill=tk.BOTH, expand=True, pady=10)
        
        result_frame = ttk.Frame(predict_window, padding=10)
        result_frame.pack(fill=tk.X)
        
        result_label = ttk.Label(result_frame, text="", font=("Arial", 10))
        result_label.pack()
        
        button_frame = ttk.Frame(predict_window, padding=10)
        button_frame.pack(fill=tk.X)
        
        def predict_disease():
            symptoms = symptoms_entry.get("1.0", tk.END).strip()
            if not symptoms:
                messagebox.showerror("Error", "Please enter symptoms")
                return
                
            try:
                symptoms_list = [s.strip().lower() for s in symptoms.split(",")]
                symptom_vector = self.symptom_encoder.transform(symptoms_list)
                predicted_disease = self.disease_predictor.predict([symptom_vector])[0]
                
                result_label.config(text=f"Predicted Disease: {predicted_disease}")
                self.add_activity(f"Predicted disease '{predicted_disease}' from symptoms: {symptoms}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to predict disease: {e}")
        
        ttk.Button(button_frame, text="Predict", command=predict_disease).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Close", command=predict_window.destroy).pack(side=tk.RIGHT)

    def show_admin_requests(self):
        if self.current_user.role != "superadmin":
            return
            
        requests_window = tk.Toplevel(self.root)
        requests_window.title("Admin Requests")
        requests_window.geometry("600x400")
        
        columns = ("Username", "Request Date", "Status")
        tree = ttk.Treeview(requests_window, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(requests_window)
        btn_frame.pack(fill=tk.X, pady=5)
        
        def approve_request():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select a request")
                return
                
            username = tree.item(selected, "values")[0]
            
            cursor = self.conn.cursor()
            cursor.execute("UPDATE users SET role = 'admin', approved = 1 WHERE username = ?", (username,))
            self.conn.commit()
            
            messagebox.showinfo("Approved", f"{username} is now an admin")
            tree.delete(selected)
        
        def deny_request():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select a request")
                return
                
            username = tree.item(selected, "values")[0]
            tree.delete(selected)
            messagebox.showinfo("Denied", f"Request from {username} denied")
        
        tk.Button(btn_frame, text="Approve", command=approve_request, bg="green", fg="white").pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Deny", command=deny_request, bg="red", fg="white").pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Close", command=requests_window.destroy).pack(side=tk.RIGHT)

    def show_system_settings(self):
        if self.current_user.role != "superadmin":
            return
            
        settings_window = tk.Toplevel(self.root)
        settings_window.title("System Settings")
        settings_window.geometry("400x300")
        
        tk.Label(settings_window, text="System Configuration", font=("Arial", 12)).pack(pady=10)
        
        tk.Label(settings_window, text="Reminder Sound:").pack()
        sound_var = tk.StringVar(value="default")
        ttk.Combobox(settings_window, textvariable=sound_var, 
                    values=["Default", "Beep", "Chime"]).pack()
        
        tk.Label(settings_window, text="Backup Frequency:").pack()
        backup_var = tk.StringVar(value="daily")
        ttk.Combobox(settings_window, textvariable=backup_var, 
                    values=["Daily", "Weekly", "Monthly"]).pack()
        
        def save_settings():
            messagebox.showinfo("Saved", "Settings saved successfully")
            settings_window.destroy()
        
        tk.Button(settings_window, text="Save Settings", command=save_settings).pack(pady=10)

    def show_user_management(self):
        if self.current_user.role not in ["admin", "superadmin"]:
            return
            
        user_window = tk.Toplevel(self.root)
        user_window.title("User Management")
        user_window.geometry("600x400")
        
        columns = ("Username", "Role", "Status")
        tree = ttk.Treeview(user_window, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT username, role, approved FROM users")
        for user in cursor.fetchall():
            status = "Approved" if user[2] else "Pending"
            tree.insert("", tk.END, values=(user[0], user[1], status))
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(user_window)
        btn_frame.pack(fill=tk.X, pady=5)
        
        def edit_user():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select a user")
                return
                
            username = tree.item(selected, "values")[0]
            
            if username == self.current_user.username:
                messagebox.showerror("Error", "You cannot edit your own account")
                return
                
            edit_window = tk.Toplevel(user_window)
            edit_window.title(f"Edit User {username}")
            
            tk.Label(edit_window, text="Role:").pack()
            role_var = tk.StringVar(value="user")
            
            if self.current_user.role == "superadmin":
                roles = ["user", "admin", "superadmin"]
            else:
                roles = ["user", "admin"]
                
            ttk.Combobox(edit_window, textvariable=role_var, values=roles, state="readonly").pack()
            
            tk.Label(edit_window, text="Status:").pack()
            approved_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(edit_window, text="Approved", variable=approved_var).pack()
            
            def save_changes():
                cursor = self.conn.cursor()
                cursor.execute("UPDATE users SET role = ?, approved = ? WHERE username = ?",
                             (role_var.get(), approved_var.get(), username))
                self.conn.commit()
                
                status = "Approved" if approved_var.get() else "Pending"
                tree.item(selected, values=(username, role_var.get(), status))
                
                messagebox.showinfo("Saved", "Changes saved successfully")
                edit_window.destroy()
            
            tk.Button(edit_window, text="Save", command=save_changes).pack(pady=10)
        
        def delete_user():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select a user")
                return
                
            username = tree.item(selected, "values")[0]
            
            if username == self.current_user.username:
                messagebox.showerror("Error", "You cannot delete your own account")
                return
                
            if messagebox.askyesno("Confirm", f"Delete user {username} permanently?"):
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM users WHERE username = ?", (username,))
                self.conn.commit()
                tree.delete(selected)
                messagebox.showinfo("Deleted", "User deleted successfully")
        
        tk.Button(btn_frame, text="Edit User", command=edit_user).pack(side=tk.LEFT)
        
        if self.current_user.role == "superadmin":
            tk.Button(btn_frame, text="Delete User", command=delete_user, bg="red", fg="white").pack(side=tk.LEFT)
        
        tk.Button(btn_frame, text="Close", command=user_window.destroy).pack(side=tk.RIGHT)

    def backup_data(self):
        if self.current_user.role not in ["admin", "superadmin"]:
            return
            
        try:
            import shutil
            from datetime import datetime
            
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"backup_{timestamp}.db")
            
            shutil.copy2('medicine_reminder.db', backup_file)
            
            messagebox.showinfo("Backup", f"Backup created successfully at:\n{backup_file}")
            self.add_activity(f"Created backup: {backup_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed: {str(e)}")

    def check_reminders(self):
        last_minute_checked = -1
        
        while not self.stop_thread:
            try:
                now = datetime.now()
                current_time = now.time()
                current_minute = now.minute
                
                if current_minute != last_minute_checked:
                    last_minute_checked = current_minute
                    
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"Reminder active - Current time: {now.strftime('%I:%M:%S %p')}"
                    ))
                    
                    today = now.strftime('%Y-%m-%d')
                    
                    for patient in self.patients:
                        for medicine in patient.medicines:
                            if (current_time.hour == medicine.time_obj.hour and 
                                current_time.minute == medicine.time_obj.minute):
                                
                                reminder_key = f"{patient.name}_{medicine.name}_{today}_{medicine.time_obj.hour}:{medicine.time_obj.minute}"
                                
                                if reminder_key not in self.reminder_history:
                                    self.reminder_history.append(reminder_key)
                                    self.trigger_reminder(patient, medicine)
                    
                    self.reminder_history = [r for r in self.reminder_history if today in r]
                
                time.sleep(1)
            except Exception as e:
                print(f"Error in reminder thread: {e}")
                time.sleep(5)

    def trigger_reminder(self, patient, medicine):
        self.root.after(0, lambda: self._show_reminder(patient, medicine))
        self._play_reminder_sound()
        self.add_activity(f"Triggered reminder for {patient.name}: {medicine.name} at {medicine.time_str}")

    def _show_reminder(self, patient, medicine):
        reminder_text = f"MEDICINE REMINDER\n\n"
        reminder_text += f"Patient: {patient.name} ({patient.age}, {patient.gender})\n"
        reminder_text += f"Medicine: {medicine.name} ({medicine.dosage})\n"
        reminder_text += f"Category: {medicine.category}\n"
        reminder_text += f"For: {medicine.disease}\n"
        reminder_text += f"Take: {medicine.meal_timing}\n"
        reminder_text += f"Time: {datetime.now().strftime('%I:%M %p')}\n"
        
        if medicine.is_diabetic:
            reminder_text += "\n⚠️ DIABETIC MEDICATION ⚠️\n"

        try:
            reminder_window = tk.Toplevel(self.root)
            reminder_window.title("Medicine Reminder")
            reminder_window.geometry("400x300")
            reminder_window.lift()
            reminder_window.attributes('-topmost', True)
            
            reminder_frame = tk.Frame(reminder_window, bg="#FFD700", padx=20, pady=20)
            reminder_frame.pack(fill=tk.BOTH, expand=True)
            
            reminder_label = tk.Label(reminder_frame, 
                                    text=reminder_text,
                                    font=("Arial", 12, "bold"),
                                    bg="#FFD700",
                                    justify=tk.LEFT)
            reminder_label.pack(pady=10)
            
            button_frame = tk.Frame(reminder_frame, bg="#FFD700")
            button_frame.pack(pady=10)
            
            def mark_taken():
                reminder_window.destroy()
                self.add_activity(f"Marked {medicine.name} as taken for {patient.name}")
                messagebox.showinfo("Confirmation", f"Marked {medicine.name} as taken!")
            
            take_button = tk.Button(button_frame, 
                                text="Mark as Taken",
                                font=("Arial", 12, "bold"),
                                bg="#4CAF50",
                                fg="white",
                                command=mark_taken)
            take_button.pack(pady=10)
            
            reminder_window.after(60000, reminder_window.destroy)
        except Exception as e:
            print(f"Error showing reminder: {e}")

    def _play_reminder_sound(self):
        try:
            for _ in range(7):
                winsound.Beep(1000, 500)
                time.sleep(0.3)
        except Exception as e:
            print(f"Sound error: {e}")

    def show_dashboard(self):
        dashboard_window = tk.Toplevel(self.root)
        dashboard_window.title("Dashboard")
        dashboard_window.geometry("800x600")
        
        tabs = ttk.Notebook(dashboard_window)
        
        summary_tab = ttk.Frame(tabs)
        tabs.add(summary_tab, text="Summary")
        
        schedule_tab = ttk.Frame(tabs)
        tabs.add(schedule_tab, text="Schedule")
        
        patients_tab = ttk.Frame(tabs)
        tabs.add(patients_tab, text="Patients")
        
        stats_tab = ttk.Frame(tabs)
        tabs.add(stats_tab, text="Statistics")
        
        tabs.pack(expand=1, fill="both")
        
        self._create_summary_tab(summary_tab)
        self._create_schedule_tab(schedule_tab)
        self._create_patients_tab(patients_tab)
        self._create_stats_tab(stats_tab)
        
        self.add_activity("Opened dashboard")

    def _create_summary_tab(self, tab):
        summary_frame = ttk.Frame(tab, padding=10)
        summary_frame.pack(fill=tk.BOTH, expand=True)
        
        stats_frame = ttk.Frame(summary_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        
        total_patients = len(self.patients)
        total_medicines = sum(len(p.medicines) for p in self.patients)
        diabetic_count = sum(1 for p in self.patients for m in p.medicines if m.is_diabetic)
        
        ttk.Label(stats_frame, text=f"Total Patients: {total_patients}", font=("Arial", 12)).grid(row=0, column=0, padx=20, pady=5, sticky="w")
        ttk.Label(stats_frame, text=f"Total Medicines: {total_medicines}", font=("Arial", 12)).grid(row=1, column=0, padx=20, pady=5, sticky="w")
        ttk.Label(stats_frame, text=f"Diabetic Medications: {diabetic_count}", font=("Arial", 12)).grid(row=2, column=0, padx=20, pady=5, sticky="w")
        
        activity_frame = ttk.LabelFrame(summary_frame, text="Recent Activity", padding=10)
        activity_frame.pack(fill=tk.BOTH, expand=True)
        
        activity_text = tk.Text(activity_frame, height=10, state="disabled", wrap=tk.WORD)
        activity_text.pack(fill=tk.BOTH, expand=True)
        
        self.activity_text.config(state="normal")
        last_activities = self.activity_text.get("1.0", tk.END).split("\n")[-11:-1]
        self.activity_text.config(state="disabled")
        
        activity_text.config(state="normal")
        for activity in last_activities:
            activity_text.insert(tk.END, activity + "\n")
        activity_text.config(state="disabled")
        
        scrollbar = ttk.Scrollbar(activity_frame, orient=tk.VERTICAL, command=activity_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        activity_text.config(yscrollcommand=scrollbar.set)

    def _create_schedule_tab(self, tab):
        schedule_frame = ttk.Frame(tab, padding=10)
        schedule_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(schedule_frame, text="Today's Medication Schedule", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)
        
        columns = ("Time", "Patient", "Medicine", "Dosage", "Disease", "Category")
        schedule_tree = ttk.Treeview(schedule_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            schedule_tree.heading(col, text=col)
            schedule_tree.column(col, width=100, anchor=tk.W)
        
        all_meds = []
        for patient in self.patients:
            for medicine in patient.medicines:
                all_meds.append((
                    medicine.time_str,
                    patient.name,
                    medicine.name,
                    medicine.dosage,
                    medicine.disease,
                    medicine.category
                ))
        
        all_meds.sort(key=lambda x: datetime.strptime(x[0], "%I:%M %p").time())
        
        for med in all_meds:
            schedule_tree.insert("", tk.END, values=med)
            
        schedule_tree.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(schedule_frame, orient=tk.VERTICAL, command=schedule_tree.yview)
        schedule_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_patients_tab(self, tab):
        patients_frame = ttk.Frame(tab, padding=10)
        patients_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(patients_frame, text="Patient Records", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)
        
        columns = ("Name", "Age", "Gender", "Chronic Diseases", "Medicines")
        patients_tree = ttk.Treeview(patients_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            patients_tree.heading(col, text=col)
            patients_tree.column(col, width=120, anchor=tk.W)
        
        for patient in self.patients:
            patients_tree.insert("", tk.END, values=(
                patient.name,
                patient.age,
                patient.gender,
                ", ".join(patient.chronic_diseases) if patient.chronic_diseases else "None",
                len(patient.medicines)
            ))
            
        patients_tree.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(patients_frame, orient=tk.VERTICAL, command=patients_tree.yview)
        patients_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def on_double_click(event):
            item = patients_tree.selection()[0]
            patient_name = patients_tree.item(item, "values")[0]
            patient = next((p for p in self.patients if p.name == patient_name), None)
            
            if patient:
                self._show_patient_details(patient)
        
        patients_tree.bind("<Double-1>", on_double_click)

    def _show_patient_details(self, patient):
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Patient Details - {patient.name}")
        details_window.geometry("600x500")
        
        main_frame = ttk.Frame(details_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        info_frame = ttk.LabelFrame(main_frame, text="Patient Information", padding=10)
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text=f"Name: {patient.name}").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(info_frame, text=f"Age: {patient.age}").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(info_frame, text=f"Gender: {patient.gender}").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Label(info_frame, text=f"Chronic Diseases: {', '.join(patient.chronic_diseases) if patient.chronic_diseases else 'None'}").grid(row=3, column=0, sticky="w", pady=2)
        
        history_frame = ttk.LabelFrame(main_frame, text="Medical History", padding=10)
        history_frame.pack(fill=tk.X, pady=5)
        
        history_text = tk.Text(history_frame, height=5, wrap=tk.WORD)
        historyاضی

        history_text.insert(tk.END, patient.medical_history)
        history_text.config(state="disabled")
        history_text.pack(fill=tk.X)
        
        meds_frame = ttk.LabelFrame(main_frame, text="Medications", padding=10)
        meds_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Name", "Dosage", "Time", "Disease", "Category")
        meds_tree = ttk.Treeview(meds_frame, columns=columns, show="headings", height=5)
        
        for col in columns:
            meds_tree.heading(col, text=col)
            meds_tree.column(col, width=100, anchor=tk.W)
        
        for medicine in patient.medicines:
            meds_tree.insert("", tk.END, values=(
                medicine.name,
                medicine.dosage,
                medicine.time_str,
                medicine.disease,
                medicine.category
            ))
            
        meds_tree.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(meds_frame, orient=tk.VERTICAL, command=meds_tree.yview)
        meds_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_stats_tab(self, tab):
        stats_frame = ttk.Frame(tab, padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(stats_frame, text="Medication Statistics", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)
        
        total_meds = sum(len(p.medicines) for p in self.patients)
        diabetic_meds = sum(1 for p in self.patients for m in p.medicines if m.is_diabetic)
        morning_meds = sum(1 for p in self.patients for m in p.medicines if m.time_obj.hour < 12)
        afternoon_meds = sum(1 for p in self.patients for m in p.medicines if 12 <= m.time_obj.hour < 17)
        evening_meds = sum(1 for p in self.patients for m in p.medicines if m.time_obj.hour >= 17)
        
        categories = {}
        for p in self.patients:
            for m in p.medicines:
                categories[m.category] = categories.get(m.category, 0) + 1
        
        stats_text = tk.Text(stats_frame, height=15, wrap=tk.WORD)
        stats_text.insert(tk.END, "=== General Statistics ===\n")
        stats_text.insert(tk.END, f"Total Medications: {total_meds}\n")
        stats_text.insert(tk.END, f"Diabetic Medications: {diabetic_meds}\n")
        stats_text.insert(tk.END, f"Morning Medications: {morning_meds}\n")
        stats_text.insert(tk.END, f"Afternoon Medications: {afternoon_meds}\n")
        stats_text.insert(tk.END, f"Evening Medications: {evening_meds}\n\n")
        
        stats_text.insert(tk.END, "=== Category Distribution ===\n")
        for category, count in categories.items():
            stats_text.insert(tk.END, f"{category}: {count} ({count/total_meds:.1%})\n")
        
        stats_text.config(state="disabled")
        stats_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=stats_text.yview)
        stats_text.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def on_closing(self):
        self.stop_thread = True
        self.conn.close()
        self.add_activity("Application closed")
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    login_app = LoginApp(root)
    root.mainloop()