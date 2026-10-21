import psycopg2
import datetime

# --- CONFIGURATION (MUST BE UPDATED) ---
# NOTE: The Tkinter app will pull these from its global environment variables (os.getenv)
DB_NAME = "evm_db"  
DB_USER = "evm_user" 
DB_PASS = "himshruti1976" # <--- UPDATE THIS LINE
DB_HOST = "localhost"
VOTER_ID = 'TEST_VOTER_1' # Mock ID for simulation

# --- 1. Connection Function ---
def connect_db():
    """Establishes and returns a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST
        )
        return conn
    except psycopg2.Error as e:
        print(f"FATAL: Database Connection Error. Check DB service and credentials: {e}")
        return None

# --- 2. Table Setup Function (Run Once) ---
def setup_tables(conn):
    """Creates the Voter_Registry and Vote_Tally tables if they do not exist."""
    cursor = conn.cursor()
    
    # Voter_Registry: Stores ID, Fingerprint (BYTEA), and Status (BOOLEAN)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Voter_Registry (
            VoterID TEXT PRIMARY KEY,
            FingerprintTemplate BYTEA NOT NULL, 
            VotedStatus BOOLEAN NOT NULL 
        );
    """)

    # Vote_Tally: Stores the actual vote record and links back to the voter
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Vote_Tally (
            VoteID SERIAL PRIMARY KEY, 
            VoterID_FK TEXT NOT NULL,
            PartyID TEXT NOT NULL,
            Timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            FOREIGN KEY (VoterID_FK) REFERENCES Voter_Registry(VoterID)
        );
    """)
    
    # Insert a CLEAN voter (VotedStatus=False) for testing the UI
    try:
        cursor.execute("""
            INSERT INTO Voter_Registry (VoterID, FingerprintTemplate, VotedStatus) 
            VALUES (%s, %s, %s) ON CONFLICT (VoterID) DO NOTHING;
        """, (VOTER_ID, b'mock_template_1', False))
        conn.commit()
        print(f"Test Voter '{VOTER_ID}' ensured in registry (Status: False).")
    except psycopg2.Error as e:
        print(f"Error inserting test data: {e}")
        conn.rollback()

    conn.commit()
    cursor.close()
    return True, "DB CONNECTED | Ready"

# --- 3. Status Check Function (Core Security Logic - Simulated Biometric Check) ---
def check_voted_status(conn, voter_id):
    """Checks the database to determine a voter's eligibility status."""
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT VotedStatus FROM Voter_Registry WHERE VoterID = %s", 
            (voter_id,)
        )
        status = cursor.fetchone()
        
        if status is None:
            # Voter ID not found (Simulating failed Aadhaar/Fingerprint verification)
            return "NOT_REGISTERED", "Verification failed: Voter ID not found in registry."
        elif status[0] is True:
            # Status is True (Already Voted)
            return "ALREADY_VOTED", "Voter has already cast their vote."
        else:
            # Status is False (Clean, Ready to Vote)
            return "READY_TO_VOTE", "Verification successful. Proceed to vote."
            
    except psycopg2.Error as e:
        print(f"Database Query Error during status check: {e}")
        return "DB_ERROR", f"Database error during eligibility check: {e}"
    finally:
        cursor.close()

# --- 4. The Atomic Voting Function (Most Important Security) ---
def cast_atomic_vote(conn, voter_id, party_id):
    """Executes the vote recording and status update in a single transaction."""
    cursor = conn.cursor()
    
    try:
        # Start transaction block
        cursor.execute("BEGIN;")
        
        # 4a. Update the Voter_Registry Status
        cursor.execute("""
            UPDATE Voter_Registry
            SET VotedStatus = TRUE
            WHERE VoterID = %s AND VotedStatus = FALSE
        """, (voter_id,))
        
        # Check if the update was successful (i.e., status was FALSE before update)
        if cursor.rowcount != 1:
            conn.rollback()
            return False, "Security fail: Voter already marked as Voted, or ID not found."
            
        # 4b. Record the Vote in the Vote_Tally table
        cursor.execute("""
            INSERT INTO Vote_Tally (VoterID_FK, PartyID, Timestamp)
            VALUES (%s, %s, %s)
        """, (voter_id, party_id, datetime.datetime.now()))
        
        # Commit both operations (update and insert) together
        conn.commit()
        return True, "Vote successfully recorded and status locked."
        
    except psycopg2.Error as e:
        conn.rollback() # Rollback the transaction on any failure
        print(f"FATAL: Transaction failed. Rolling back changes. Error: {e}")
        return False, f"FATAL ERROR: Vote transaction failed. {e}"
    finally:
        cursor.close()

# --- 5. Get Secure Results ---
def get_secure_results(conn):
    """Queries the database and returns a dictionary of candidate vote counts."""
    cursor = conn.cursor()
    
    try:
        # SQL to count votes grouped by candidate (PartyID)
        sql = f"""
            SELECT PartyID, COUNT(VoteID) 
            FROM Vote_Tally
            GROUP BY PartyID 
            ORDER BY COUNT(VoteID) DESC;
        """
        cursor.execute(sql)
        results = dict(cursor.fetchall())
        return results, "Results fetched successfully."
        
    except psycopg2.Error as e:
        print(f"PostgreSQL error during results query: {e}")
        return None, f"Database Error: Could not retrieve results. {e}"
    finally:
        cursor.close()
        
# --- INITIAL RUN BLOCK (For testing) ---
if __name__ == '__main__':
    connection = connect_db()
    if connection:
        setup_tables(connection)
        connection.close()
