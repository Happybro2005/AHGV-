import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk  
import re
import psycopg2 
import sys 
import os 

#Configure these variables for your PostgreSQL server!

DB_HOST = os.getenv("PG_HOST", "localhost")  
DB_NAME = os.getenv("PG_DB", "postgres")    
DB_USER = os.getenv("PG_USER", "postgres")  
DB_PASSWORD = os.getenv("PG_PASSWORD", "himshruti1976") 
TABLE_NAME = 'voters_enrollment_data'

def connect_db():
    """Establishes and returns a connection to the PostgreSQL database."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"PostgreSQL Connection Error: {e}")
        messagebox.showerror("Connection Error", 
                             f"Failed to connect to PostgreSQL at {DB_HOST}/{DB_NAME}. "
                             "Please check your server status and the password in the script configuration.")
        return None
    except Exception as e:
        print(f"Unexpected DB error: {e}")
        return None

def initialize_database():
    """Connects to the PostgreSQL database and creates the table if it doesn't exist."""
    conn = connect_db()
    if not conn:
        return False, "Failed to initialize: Database connection error."
        
    try:
        cursor = conn.cursor()
    
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id SERIAL PRIMARY KEY, 
                id_number VARCHAR(50) NOT NULL, 
                name VARCHAR(100) NOT NULL,
                father_name VARCHAR(100) NOT NULL,
                college_name VARCHAR(100),
                branch_name VARCHAR(50),
                section VARCHAR(10),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()              
        print(f"PostgreSQL table '{TABLE_NAME}' initialized successfully.")
        return True, "Connected to server."
    except psycopg2.Error as e:
        print(f"PostgreSQL error during initialization: {e}")
        if conn: conn.close()
        return False, f"PostgreSQL Initialization Error: {e}"

def insert_voter_data(data):
    """Inserts a new voter record into the PostgreSQL database."""
    conn = connect_db()
    if not conn:
        return False, "Database connection failed. Check status and credentials."

    try:
        cursor = conn.cursor()
        
        sql = f"""
            INSERT INTO {TABLE_NAME} 
            (id_number, name, father_name, college_name, branch_name, section) 
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        
        cursor.execute(sql, (
            data['id_number'], 
            data['name'], 
            data['father_name'], 
            data['college_name'], 
            data['branch_name'], 
            data['section']
        ))
        
        conn.commit() 
        cursor.close()
        conn.close()
        return True, "Data successfully submitted. Enrollment record saved."
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"PostgreSQL error during insertion: {e}")
        return False, f"PostgreSQL Error: Could not save data. Details: {e}"
    finally:
        if conn:
            conn.close()

class VoterCollectorApp:
    def __init__(self, master, db_status):
        self.master = master
        master.title("Voter Details System")
        master.geometry("800x850") 
        master.configure(bg='#ECEFF1') 

        self.entries = {}
        self.fields = [
            ("Voter ID Number", 'id_number'), 
            ("Applicant's Name", 'name'),
            ("Father's Name", 'father_name'),
            ("Institution/College Name", 'college_name'),
            ("Department/Branch Name", 'branch_name'),
            ("Section/Batch", 'section')
        ]
        
       
        self.style = ttk.Style()
        self.style.theme_use('clam') 

        NAVY_BLUE = '#1A237E'
        SAFFRON_ORANGE = '#FF9800'
        SUCCESS_GREEN = '#4CAF50'
        OFFICIAL_GREY = '#607D8B' 
        BORDER_COLOR = '#90A4AE' 

        self.style.configure('.', font=('Times New Roman', 12)) 
        
        self.style.configure('Official.TFrame', 
                             background='#FFFFFF', 
                             relief='solid', 
                             borderwidth=3, 
                             bordercolor=BORDER_COLOR)
        
        self.style.configure('TLabel', 
                             foreground=NAVY_BLUE, 
                             background='#FFFFFF', 
                             font=('Times New Roman', 11))
        self.style.configure('TEntry', 
                             fieldbackground='#F9F9F9', 
                             foreground='#333333',
                             borderwidth=1,
                             relief='groove') 

        self.style.configure('Primary.TButton', 
                             background=NAVY_BLUE, 
                             foreground='white', 
                             font=('Helvetica', 14, 'bold'), 
                             padding=[25, 12])
        self.style.map('Primary.TButton', 
                        background=[('active', '#0D47A1'), ('!disabled', NAVY_BLUE)],
                        foreground=[('active', 'white'), ('!disabled', 'white')])


        # --- Layout and Structure ---
        
        center_frame = ttk.Frame(master, style='TFrame', padding=20, borderwidth=0)
        center_frame.pack(fill='both', expand=True)

        main_frame = ttk.Frame(center_frame, padding="30 40 30 30", style='Official.TFrame')
        main_frame.pack(pady=30, padx=30, anchor='center', fill='both', expand=True) 

        header_block = tk.Frame(main_frame, bg='#FFFFFF')
        header_block.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 25))
        
        header_block.grid_columnconfigure(0, weight=1) 
        
        # Government Title 
        tk.Label(header_block, 
                 text="GOVERNMENT OF INDIA", 
                 font=("Times New Roman", 16, "bold"), 
                 fg=NAVY_BLUE, 
                 bg='#FFFFFF', 
                 pady=5).grid(row=0, column=0) 
                 
        # Application Title 
        tk.Label(header_block, 
                 text="VOTER DETAILS ENROLLMENT SYSTEM", 
                 font=("Times New Roman", 20, "bold"), 
                 fg=NAVY_BLUE, 
                 bg='#FFFFFF').grid(row=1, column=0, pady=(0, 10))
        
        # /Form Name 
        tk.Label(header_block, 
                 text="FORM I: Applicant Details Submission", 
                 font=("Times New Roman", 14, "bold"), 
                 fg=SAFFRON_ORANGE, 
                 bg='#FFFFFF').grid(row=2, column=0, pady=(0, 20))
        # --- END HEADER BLOCK ---

        # Create form fields
        row_num = 1 
        for label_text, field_key in self.fields:
            
            ttk.Label(main_frame, text=label_text + " *:", 
                      font=('Times New Roman', 12, 'bold')).grid(row=row_num, column=0, sticky='e', padx=(10, 20), pady=12)
             
            entry = ttk.Entry(main_frame, width=50)
            entry.grid(row=row_num, column=1, sticky='ew', padx=10, pady=12)
            
            self.entries[field_key] = entry
            row_num += 1
        
        
        main_frame.grid_columnconfigure(1, weight=1)

        
        db_connected = db_status[0]
        button_state = tk.NORMAL if db_connected else tk.DISABLED
        status_color = SUCCESS_GREEN if db_connected else '#DC3545'

        # Submit Button
        self.submit_button = ttk.Button(main_frame, 
                                        text="Submit Details", 
                                        command=self.submit_form, 
                                        style='Primary.TButton', 
                                        state=button_state)
        self.submit_button.grid(row=row_num, column=0, columnspan=2, pady=(40, 15), sticky='ew', padx=20) 

        # Status Label
        self.status_label = ttk.Label(main_frame, 
                                      text=db_status[1], 
                                      foreground=status_color, 
                                      font=("Times New Roman", 10, "italic"))
        self.status_label.grid(row=row_num + 1, column=0, columnspan=2, pady=5)
        
        # Footer 
        ttk.Label(main_frame, 
                  text="*Mandatory fields. All submissions are subject to verification by the relevant authorities.", 
                  foreground=OFFICIAL_GREY, 
                  font=("Times New Roman", 10, "italic")).grid(row=row_num + 2, column=0, columnspan=2, pady=(15, 0))


    def validate_inputs(self, data):
        """Performs basic validation on required fields and formats."""
        
        required_fields = ['id_number', 'name', 'father_name']
        for key in required_fields:
            if not data.get(key, '').strip():
                display_name = next(f[0] for f in self.fields if f[1] == key)
                return False, f"Error: '{display_name}' is a mandatory field."

        id_number = data['id_number'].strip()
       
        if not re.match(r'^[a-zA-Z0-9_/ -]+$', id_number):
            return False, "Error: Voter ID Number contains invalid characters."
            
        return True, ""

    def submit_form(self):
        """Collects data, validates it, and attempts to insert it into the database."""
        
        voter_data = {key: entry.get().strip() for key, entry in self.entries.items()}
        
        is_valid, message = self.validate_inputs(voter_data)
        
        if not is_valid:
            self.show_status(message, color='#DC3545') # Red error
            messagebox.showerror("Validation Failed", message)
            return

        self.submit_button.config(state=tk.DISABLED, text="Processing Request...")

        success, db_message = insert_voter_data(voter_data)
        
        self.submit_button.config(state=tk.NORMAL, text="Submit Details")
        
        if success:
            self.show_status(db_message, color='#4CAF50') # Green success
            messagebox.showinfo("Success", db_message)
            self.clear_entries()
        else:
            self.show_status(db_message, color='#DC3545') # Red error
            messagebox.showerror("Transaction Failed", db_message)

    def clear_entries(self):
        """Resets all entry fields after a successful submission."""
        for entry in self.entries.values():
            entry.delete(0, tk.END)

    def show_status(self, message, color):
        """Updates the status label with a message and color."""
        self.status_label.config(text=message, foreground=color)
        
        self.master.after(5000, lambda: self.status_label.config(text="")) 

# --- 3. Main Execution Block ---

if __name__ == "__main__":
    db_status = initialize_database() 
    
    root = tk.Tk()
    app = VoterCollectorApp(root, db_status) 
    root.mainloop()