import tkinter as tk
from tkinter import messagebox
import re
# Import the PostgreSQL adapter
import psycopg2 
import sys 
import os 

DB_HOST = os.getenv("PG_HOST", "localhost")  # Default to 'localhost'
DB_NAME = os.getenv("PG_DB", "postgres")    # Default to 'postgres'
DB_USER = os.getenv("PG_USER", "postgres")  # Default to 'postgres'
DB_PASSWORD = os.getenv("PG_PASSWORD", "himshruti1976") # <<< MUST CHANGE THIS to your actual password
TABLE_NAME = 'voters'

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
        # Handle connection failure specifically
        print(f"PostgreSQL Connection Error: {e}")
        # Note: messagebox.showerror will interrupt the main loop on connection error
        messagebox.showerror("Connection Error", 
                             f"Failed to connect to PostgreSQL at {DB_HOST}/{DB_NAME}. "
                             "Please check your server status and the password in the script configuration.")
        return None
    except Exception as e:
        print(f"Unexpected DB error: {e}")
        return None
    
def display_voter_data():
    """Display voter records from the PostgreSQL database."""
    conn = connect_db()
    if not conn:
        return False, "Database connection failed. Check status and credentials."

    try:
        cursor = conn.cursor()
        sql = f"SELECT * FROM {TABLE_NAME};"
        cursor.execute(sql)

        rows = cursor.fetchall()  # ✅ Fetch all rows

        if not rows:
            messagebox.showinfo("Info", "No voter records found in database.")
        else:
            # Print rows in console
            print("Voter Data:")
            for row in rows:
                print(row)
            
            # Optional: show in popup message
            messagebox.showinfo("Voter Data", "\n".join(str(row) for row in rows))

        cursor.close()
        conn.close()
        return True, "Displayed Voter details successfully from PostgreSQL."
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"PostgreSQL Error: {e}")
        return False, f"PostgreSQL Error: {e}"
    finally:
        if conn:
            conn.close()


display_data = display_voter_data()