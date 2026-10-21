import cv2
import numpy as np
import pickle
from models import db, Voter, Vote, Candidate
from datetime import datetime
import os, secrets

def extract_features(file):
    """Extracts ORB features (keypoints and descriptors) from a fingerprint image file."""
    try:
        # Read file stream bytes into numpy array
        img_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(img_bytes, cv2.IMREAD_GRAYSCALE)
        
        # Ensure image is loaded and valid
        if img is None or img.size == 0:
            return None
        
        # Use ORB feature detector
        orb = cv2.ORB_create()
        keypoints, descriptors = orb.detectAndCompute(img, None)
        
        # Ensure descriptors are found
        if descriptors is None:
            return None
            
        # ORB descriptors are typically float32; convert to uint8 for NORM_HAMMING matching
        if descriptors.dtype != np.uint8:
            descriptors = np.uint8(descriptors)
            
        return descriptors
        
    except Exception as e:
        print(f"Error extracting features: {e}")
        return None

def match_features(desc1, desc2):
    """Matches two sets of feature descriptors using BFMatcher."""
    # Ensure descriptors are valid and of the correct type
    if desc1 is None or desc2 is None or desc1.size == 0 or desc2.size == 0:
        return 0
        
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(desc1, desc2)
    return len(matches)

def enroll_voter(name, reg_no, father_name, college_name, branch_name, section, file):
    """Enrolls a voter with all metadata and their fingerprint template."""
    
    # 1. Extract fingerprint features
    desc = extract_features(file)
    if desc is None:
        return False, "Invalid or unusable fingerprint image. Enrollment failed."
        
    # 2. Check for duplicate registration number
    voter = Voter.query.filter_by(reg_no=reg_no).first()
    if voter:
        return False, "Voter ID already enrolled."
        
    # 3. Create new voter record
    voter = Voter(
        name=name, 
        reg_no=reg_no, 
        father_name=father_name, 
        college_name=college_name,
        branch_name=branch_name,
        section=section,
        template=desc.dumps() # Serialize numpy array to binary string
    )
    db.session.add(voter)
    db.session.commit()
    return True, "Voter enrolled successfully."

def authenticate_voter(reg_no, file):
    """Authenticates voter by matching fingerprint and checking vote eligibility."""
    
    # 1. Extract probe fingerprint features
    desc_probe = extract_features(file)
    if desc_probe is None:
        return False, "Failed to read the fingerprint from scanner."

    # 2. Find voter record
    voter = Voter.query.filter_by(reg_no=reg_no).first()
    if not voter:
        return False, "Voter ID not found in enrollment records."
    
    # 3. Check vote counter (ELIGIBILITY CHECK)
    if voter.vote_counter > 0:
        return False, "This Voter ID has already cast a vote (Access Denied)."
        
    # 4. Match features
    try:
        desc_db = pickle.loads(voter.template)
    except Exception as e:
        print(f"Error deserializing template: {e}")
        return False, "Corrupted biometric template in database."
    score = match_features(desc_db, desc_probe)
    
    # Threshold for a successful match
    MATCH_THRESHOLD = 15 # Adjust this based on testing
    is_authenticated = (score > MATCH_THRESHOLD)
    
    return (is_authenticated, "Authenticated (Score: {})".format(score) if is_authenticated else "Authentication failed. Score: {}".format(score))

# The issue_token function is no longer strictly needed for a single user, 
# but we keep it for framework completeness.
def issue_token(reg_no, election_id):
    """Simulates issuing a short-lived token (used for framework compatibility)."""
    return secrets.token_hex(16)

def cast_vote(voter_id, candidate_id):
    """Records the vote and increments the vote_counter for the voter."""
    
    # 1. Get objects
    candidate = Candidate.query.get(candidate_id)
    voter = Voter.query.get(voter_id) 

    if not candidate:
        return False, "Candidate not found."
    if not voter:
        return False, "Voter record not found."
    if voter.vote_counter > 0:
        return False, "Voter is ineligible (already voted)."

    # 2. Record the vote
    vote = Vote(election_id=candidate.election_id, voter_id=voter_id, candidate_id=candidate_id)
    db.session.add(vote)

    # 3. Increment the vote counter (CRITICAL STEP)
    voter.vote_counter += 1 
    
    db.session.commit()
    return True, "Vote cast successfully and counter updated."

def list_results(election_id):
    """Lists election results."""
    rows = db.session.query(Candidate.name, db.func.count(Vote.id)).join(Vote, Candidate.id==Vote.candidate_id, isouter=True).filter(Candidate.election_id==election_id).group_by(Candidate.name).all()
    return rows
