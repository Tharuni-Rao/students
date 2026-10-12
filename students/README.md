# EduPulse AI — Smart Campus Analytics & Student Success Platform

EduPulse AI is a full-stack prototype that combines academic, attendance, LMS, skills, and placement data into a unified student profile and exposes a transparent student success score, risk explanation, intervention workflow, and a what-if simulator.

## Features

- Unified student profile across academic, attendance, LMS, engagement, and placement signals
- Student Success Score from 0–100 with weighted, configurable factors
- Separate academic and placement risk logic with explainable triggers
- Student segmentation and intervention engine
- Role-based demo access for administrator, faculty, placement officer, and student views
- CSV/JSON import validation and preview summary
- Scenario simulator for attendance and assessment adjustments
- Synthetic dataset of 120+ students across multiple departments

## Demo roles

- Administrator: admin / admin123
- Faculty: faculty / faculty123
- Placement Officer: placement / placement123
- Student: student / student123

## Local setup (Windows)

### 1) Frontend

```powershell
cd "c:\Users\rishwith kumar\OneDrive\Desktop\students\frontend"
$env:PATH = "C:\Program Files\nodejs;$env:PATH"
& "C:\Program Files\nodejs\npm.cmd" install
& "C:\Program Files\nodejs\npm.cmd" run dev -- --host 0.0.0.0
```

The app runs at http://localhost:5173/

### 2) Backend

```powershell
cd "c:\Users\rishwith kumar\OneDrive\Desktop\students\backend"
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API runs at http://localhost:8000/

## Project structure

- frontend/ — React + Vite dashboard UI
- backend/app/main.py — FastAPI app, seeded records, analytics, import validation, endpoints
- backend/data/students.json — generated synthetic student dataset
- docs/ — methodology, architecture, demo, limitations

## Core API endpoints

- GET /api/health
- POST /api/login
- GET /api/dashboard
- GET /api/students
- GET /api/students/{student_id}
- GET /api/segments
- GET /api/score-config
- POST /api/score-config
- POST /api/scenario
- POST /api/import

## Scoring formula

The Student Success Score uses a weighted blend of the six components:

- Academic performance: 30%
- Attendance: 20%
- LMS engagement: 15%
- Skills development: 15%
- Placement readiness: 15%
- Engagement: 5%

The score is calculated from normalized 0–100 component scores with clear rule-based risk indicators. Missing data is treated conservatively and flagged as incomplete instead of being silently converted into poor performance.

## Responsible AI notes

This is a prototype built on synthetic data and is intended for educational decision support, not automatic disciplinary, scholarship, or placement decisions.

## Hackathon presentation outline

1. Campus data is fragmented and support is often reactive
2. EduPulse AI unifies campus signals into one profile
3. Explainable score + risk rules show why support is needed
4. Interventions and what-if analysis turn insights into actions
5. Demonstrate import, dashboard, profile review, and simulation

## Limitations

- This is a synthetic, hackathon-grade prototype, not a production student system
- Real deployment would require secure authentication and governed data access
- Historical labeled outcomes would be needed for validated predictive ML models
