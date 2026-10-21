import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk 
import re
import psycopg2 
import os 
import datetime
import time # Added for the timer logic

# --- 1. PostgreSQL Configuration ---
# !!! IMPORTANT: Configure these variables for your PostgreSQL server !!!

DB_HOST = os.getenv("PG_HOST", "localhost") 
DB_NAME = os.getenv("PG_DB", "postgres")    
DB_USER = os.getenv("PG_USER", "postgres")  
DB_PASSWORD = os.getenv("PG_PASSWORD", "himshruti1976") 

# Database Tables for the Two-Step System
TABLE_ENROLLMENT = 'voters_enrollment_data' # Stores Name, Father, College, etc.
TABLE_STATUS = 'voter_status_records'      # Stores ID, Fingerprint (Simulated), VotedStatus
TABLE_TALLY = 'vote_tally'                 # Stores final votes

# --- Global State Definitions ---
STATE_DETAILS_ENTRY = 0
STATE_FINGERPRINT_SCAN = 1
STATE_VOTING_UNIT = 2
STATE_LOCKED = 3

# --- Global Color Palette ---
NAVY_BLUE = '#1A237E'
SAFFRON_ORANGE = '#FF9800'
SUCCESS_GREEN = '#4CAF50'
ERROR_RED = '#DC3545'
OFFICIAL_GREY = '#607D8B' 
BORDER_COLOR = '#90A4AE' 

# --- 2. Database Connection and Setup Functions ---

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
        return None
    except Exception as e:
        print(f"Unexpected DB error: {e}")
        return None

def initialize_database():
    """Connects to the PostgreSQL DB and ensures all three tables exist."""
    conn = connect_db()
    if not conn:
        return False, "Failed to initialize: Database connection error. Check credentials."
        
    try:
        cursor = conn.cursor()
        
        # 1. Enrollment Data Table (for personal detail verification)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_ENROLLMENT} (
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
        
        # 2. Status/Biometric Table (for voting eligibility check)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_STATUS} (
                id_number VARCHAR(50) PRIMARY KEY,
                fingerprint_template BYTEA, -- Simulated Biometric Data
                voted_status BOOLEAN NOT NULL DEFAULT FALSE
            )
        """)

        # 3. Vote Tally Table (for storing cast votes)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_TALLY} (
                vote_id SERIAL PRIMARY KEY, 
                id_number_fk VARCHAR(50) NOT NULL,
                party_id VARCHAR(50) NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # --- MOCK DATA INSERTION (For testing the two-step flow) ---
        # Insert a clean test enrollment record
        cursor.execute(f"""
            INSERT INTO {TABLE_ENROLLMENT} (id_number, name, father_name, college_name, branch_name, section) 
            VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING;
        """, ('TEST_VOTER_1', 'Rajesh Kumar', 'Deepak Kumar', 'City University', 'Computer Science', 'A'))

        # Insert a clean voter status record (Ready to Vote)
        cursor.execute(f"""
            INSERT INTO {TABLE_STATUS} (id_number, fingerprint_template, voted_status) 
            VALUES (%s, %s, %s) ON CONFLICT (id_number) DO NOTHING;
        """, ('TEST_VOTER_1', b'mock_template_1', False))

        conn.commit()
        cursor.close()
        conn.close()              
        print(f"PostgreSQL setup complete. MOCK voter 'TEST_VOTER_1' is ready.")
        return True, "Connected to server. Ready for details entry."
    except psycopg2.Error as e:
        print(f"PostgreSQL error during initialization: {e}")
        if conn: conn.close()
        return False, f"PostgreSQL Initialization Error: {e}"

def find_enrollment_match(data):
    """Checks the Enrollment Table for a match on all six input fields."""
    conn = connect_db()
    if not conn:
        return None, "Database connection failed. Cannot verify details."

    field_keys = ['id_number', 'name', 'father_name', 'college_name', 'branch_name', 'section']
    where_clauses = [f"{key} = %s" for key in field_keys]
    values = tuple(data[key] for key in field_keys)

    try:
        cursor = conn.cursor()
        sql = f"SELECT id_number FROM {TABLE_ENROLLMENT} WHERE {' AND '.join(where_clauses)};"
        
        cursor.execute(sql, values)
        result = cursor.fetchone()
        
        if result:
            return result[0], "Details verified successfully. Proceed to Biometrics."
        else:
            return None, "VERIFICATION FAILED: No matching enrollment record found."
            
    except psycopg2.Error as e:
        print(f"PostgreSQL error during enrollment verification: {e}")
        return None, f"PostgreSQL Error: {e}"
    finally:
        if conn: conn.close()

def check_voted_status(id_number):
    """Simulates biometric match and checks VotedStatus."""
    conn = connect_db()
    if not conn:
        return False, "Database connection failed."

    # NOTE: Biometric hardware integration would happen here. We skip the fingerprint match 
    # and go straight to checking the VotedStatus for the confirmed ID.

    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT voted_status FROM {TABLE_STATUS} WHERE id_number = %s", (id_number,))
        result = cursor.fetchone()
        
        if result is None:
            # If details matched enrollment but no status record exists (e.g., integrity error)
            return False, "Error: Biometric record missing. Contact administration."
        elif result[0] is True:
            # Already voted
            return False, "VOTING BLOCKED: This voter ID has already cast a vote."
        else:
            # Eligible to vote
            return True, "BIOMETRIC VERIFIED. Voting Unit Unlocked for 30 seconds."

    except psycopg2.Error as e:
        print(f"PostgreSQL error during status check: {e}")
        return False, f"PostgreSQL Error: {e}"
    finally:
        if conn: conn.close()

def cast_atomic_vote(id_number, party_id):
    """Executes the vote recording and status update in a single secure transaction."""
    conn = connect_db()
    if not conn:
        return False, "Database connection failed."

    try:
        # Start transaction
        cursor = conn.cursor()
        
        # 1. Update VotedStatus to TRUE (LOCK THE VOTER)
        cursor.execute(f"""
            UPDATE {TABLE_STATUS} 
            SET voted_status = TRUE 
            WHERE id_number = %s AND voted_status = FALSE;
        """, (id_number,))
        
        # Check if the update affected exactly one row (crucial)
        if cursor.rowcount != 1:
            raise psycopg2.IntegrityError("Concurrency error: VotedStatus was not updated correctly.")
        
        # 2. Insert the Vote into the Tally Table (RECORD THE VOTE)
        cursor.execute(f"""
            INSERT INTO {TABLE_TALLY} (id_number_fk, party_id, timestamp) 
            VALUES (%s, %s, %s);
        """, (id_number, party_id, datetime.datetime.now()))
        
        # Commit the transaction (finalize both steps together)
        conn.commit() 
        return True, f"VOTE CONFIRMED: Vote for {party_id} securely recorded."

    except psycopg2.Error as e:
        # Rollback the transaction if any error occurs (e.g., IntegrityError)
        conn.rollback()
        print(f"Atomic Vote Failed: {e}")
        return False, f"VOTE FAILED: Security check failed during submission. Details: {e}"
    finally:
        if conn: cursor.close(); conn.close()

def get_secure_results():
    """Queries the vote tally table and returns vote counts per party."""
    conn = connect_db()
    if not conn:
        return None, "Database connection failed."

    try:
        cursor = conn.cursor()
        # Query to count votes and group by party
        sql = f"""
            SELECT party_id, COUNT(vote_id) as total_votes
            FROM {TABLE_TALLY}
            GROUP BY party_id
            ORDER BY total_votes DESC;
        """
        cursor.execute(sql)
        results = cursor.fetchall()

        # Get total count for percentage calculation
        cursor.execute(f"SELECT COUNT(vote_id) FROM {TABLE_TALLY}")
        total_votes = cursor.fetchone()[0]
        
        return (results, total_votes), "Results retrieved successfully."

    except psycopg2.Error as e:
        print(f"PostgreSQL error during results retrieval: {e}")
        return None, f"Database Error: Could not retrieve results. Details: {e}"
    finally:
        if conn: conn.close()

# --- 3. GUI Application Class ---

class SecureVotingApp:
    def __init__(self, master, db_status):
        self.master = master
        master.title("Biometric Voting Verification Unit")
        master.geometry("800x850") 
        master.configure(bg='#ECEFF1') 

        self.db_connected = db_status[0]
        self.voter_id = None # Stores ID after Step 1 verification
        self.current_state = STATE_DETAILS_ENTRY
        self.timer_id = None
        self.time_left = 30 # 30 seconds for voting
        
        # --- Styling Configuration ---
        self.style = ttk.Style()
        self.style.theme_use('clam') 
        self.style.configure('TLabel', foreground=NAVY_BLUE, background='#FFFFFF', font=('Times New Roman', 11))
        self.style.configure('Primary.TButton', background=NAVY_BLUE, foreground='white', font=('Helvetica', 14, 'bold'), padding=[25, 12])
        self.style.map('Primary.TButton', background=[('active', '#0D47A1'), ('!disabled', NAVY_BLUE)], foreground=[('active', 'white'), ('!disabled', 'white')])

        # --- Base Layout ---
        self.center_frame = ttk.Frame(master, style='TFrame', padding=20, borderwidth=0)
        self.center_frame.pack(fill='both', expand=True)
        self.main_card = ttk.Frame(self.center_frame, padding="30 40 30 30", style='Official.TFrame', width=700)
        self.main_card.pack(pady=30, padx=30, anchor='center', fill='both', expand=False) 

        self.header_label = tk.Label(self.main_card, font=("Times New Roman", 20, "bold"), fg=NAVY_BLUE, bg='#FFFFFF', pady=10)
        self.header_label.grid(row=0, column=0, columnspan=2, sticky='ew')
        
        self.status_label = tk.Label(self.main_card, text=db_status[1], font=("Times New Roman", 12, "italic"), pady=10)
        self.status_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        self.content_frame = tk.Frame(self.main_card, bg='#FFFFFF')
        self.content_frame.grid(row=2, column=0, columnspan=2, sticky='nsew')
        
        # Configure grid weights for centering content
        self.main_card.grid_columnconfigure(0, weight=1)
        self.main_card.grid_columnconfigure(1, weight=1)
        self.main_card.grid_rowconfigure(2, weight=1)

        self.setup_details_entry()

    # --- UI Setup Methods ---

    def setup_details_entry(self):
        """Sets up the initial screen for personal details entry (Step 1)."""
        self.current_state = STATE_DETAILS_ENTRY
        self.clear_frame(self.content_frame)

        self.header_label.config(text="VOTER DETAILS VERIFICATION SYSTEM", fg=NAVY_BLUE)
        self.status_label.config(fg=SUCCESS_GREEN if self.db_connected else ERROR_RED)

        self.entries = {}
        self.fields = [
            ("Voter ID Number", 'id_number'), 
            ("Applicant's Name", 'name'),
            ("Father's Name", 'father_name'),
            ("Institution/College Name", 'college_name'),
            ("Department/Branch Name", 'branch_name'),
            ("Section/Batch", 'section')
        ]
        
        form_frame = ttk.Frame(self.content_frame, padding=10)
        form_frame.pack(padx=20, pady=20, fill='x')
        form_frame.grid_columnconfigure(1, weight=1)

        row_num = 0
        for label_text, field_key in self.fields:
            ttk.Label(form_frame, text=label_text + " *:", 
                      font=('Times New Roman', 12, 'bold')).grid(row=row_num, column=0, sticky='w', padx=(10, 20), pady=12)
            entry = ttk.Entry(form_frame, width=50)
            entry.grid(row=row_num, column=1, sticky='ew', padx=10, pady=12)
            self.entries[field_key] = entry
            row_num += 1

        # Container for the two bottom buttons (Verify and Tally)
        button_container = ttk.Frame(self.content_frame, padding="0 10 0 0")
        button_container.pack(pady=30, fill='x', padx=30)
        button_container.columnconfigure(0, weight=1)
        button_container.columnconfigure(1, weight=1)

        self.verify_button = ttk.Button(button_container, 
                                        text="Verify Details", 
                                        command=self.process_details_verification,
                                        style='Primary.TButton', 
                                        state=tk.NORMAL if self.db_connected else tk.DISABLED)
        self.verify_button.grid(row=0, column=0, padx=10, sticky='ew')

        self.tally_button = ttk.Button(button_container,
                                       text="Show Tally (Admin)",
                                       command=self.show_results_window,
                                       style='Primary.TButton',
                                       state=tk.NORMAL if self.db_connected else tk.DISABLED)
        self.tally_button.grid(row=0, column=1, padx=10, sticky='ew')

    def setup_fingerprint_scan(self):
        """Sets up the screen for simulated fingerprint verification (Step 2)."""
        self.current_state = STATE_FINGERPRINT_SCAN
        self.clear_frame(self.content_frame)

        self.header_label.config(text="IDENTITY CONFIRMED", fg=SUCCESS_GREEN)
        self.status_label.config(text=f"Voter ID: {self.voter_id}. Proceed to Biometric Verification.", fg=NAVY_BLUE)

        # Biometric Area (Simulated)
        tk.Label(self.content_frame, text="SCANNER ACTIVE", font=('Arial', 18, 'bold'), fg='#1A237E', bg='#FFFFFF').pack(pady=(50, 10))
        
        scanner_frame = tk.Frame(self.content_frame, bg='#CCCCCC', height=200, width=200, bd=5, relief=tk.RIDGE)
        scanner_frame.pack(pady=20)
        tk.Label(scanner_frame, text="[ PLACE FINGER HERE ]", font=('Arial', 14), fg='#666666', bg='#CCCCCC').pack(expand=True, padx=20, pady=20)
        
        # EDITED: Changed button text to emphasize the verification step
        scan_button = ttk.Button(self.content_frame, 
                                 text="Simulate Biometric Verification", 
                                 command=self.process_fingerprint_verification,
                                 style='Primary.TButton', 
                                 width=30)
        scan_button.pack(pady=30)

    def setup_voting_unit(self):
        """Sets up the timed voting unit (Step 3)."""
        self.current_state = STATE_VOTING_UNIT
        self.clear_frame(self.content_frame)
        self.time_left = 30
        self.start_timer()

        self.header_label.config(text="AUTHENTICATION SUCCESSFUL", fg=SUCCESS_GREEN)
        
        # Candidate Data
        candidates = [
            ("BJP", "1. VOTE FOR BJP", "#1E90FF"), # Royal Blue
            ("INC", "2. VOTE FOR INC", "#FF4500"), # Orange-Red
            ("BSP", "3. VOTE FOR BSP", "#008000")  # Dark Green
        ]

        # Voting Buttons
        for party_id, party_text, color in candidates:
            button = tk.Button(self.content_frame, 
                                text=party_text, 
                                font=("Arial", 18, "bold"), 
                                bg=color, fg="white", 
                                height=2, width=30, 
                                relief=tk.RAISED, bd=4,
                                command=lambda p=party_id: self.cast_vote(p))
            button.pack(pady=15, padx=50)
            
    # --- State Transition Logic ---
            
    def process_details_verification(self):
        """Handles Step 1: Verification of personal details."""
        voter_data = {key: entry.get().strip() for key, entry in self.entries.items()}
        is_valid, message = self.validate_inputs(voter_data)
        
        if not is_valid:
            self.show_status(message, color=ERROR_RED) 
            messagebox.showerror("Validation Failed", message)
            return

        self.verify_button.config(state=tk.DISABLED, text="Searching Enrollment Records...")

        verified_id, db_message = find_enrollment_match(voter_data)
        
        if verified_id:
            self.voter_id = verified_id
            self.show_status(db_message, color=SUCCESS_GREEN)
            self.setup_fingerprint_scan() # Go to Step 2
        else:
            self.show_status(db_message, color=ERROR_RED)
            messagebox.showerror("Verification Failed", db_message)
            self.verify_button.config(state=tk.NORMAL, text="Verify Details")

    def process_fingerprint_verification(self):
        """Handles Step 2: Simulated Biometric/Status Check."""
        # The software logic performs the check against the database
        self.status_label.config(text="Processing biometric data...", fg=NAVY_BLUE)
        
        is_eligible, message = check_voted_status(self.voter_id)
        
        if is_eligible:
            self.show_status(message, color=SUCCESS_GREEN)
            self.setup_voting_unit() # Go to Step 3: Open voting unit
        else:
            self.show_status(message, color=ERROR_RED)
            messagebox.showerror("Biometric Failed", message)
            self.lock_unit("Biometric Check Failed")

    def cast_vote(self, party_id):
        """Handles Step 3: Atomic vote recording and lock."""
        self.stop_timer()
        self.status_label.config(text="Submitting secure vote...", fg=NAVY_BLUE)
        self.lock_unit("Processing Vote...")
        
        success, message = cast_atomic_vote(self.voter_id, party_id)
        
        if success:
            self.show_status(message, color=SUCCESS_GREEN)
            messagebox.showinfo("VOTE CONFIRMED", message)
        else:
            self.show_status(message, color=ERROR_RED)
            messagebox.showerror("Vote Failed", message)
            
        # Reset the entire system after a successful or failed vote
        self.master.after(5000, self.setup_details_entry)

    # --- Utility Methods ---

    def show_results_window(self):
        """Creates a new administrative window to display current vote totals."""
        results_data, message = get_secure_results()

        if results_data is None:
            messagebox.showerror("Results Error", message)
            return

        results, total_votes = results_data

        # Create new Toplevel window
        results_window = tk.Toplevel(self.master)
        results_window.title("Administrative Vote Tally")
        results_window.geometry("500x400")
        results_window.configure(bg='#F8F8F8')

        tk.Label(results_window, text="OFFICIAL VOTE TALLY", font=("Times New Roman", 18, "bold"), fg=NAVY_BLUE, bg='#F8F8F8').pack(pady=15)
        tk.Label(results_window, text=f"Total Votes Cast: {total_votes}", font=("Times New Roman", 12), fg=OFFICIAL_GREY, bg='#F8F8F8').pack(pady=5)

        if total_votes == 0:
            tk.Label(results_window, text="No votes have been cast yet.", font=("Times New Roman", 14), fg=ERROR_RED, bg='#F8F8F8').pack(pady=40)
            return

        # Results table frame
        table_frame = ttk.Frame(results_window, padding=10)
        table_frame.pack(padx=20, pady=10)

        # Headers
        ttk.Label(table_frame, text="Party ID", font=("Times New Roman", 12, "bold"), anchor='w', width=15).grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(table_frame, text="Votes", font=("Times New Roman", 12, "bold"), width=10).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(table_frame, text="Percentage", font=("Times New Roman", 12, "bold"), width=15).grid(row=0, column=2, padx=5, pady=5)

        # Data rows
        for i, (party_id, votes) in enumerate(results):
            percent = (votes / total_votes) * 100
            row_index = i + 1
            ttk.Label(table_frame, text=party_id, anchor='w').grid(row=row_index, column=0, padx=5, pady=2, sticky='w')
            ttk.Label(table_frame, text=str(votes)).grid(row=row_index, column=1, padx=5, pady=2)
            ttk.Label(table_frame, text=f"{percent:.2f}%").grid(row=row_index, column=2, padx=5, pady=2)

        ttk.Button(results_window, text="Close", command=results_window.destroy).pack(pady=20)
    
    def start_timer(self):
        """Starts the 30-second countdown for the voting unit."""
        if self.time_left > 0 and self.current_state == STATE_VOTING_UNIT:
            self.status_label.config(text=f"Time Left: {self.time_left} seconds. Vote within the limit.", fg=SAFFRON_ORANGE)
            self.time_left -= 1
            self.timer_id = self.master.after(1000, self.start_timer)
        elif self.time_left == 0 and self.current_state == STATE_VOTING_UNIT:
            self.lock_unit("Time Expired. Voting Session Cancelled.")
            messagebox.showwarning("Time Out", "The 30-second time limit expired. Please re-verify to cast your vote.")
            self.master.after(3000, self.setup_details_entry)

    def stop_timer(self):
        """Stops the countdown timer."""
        if self.timer_id:
            self.master.after_cancel(self.timer_id)
            self.timer_id = None

    def lock_unit(self, message):
        """Disables all interactive elements in the voting unit."""
        self.current_state = STATE_LOCKED
        self.stop_timer()
        self.status_label.config(text=message, fg=ERROR_RED)
        
        # Disable all buttons in the content frame
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(state=tk.DISABLED)

    def clear_frame(self, frame):
        """Clears all widgets from a given frame."""
        for widget in frame.winfo_children():
            widget.destroy()

    def validate_inputs(self, data):
        """Performs basic validation on required fields."""
        required_fields = ['id_number', 'name', 'father_name']
        for key in required_fields:
            if not data.get(key, '').strip():
                display_name = next(f[0] for f in self.fields if f[1] == key)
                return False, f"Error: '{display_name}' is a mandatory field."
        return True, ""

    def show_status(self, message, color):
        """Updates the status label with a message and color."""
        self.status_label.config(text=message, fg=color)
        
# --- 4. Main Execution Block ---

if __name__ == "__main__":
    # Check for connection and initialize tables
    db_status = initialize_database() 
    
    root = tk.Tk()
    app = SecureVotingApp(root, db_status) 
    root.mainloop()
