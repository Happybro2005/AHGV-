from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Voter(db.Model):
    # Mapping to your existing PostgreSQL table
    __tablename__ = 'voters_enrollment_data' 
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Matching the enrollment fields (using 'id_number' as the unique registration number)
    reg_no = db.Column('id_number', db.String, unique=True, nullable=False)
    name = db.Column('name', db.String, nullable=False)
    father_name = db.Column('father_name', db.String)
    college_name = db.Column('college_name', db.String)
    branch_name = db.Column('branch_name', db.String)
    section = db.Column('section', db.String)
    
    # New column for vote control
    vote_counter = db.Column('vote_counter', db.Integer, default=0) 

    # Biometric Template and Timestamp:
    template = db.Column(db.LargeBinary) # Stores the fingerprint features
    created_at = db.Column('timestamp', db.DateTime, default=datetime.utcnow)

class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=False)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id', ondelete='CASCADE'))
    name = db.Column(db.String, nullable=False)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'))
    voter_id = db.Column(db.Integer, db.ForeignKey('voters_enrollment_data.id')) # Link to the new table name
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    cast_at = db.Column(db.DateTime, default=datetime.utcnow)

def init_db(app):
    with app.app_context():
        # WARNING: This will try to create/update tables. 
        # If your PostgreSQL user lacks permission, or if tables already exist, 
        # run ALTER TABLE commands manually.
        db.create_all()
