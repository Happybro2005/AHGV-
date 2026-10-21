import os
import psycopg2
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, init_db, Voter, Election, Candidate, Vote
from services import enroll_voter, authenticate_voter, issue_token, cast_vote, list_results

# --- Database Configuration ---
DB_HOST = os.getenv("PG_HOST", "localhost")
DB_NAME = os.getenv("PG_DB", "postgres")
DB_USER = os.getenv("PG_USER", "postgres")
DB_PASSWORD = os.getenv("PG_PASSWORD", "himshruti1976")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'biovote-dev-secret-key-2026')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Smart DB Selection: PostgreSQL if accessible, SQLite as seamless fallback
use_postgres = False
pg_uri = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}'

try:
    # Quick probe to test if PostgreSQL credentials work
    test_conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=2
    )
    test_conn.close()
    app.config['SQLALCHEMY_DATABASE_URI'] = pg_uri
    use_postgres = True
    print("[BioVote DB] Successfully connected to PostgreSQL server.")
except Exception as e:
    sqlite_db_path = os.path.abspath("voting_system.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_db_path}'
    use_postgres = False
    print(f"[BioVote DB] PostgreSQL unreachable ({e}). Using local SQLite database: {sqlite_db_path}")

db.init_app(app)
init_db(app)

# Auto-seed default election if database is fresh
def seed_default_election():
    with app.app_context():
        if Election.query.count() == 0:
            print("[BioVote Seed] Creating initial Election and Candidates...")
            now = datetime.utcnow()
            election = Election(
                title="National General Election 2026",
                start_at=now - timedelta(days=1),
                end_at=now + timedelta(days=90)
            )
            db.session.add(election)
            db.session.flush()

            candidates = [
                Candidate(election_id=election.id, name="Bharatiya Janata Party (BJP)"),
                Candidate(election_id=election.id, name="Indian National Congress (INC)"),
                Candidate(election_id=election.id, name="Bahujan Samaj Party (BSP)")
            ]
            db.session.add_all(candidates)
            db.session.commit()
            print("[BioVote Seed] Seed complete.")

seed_default_election()

@app.context_processor
def inject_system_status():
    backend_str = "PostgreSQL" if use_postgres else "SQLite (Local)"
    return dict(db_backend=backend_str)

@app.route('/')
def home():
    now = datetime.utcnow()
    # Filter active elections
    elections = Election.query.filter(Election.start_at <= now, Election.end_at >= now).all()
    # If none strictly active, show all scheduled elections
    if not elections:
        elections = Election.query.order_by(Election.id.desc()).all()
    return render_template('home.html', elections=elections)

@app.route('/enroll', methods=['GET', 'POST'])
def enroll():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        reg_no = request.form.get('reg_no', '').strip()
        father_name = request.form.get('father_name', '').strip()
        college_name = request.form.get('college_name', '').strip()
        branch_name = request.form.get('branch_name', '').strip()
        section = request.form.get('section', '').strip()

        file = request.files.get('fingerprint')
        if not file or file.filename == '':
            flash("Please upload a valid fingerprint image file.", 'danger')
            return redirect(url_for('enroll'))
        
        ok, msg = enroll_voter(name, reg_no, father_name, college_name, branch_name, section, file)
        flash(msg, 'success' if ok else 'danger')
        return redirect(url_for('enroll'))
        
    return render_template('enroll.html')

@app.route('/vote/<int:election_id>', methods=['GET', 'POST'])
def vote(election_id):
    election = Election.query.get_or_404(election_id)
    if request.method == 'POST':
        reg_no = request.form.get('reg_no', '').strip()
        file = request.files.get('fingerprint')
        candidate_id_raw = request.form.get('candidate_id')

        if not candidate_id_raw:
            flash("Please select a candidate before casting your vote.", 'danger')
            return redirect(url_for('vote', election_id=election_id))

        if not file or file.filename == '':
            flash("Please upload your fingerprint scan to authenticate.", 'danger')
            return redirect(url_for('vote', election_id=election_id))

        candidate_id = int(candidate_id_raw)

        # 1. Biometric Authentication & Eligibility Check
        ok, msg = authenticate_voter(reg_no, file)
        
        if ok:
            # 2. Get voter record
            voter = Voter.query.filter_by(reg_no=reg_no).first()
            if voter:
                # 3. Cast vote and increment vote_counter
                ok, msg = cast_vote(voter.id, candidate_id)
            else:
                ok, msg = False, "Authentication succeeded, but voter ID not found in database records."
                
        flash(msg, 'success' if ok else 'danger')
        if ok:
            return redirect(url_for('results', election_id=election_id))
        return redirect(url_for('vote', election_id=election_id))
        
    candidates = Candidate.query.filter_by(election_id=election_id).all()
    return render_template('vote.html', election=election, candidates=candidates)

@app.route('/results/<int:election_id>')
def results(election_id):
    election = Election.query.get_or_404(election_id)
    rows = list_results(election_id)
    return render_template('results.html', election=election, rows=rows)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print(f"\n=======================================================")
    print(f"  BIO-VOTE System Running on http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    app.run(host='0.0.0.0', port=port, debug=False)
