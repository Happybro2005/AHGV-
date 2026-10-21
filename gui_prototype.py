import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import time
import sys
import datetime
import sqlite3

# --- Configuration ---
TIMEOUT_SECONDS = 30
NAVY_BLUE = '#1A237E'
RED_ALERT = '#DC3545'
GREEN_SUCCESS = '#28A745'
LIGHT_BG = '#F5F5F5'

# --- PostgreSQL Configuration (Now using default admin user/db for reliable connection) ---
DB_CONFIG = {
    'host': 'localhost',
    'database': 'postgres',  # Using default database
    'user': 'postgres',      # Using default superuser
    'password': 'himshruti1976' 
}

# --- Database Manager Class ---
try:
    import psycopg2
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False
    print("Warning: psycopg2 not found. Using local SQLite fallback.")


class DatabaseManager:
    """Handles connection and logging votes, favoring PostgreSQL with SQLite fallback."""
    def __init__(self, config):
        self.is_postgres = False
        self.conn = None
        self.cursor = None

        if HAS_POSTGRES:
            # 1. Try PostgreSQL connection
            try:
                self.conn = psycopg2.connect(**config)
                self.conn.autocommit = True
                self.cursor = self.conn.cursor()
                self.is_postgres = True
                print("Database: Connected to PostgreSQL.")
                self._create_tables()
                return
            except Exception as e:
                # Log the failure and fall through to SQLite
                print(f"PostgreSQL connection failed: {e}. Falling back to SQLite.")
                messagebox.showwarning("DB Fallback", 
                                       f"PostgreSQL connection failed. Using local SQLite database.\nError: {e}")

        # 2. Fallback to SQLite (Ensures the app is runnable even without Postgres setup)
        try:
            self.conn = sqlite3.connect('local_votes.db')
            self.cursor = self.conn.cursor()
            self.is_postgres = False
            print("Database: Connected to SQLite.")
            self._create_tables()
        except Exception as e:
            messagebox.showerror("Critical Error", f"Could not connect to or create SQLite database: {e}")
            self.conn = None
            self.cursor = None

    def _create_tables(self):
        """Creates the 'votes' and 'vote_counts' tables."""
        if not self.cursor: return
        
        if self.is_postgres:
            # PostgreSQL Schema:
            sql_create_votes = """
                CREATE TABLE IF NOT EXISTS votes (
                    id SERIAL PRIMARY KEY,
                    party_name VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """
            # This table holds the running total, with party_name as the unique key (PRIMARY KEY)
            sql_create_counts = """
                CREATE TABLE IF NOT EXISTS vote_counts (
                    party_name VARCHAR(50) PRIMARY KEY,
                    total_count INTEGER DEFAULT 0 
                );
            """
        else:
            # SQLite specific schema
            sql_create_votes = """
                CREATE TABLE IF NOT EXISTS votes (
                    id INTEGER PRIMARY KEY,
                    party_name TEXT NOT NULL,
                    timestamp TEXT DEFAULT (datetime('now','localtime'))
                );
            """
            sql_create_counts = """
                CREATE TABLE IF NOT EXISTS vote_counts (
                    party_name TEXT PRIMARY KEY,
                    total_count INTEGER DEFAULT 0
                );
            """
        
        try:
            self.cursor.execute(sql_create_votes)
            self.cursor.execute(sql_create_counts)
            
            if not self.is_postgres:
                 self.conn.commit() # Commit needed for SQLite
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not create tables: {e}")

    def log_vote(self, party_name):
        """
        Inserts a new vote record into the 'votes' table and atomically 
        increments the 'total_count' in the 'vote_counts' table.
        """
        if not self.cursor:
            return False 
        
        # voter_id generation removed as the column is no longer needed.
        
        try:
            # 1. Insert the individual vote (for auditing)
            # SQL statement updated to exclude voter_id
            sql_insert_vote = "INSERT INTO votes (party_name) VALUES (%s);"
            sql_insert_vote_sqlite = "INSERT INTO votes (party_name) VALUES (?);"
            
            if self.is_postgres:
                self.cursor.execute(sql_insert_vote, (party_name,))
            else:
                self.cursor.execute(sql_insert_vote_sqlite, (party_name,))
            
            # 2. Update/Insert the vote count (for total tally)
            if self.is_postgres:
                # PostgreSQL: Uses ON CONFLICT to ensure the party_name is unique and the count increases.
                # SQL updated to use 'total_count'
                self.cursor.execute("""
                    INSERT INTO vote_counts (party_name, total_count)
                    VALUES (%s, 1)
                    ON CONFLICT (party_name) 
                    DO UPDATE SET total_count = vote_counts.total_count + 1;
                """, (party_name,))
            else:
                # SQLite: Manually checks for existence and then Inserts or Updates.
                # SQL updated to use 'total_count'
                self.cursor.execute("SELECT total_count FROM vote_counts WHERE party_name = ?", (party_name,))
                result = self.cursor.fetchone()
                
                if result is None:
                    # Insert new party
                    self.cursor.execute("INSERT INTO vote_counts (party_name, total_count) VALUES (?, 1)", (party_name,))
                else:
                    # Update existing party
                    new_count = result[0] + 1
                    self.cursor.execute("UPDATE vote_counts SET total_count = ? WHERE party_name = ?", (new_count, party_name))

                self.conn.commit() # Commit explicitly for SQLite

            return True
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to log vote: {e}")
            return False

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()

# --- Logo Simulation Class (Unchanged) ---

class LogoCreator:
    """Creates simple, high-contrast colored square placeholders for logos."""
    def __init__(self, master):
        self.master = master
        self.logos = {}

    def get_square_logo(self, color, size=70):
        """Generates a Tkinter PhotoImage object with a solid color."""
        return tk.Frame(self.master, width=size, height=size, bg=color, bd=0)


# --- Voting Machine Application Class ---

class VotingMachineUI:
    def __init__(self, master):
        self.master = master
        master.title("Official Secure Voting Unit")
        master.geometry("800x700")
        master.configure(bg=LIGHT_BG)

        # Initialize Database Manager
        self.db_manager = DatabaseManager(DB_CONFIG)
        if not self.db_manager.conn:
             messagebox.showerror("Critical Error", "Application cannot proceed without a database connection. Please check configurations.")
             sys.exit(1)

        # State management
        self.time_left = TIMEOUT_SECONDS
        self.timer_id = None
        self.vote_cast = False
        
        # Initialize logo creator (for placeholders)
        self.logo_creator = LogoCreator(master)

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('.', font=('Arial', 12))
        
        # --- UI Setup ---
        self.main_frame = tk.Frame(master, bg='#FFFFFF', bd=2, relief=tk.FLAT, highlightbackground='#E0E0E0', highlightthickness=1)
        self.main_frame.pack(pady=40, padx=50, expand=True, fill='both')
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        header_frame = tk.Frame(self.main_frame, bg=NAVY_BLUE, height=60)
        header_frame.grid(row=0, column=0, sticky='ew')
        tk.Label(header_frame, text="✅ AUTHENTICATION SUCCESSFUL", font=("Arial", 18, "bold"), fg='white', bg=NAVY_BLUE, padx=20).pack(side=tk.LEFT, fill=tk.Y)
        self.timer_label = tk.Label(header_frame, text=f"TIME: {TIMEOUT_SECONDS}s", font=("Arial", 18, "bold"), fg='#FFD700', bg=NAVY_BLUE, padx=20)
        self.timer_label.pack(side=tk.RIGHT, fill=tk.Y)
        self.prompt_label = tk.Label(self.main_frame, text="SELECT YOUR CANDIDATE BELOW. UNIT WILL LOCK IN 30 SECONDS.", font=("Arial", 14), fg=RED_ALERT, bg='#FFFFFF')
        self.prompt_label.grid(row=1, column=0, pady=20)
        
        self.button_frame = tk.Frame(self.main_frame, bg='#FFFFFF')
        self.button_frame.grid(row=2, column=0, padx=30, pady=10, sticky='nsew')
        
        self.candidates = [
            ("BJP", "1. VOTE FOR BJP\n(Bharatiya Janta Party)", '#FF9933', '#007bff'),
            ("Congress", "2. VOTE FOR Congress\n(Indian National Congress)", '#4CAF50', '#ffc107'),
            ("BSP", "3. VOTE FOR BSP\n(Bahujan Samaj Party)", '#800080', '#007bff')
        ]

        self.candidate_panels = {}
        for party_name, party_text, logo_color, button_color in self.candidates:
            self.create_party_panel(party_name, party_text, logo_color, button_color)
            
        self.start_timer()

    def create_party_panel(self, party_name, party_text, logo_color, button_color):
        row_frame = tk.Frame(self.button_frame, bd=1, relief=tk.SOLID, background="#F8F8F8")
        row_frame.pack(pady=10, fill=tk.X) 
        
        logo_panel = self.logo_creator.get_square_logo(logo_color, size=70)
        logo_panel.pack(side=tk.LEFT, padx=20, pady=10)
        
        vote_button = tk.Button(
            row_frame, text=party_text, font=("Arial", 18, "bold"), bg=button_color, fg="white", 
            height=3, relief=tk.RAISED, bd=5, activebackground=button_color,
            activeforeground="white", command=lambda: self.cast_vote(party_name)
        )
        vote_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=20, pady=10)
        self.candidate_panels[party_name] = vote_button

    # --- Timer and Lock Logic ---
    def start_timer(self):
        if self.timer_id: self.master.after_cancel(self.timer_id)
        self.time_left = TIMEOUT_SECONDS
        self.update_timer()

    def update_timer(self):
        if self.time_left >= 0:
            color = RED_ALERT if self.time_left <= 10 else '#FFD700'
            self.timer_label.config(text=f"TIME: {self.time_left}s", fg=color)
            self.time_left -= 1
            self.timer_id = self.master.after(1000, self.update_timer)
        else:
            self.lock_unit("Vote time expired! The unit is locked.")

    def lock_unit(self, message):
        if self.timer_id: self.master.after_cancel(self.timer_id); self.timer_id = None
        for button in self.candidate_panels.values():
            button.config(state=tk.DISABLED)
        self.timer_label.config(text="LOCKED", fg=RED_ALERT)
        self.prompt_label.config(text=message, fg=NAVY_BLUE)
        messagebox.showwarning("Unit Locked", message)

    # --- Vote Submission ---

    def cast_vote(self, party_name):
        if self.vote_cast: return 
        self.vote_cast = True
        
        success = self.db_manager.log_vote(party_name)
        
        if success:
            self.lock_unit("VOTE SUCCESSFULLY RECORDED.")
            
            db_type = "PostgreSQL" if self.db_manager.is_postgres else "SQLite"
            
            messagebox.showinfo("VOTE CONFIRMED", 
                                f"Your vote for {party_name} has been securely recorded and stored in the {db_type} database. Thank you.\n\n"
                                "The system is now resetting for the next voter.")
            
            self.master.after(5000, self.reset_unit)
        else:
            self.vote_cast = False 
            messagebox.showerror("Database Failure", "Failed to record vote. Please contact a poll official.")
            self.lock_unit("CRITICAL ERROR: Vote recording failed.")


    def reset_unit(self):
        """Simulates the unit resetting for the next voter and closes DB connection."""
        self.db_manager.close() 
        
        messagebox.showinfo("System Reset", "Unit is now reset and ready for the next verification.")
        self.master.destroy()
        
# --- E. Start the GUI Event Loop ---
if __name__ == '__main__':
    # Ensure psycopg2 or sqlite3 can be used
    if not HAS_POSTGRES and not hasattr(sys.modules['__main__'], 'sqlite3'):
        print("Required libraries (psycopg2 or sqlite3) are missing.")
        sys.exit(1)

    root = tk.Tk()
    app = VotingMachineUI(root)
    root.mainloop()
