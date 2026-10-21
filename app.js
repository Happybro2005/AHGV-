/**
 * BioVote - Client-Side Biometric Voting Engine
 * Complete standalone simulation compatible with GitHub Pages.
 */

// --- Default Demo State ---
const DEFAULT_CANDIDATES = [
    { id: 1, name: "Bharatiya Janata Party (BJP)", code: "BJP", logo: "static/images/party_a_logo.png", color: "#f97316" },
    { id: 2, name: "Indian National Congress (INC)", code: "INC", logo: "static/images/party_b_logo.png", color: "#10b981" },
    { id: 3, name: "Bahujan Samaj Party (BSP)", code: "BSP", logo: "static/images/party_c_logo.png", color: "#3b82f6" }
];

const DEFAULT_VOTERS = [
    {
        name: "Shruti Jain",
        reg_no: "2401640100996",
        father_name: "Himanshu Jain",
        college_name: "PSIT Kanpur",
        branch_name: "Computer Science",
        section: "Section P",
        fingerprint_name: "voter1_fingerprint.png",
        fingerprint_sig: "voter_1_signature",
        has_voted: false,
        voted_at: null
    },
    {
        name: "Prashant Singh",
        reg_no: "2401641520131",
        father_name: "Ram Singh",
        college_name: "PSIT Kanpur",
        branch_name: "Information Technology",
        section: "Section A",
        fingerprint_name: "voter2_fingerprint.png",
        fingerprint_sig: "voter_2_signature",
        has_voted: false,
        voted_at: null
    }
];

const DEFAULT_VOTES = [
    { id: 1, candidate_id: 1, timestamp: "2026-10-21 14:15:00" },
    { id: 2, candidate_id: 1, timestamp: "2026-10-21 14:18:22" },
    { id: 3, candidate_id: 1, timestamp: "2026-10-21 14:22:10" },
    { id: 4, candidate_id: 2, timestamp: "2026-10-21 14:30:45" },
    { id: 5, candidate_id: 2, timestamp: "2026-10-21 14:35:12" },
    { id: 6, candidate_id: 3, timestamp: "2026-10-21 14:40:05" }
];

// --- Storage Controller ---
const DB = {
    getVoters() {
        const stored = localStorage.getItem('biovote_voters');
        return stored ? JSON.parse(stored) : DEFAULT_VOTERS;
    },
    saveVoters(voters) {
        localStorage.setItem('biovote_voters', JSON.stringify(voters));
    },
    getCandidates() {
        return DEFAULT_CANDIDATES;
    },
    getVotes() {
        const stored = localStorage.getItem('biovote_votes');
        return stored ? JSON.parse(stored) : DEFAULT_VOTES;
    },
    saveVotes(votes) {
        localStorage.setItem('biovote_votes', JSON.stringify(votes));
    },
    reset() {
        localStorage.removeItem('biovote_voters');
        localStorage.removeItem('biovote_votes');
        initData();
        showToast('Database reset to clean demo state.', 'success');
        renderApp();
    }
};

function initData() {
    if (!localStorage.getItem('biovote_voters')) {
        DB.saveVoters(DEFAULT_VOTERS);
    }
    if (!localStorage.getItem('biovote_votes')) {
        DB.saveVotes(DEFAULT_VOTES);
    }
}

// --- Navigation View Switcher ---
function navigateTo(viewId) {
    window.location.hash = viewId;
}

function handleRoute() {
    const hash = window.location.hash.replace('#', '') || 'home';
    const validViews = ['home', 'enroll', 'booth', 'results'];
    const activeView = validViews.includes(hash) ? hash : 'home';

    document.querySelectorAll('.view-panel').forEach(panel => {
        panel.style.display = 'none';
    });
    const targetPanel = document.getElementById(`view-${activeView}`);
    if (targetPanel) {
        targetPanel.style.display = 'block';
    }

    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-view') === activeView) {
            link.classList.add('active');
        }
    });

    if (activeView === 'results') {
        renderResults();
    } else if (activeView === 'booth') {
        startBoothTimer();
    } else {
        stopBoothTimer();
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

window.addEventListener('hashchange', handleRoute);

// --- Toast Alerts ---
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.innerHTML = `
        <div class="alert-icon">
            ${type === 'success' ? 
                '<svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2.5" fill="none"><polyline points="20 6 9 17 4 12"></polyline></svg>' : 
                '<svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2.5" fill="none"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'}
        </div>
        <div class="alert-text">${message}</div>
        <button class="alert-close" onclick="this.parentElement.remove();">&times;</button>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        if (toast.parentElement) toast.remove();
    }, 6000);
}

// --- Booth Countdown Timer ---
let boothSeconds = 60;
let boothTimerInterval = null;

function startBoothTimer() {
    stopBoothTimer();
    boothSeconds = 60;
    const display = document.getElementById('timer-display');
    if (display) {
        display.textContent = '60s';
        display.style.color = '#3b82f6';
    }

    boothTimerInterval = setInterval(() => {
        boothSeconds--;
        if (display) {
            display.textContent = `${boothSeconds}s`;
            if (boothSeconds <= 15) {
                display.style.color = '#ef4444';
            }
        }
        if (boothSeconds <= 0) {
            stopBoothTimer();
            alert('Voting session timed out for security. Returning to main portal.');
            navigateTo('home');
        }
    }, 1000);
}

function stopBoothTimer() {
    if (boothTimerInterval) {
        clearInterval(boothTimerInterval);
        boothTimerInterval = null;
    }
}

// --- Biometric Feature Extraction Simulation (Canvas Minutiae) ---
function analyzeFingerprintCanvas(imageSrc, canvasId, callback) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.crossOrigin = 'anonymous';

    img.onload = function() {
        canvas.width = 160;
        canvas.height = 200;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        // Generate synthetic minutiae points across fingerprint ridges
        const minutiaePoints = [];
        const seedVal = Math.floor(canvas.width * canvas.height);
        for (let i = 0; i < 28; i++) {
            const x = 30 + Math.floor((Math.sin(i * 13 + seedVal) * 0.5 + 0.5) * 100);
            const y = 30 + Math.floor((Math.cos(i * 17 + seedVal) * 0.5 + 0.5) * 140);
            minutiaePoints.push({ x, y, angle: (i * 45) % 360 });

            // Draw glowing green minutiae marker
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fillStyle = '#10b981';
            ctx.fill();

            // Draw orientation direction line
            ctx.beginPath();
            ctx.moveTo(x, y);
            const dx = Math.cos((i * 45 * Math.PI) / 180) * 8;
            const dy = Math.sin((i * 45 * Math.PI) / 180) * 8;
            ctx.lineTo(x + dx, y + dy);
            ctx.strokeStyle = '#34d399';
            ctx.lineWidth = 1.5;
            ctx.stroke();
        }

        if (callback) callback(minutiaePoints);
    };

    img.src = imageSrc;
}

// --- Biometric Matcher (ORB + Hamming Distance Simulation) ---
function matchProbeWithEnrolled(voter, probeFilename) {
    // If voter registered with voter1 and probe is voter1_probe.png, match score is 34 (Threshold: 15)
    if (voter.fingerprint_name && voter.fingerprint_name.includes('voter1') && probeFilename.includes('voter1_probe')) {
        return { isMatch: true, score: 34, message: "Biometric Fingerprint Verified (ORB Match Score: 34 / Threshold: 15)" };
    }
    // If probe matches exact filename or signature
    if (voter.fingerprint_name === probeFilename) {
        return { isMatch: true, score: 38, message: "Biometric Template Matched (ORB Match Score: 38 / Threshold: 15)" };
    }
    // Mismatch case (e.g. voter 2 probe vs voter 1)
    if (probeFilename.includes('voter2') || probeFilename.includes('invalid') || probeFilename.includes('mismatch')) {
        return { isMatch: false, score: 4, message: "Biometric Verification Failed (ORB Match Score: 4 < Required Threshold: 15)" };
    }
    // Default fallback for custom uploads
    return { isMatch: true, score: 26, message: "Biometric Feature Correlated (ORB Match Score: 26 / Threshold: 15)" };
}

// --- State Handlers for Views ---

// 1. Enrollment Form Handler
function handleEnrollSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const name = form.name.value.trim();
    const reg_no = form.reg_no.value.trim();
    const father_name = form.father_name.value.trim();
    const college_name = form.college_name.value.trim();
    const branch_name = form.branch_name.value.trim();
    const section = form.section.value.trim();
    const fpName = form.getAttribute('data-fp-name') || 'custom_fingerprint.png';

    if (!name || !reg_no || !father_name) {
        showToast('Please fill out all required demographic fields.', 'danger');
        return;
    }

    const voters = DB.getVoters();
    if (voters.find(v => v.reg_no.toLowerCase() === reg_no.toLowerCase())) {
        showToast(`Registration failed: Voter ID "${reg_no}" is already enrolled.`, 'danger');
        return;
    }

    const newVoter = {
        name,
        reg_no,
        father_name,
        college_name: college_name || "PSIT",
        branch_name: branch_name || "CSE",
        section: section || "P",
        fingerprint_name: fpName,
        fingerprint_sig: "sig_" + Date.now(),
        has_voted: false,
        voted_at: null
    };

    voters.push(newVoter);
    DB.saveVoters(voters);

    showToast(`Successfully enrolled voter: ${name} (ID: ${reg_no})!`, 'success');
    form.reset();
    resetEnrollPreview();
    navigateTo('home');
}

function resetEnrollPreview() {
    const prompt = document.getElementById('enroll-dropzone-prompt');
    const preview = document.getElementById('enroll-file-preview-wrap');
    if (prompt) prompt.style.display = 'block';
    if (preview) preview.style.display = 'none';
}

function loadSampleEnrollFingerprint() {
    const form = document.getElementById('enroll-form');
    form.setAttribute('data-fp-name', 'voter1_fingerprint.png');
    
    const previewImg = document.getElementById('enroll-preview-img');
    const previewWrap = document.getElementById('enroll-file-preview-wrap');
    const prompt = document.getElementById('enroll-dropzone-prompt');
    const fileNameSpan = document.getElementById('enroll-file-name');

    if (previewImg && previewWrap && prompt) {
        previewImg.src = 'sample_data/fingerprints/voter1_fingerprint.png';
        if (fileNameSpan) fileNameSpan.textContent = 'voter1_fingerprint.png (Sample)';
        prompt.style.display = 'none';
        previewWrap.style.display = 'flex';
        analyzeFingerprintCanvas('sample_data/fingerprints/voter1_fingerprint.png', 'enroll-canvas');
        showToast('Loaded sample fingerprint template: voter1_fingerprint.png', 'info');
    }
}

// 2. Voting Booth Handler
function handleVoteSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const reg_no = form.reg_no.value.trim();
    const selectedCandidate = form.querySelector('input[name="candidate_id"]:checked');
    const probeFilename = form.getAttribute('data-probe-name') || 'voter1_probe.png';

    if (!reg_no) {
        showToast('Please enter your registered Voter ID.', 'danger');
        return;
    }
    if (!selectedCandidate) {
        showToast('Please select a candidate on the ballot.', 'danger');
        return;
    }

    const voters = DB.getVoters();
    const voter = voters.find(v => v.reg_no.toLowerCase() === reg_no.toLowerCase());

    if (!voter) {
        showToast(`Authentication Error: Voter ID "${reg_no}" not found in enrollment records.`, 'danger');
        return;
    }

    if (voter.has_voted) {
        showToast(`Access Denied: Voter ID "${reg_no}" has already cast a ballot. One-voter-one-vote lock active.`, 'danger');
        return;
    }

    // Match Biometrics
    const matchResult = matchProbeWithEnrolled(voter, probeFilename);
    if (!matchResult.isMatch) {
        showToast(matchResult.message, 'danger');
        return;
    }

    // Cast Vote
    const candidateId = parseInt(selectedCandidate.value, 10);
    const votes = DB.getVotes();
    votes.push({
        id: votes.length + 1,
        candidate_id: candidateId,
        timestamp: new Date().toISOString()
    });
    DB.saveVotes(votes);

    // Lock Voter
    voter.has_voted = true;
    voter.voted_at = new Date().toISOString();
    DB.saveVoters(voters);

    stopBoothTimer();
    showToast(`Vote Successfully Recorded! Authenticated via Biometrics (${matchResult.message}).`, 'success');
    form.reset();
    resetBoothPreview();
    navigateTo('results');
}

function resetBoothPreview() {
    const prompt = document.getElementById('booth-prompt');
    const preview = document.getElementById('booth-preview');
    if (prompt) prompt.style.display = 'block';
    if (preview) preview.style.display = 'none';
}

function loadSampleBoothProbe(probeType) {
    const form = document.getElementById('vote-form');
    let filename = 'voter1_probe.png';
    let label = 'voter1_probe.png (Matching Probe)';

    if (probeType === 'mismatch') {
        filename = 'voter2_fingerprint.png';
        label = 'voter2_fingerprint.png (Mismatch Probe)';
    }

    form.setAttribute('data-probe-name', filename);
    const thumb = document.getElementById('booth-thumb');
    const nameEl = document.getElementById('booth-filename');
    const prompt = document.getElementById('booth-prompt');
    const preview = document.getElementById('booth-preview');

    if (thumb && nameEl && prompt && preview) {
        thumb.src = `sample_data/fingerprints/${filename}`;
        nameEl.textContent = label;
        prompt.style.display = 'none';
        preview.style.display = 'flex';
        analyzeFingerprintCanvas(`sample_data/fingerprints/${filename}`, 'booth-canvas');
        showToast(`Loaded ${label}`, probeType === 'mismatch' ? 'danger' : 'info');
    }
}

function fillDemoVoter(regNo) {
    const input = document.getElementById('reg_no');
    if (input) {
        input.value = regNo;
        showToast(`Auto-filled Voter ID: ${regNo}`, 'info');
    }
}

// 3. Results View Renderer
function renderResults() {
    const candidates = DB.getCandidates();
    const votes = DB.getVotes();
    const totalVotes = votes.length;

    // Tally votes per candidate
    const counts = {};
    candidates.forEach(c => { counts[c.id] = 0; });
    votes.forEach(v => {
        if (counts[v.candidate_id] !== undefined) {
            counts[v.candidate_id]++;
        }
    });

    // Update Top Metric Cards
    const totalEl = document.getElementById('metric-total-votes');
    if (totalEl) totalEl.textContent = totalVotes;

    const candCountEl = document.getElementById('metric-candidate-count');
    if (candCountEl) candCountEl.textContent = candidates.length;

    // Render list
    const listContainer = document.getElementById('results-tally-list');
    if (!listContainer) return;

    // Sort by count descending
    const sorted = [...candidates].sort((a, b) => counts[b.id] - counts[a.id]);

    let html = '';
    sorted.forEach((cand, idx) => {
        const count = counts[cand.id] || 0;
        const percent = totalVotes > 0 ? ((count / totalVotes) * 100).toFixed(1) : '0.0';
        html += `
            <div class="tally-item">
                <div class="tally-info">
                    <div class="candidate-meta">
                        <span class="rank-tag">#${idx + 1}</span>
                        <img src="${cand.logo}" alt="${cand.code}" style="width:28px; height:28px; object-fit:contain; border-radius:4px;" onerror="this.style.display='none'">
                        <strong class="tally-cand-name">${cand.name}</strong>
                    </div>
                    <div class="tally-numbers">
                        <span class="vote-count">${count} vote${count !== 1 ? 's' : ''}</span>
                        <span class="vote-percent">${percent}%</span>
                    </div>
                </div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: ${percent}%; background: ${cand.color || 'var(--primary)'};"></div>
                </div>
            </div>
        `;
    });

    listContainer.innerHTML = html;
}

// --- App Initialization ---
function renderApp() {
    initData();
    handleRoute();
}

document.addEventListener('DOMContentLoaded', () => {
    renderApp();

    const enrollForm = document.getElementById('enroll-form');
    if (enrollForm) enrollForm.addEventListener('submit', handleEnrollSubmit);

    const voteForm = document.getElementById('vote-form');
    if (voteForm) voteForm.addEventListener('submit', handleVoteSubmit);
});
