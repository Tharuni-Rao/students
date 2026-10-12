from __future__ import annotations

import csv
import io
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

random.seed(42)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "students.json"

DEMO_USERS = {
    "admin": {"role": "Administrator", "name": "Aisha Khan", "password": "admin123"},
    "faculty": {"role": "Faculty", "name": "Rohan Mehta", "password": "faculty123"},
    "placement": {"role": "Placement Officer", "name": "Neha Verma", "password": "placement123"},
    "student": {"role": "Student", "name": "Sneha Iyer", "password": "student123"},
}

SCORE_WEIGHTS = {
    "academic": 30,
    "attendance": 20,
    "lms": 15,
    "skills": 15,
    "placement": 15,
    "engagement": 5,
}

RISK_CONFIG = {
    "attendance_threshold": 75,
    "academic_threshold": 60,
    "cgpa_threshold": 6.0,
    "aptitude_threshold": 60,
    "coding_threshold": 55,
    "interview_threshold": 60,
    "assignment_threshold": 60,
    "backlog_threshold": 2,
}


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def average(values: List[float]) -> float:
    values = [safe_float(v, 0.0) for v in values if v is not None]
    if not values:
        return 0.0
    return sum(values) / len(values)


def normalize_score(value: float, minimum: float, maximum: float) -> float:
    if maximum <= minimum:
        return 0.0
    return clamp(((value - minimum) / (maximum - minimum)) * 100)


def calculate_completeness(student: Dict[str, Any]) -> float:
    fields = [
        "cgpa",
        "internal_assessment",
        "attendance",
        "assignment_completion",
        "lms_logins_per_week",
        "aptitude",
        "coding",
        "mock_interview",
        "communication_assessment",
        "technical_skill",
        "problem_solving",
        "teamwork",
    ]
    present = 0
    for field in fields:
        if student.get(field) is not None:
            present += 1
    return round((present / len(fields)) * 100, 1)


def compute_component_scores(student: Dict[str, Any]) -> Dict[str, float]:
    academic = clamp((safe_float(student.get("cgpa", 0.0)) / 10.0) * 70 + safe_float(student.get("internal_assessment", 0.0)) * 0.3, 0.0, 100.0)
    attendance = safe_float(student.get("attendance", 0.0))
    lms = clamp(
        safe_float(student.get("assignment_completion", 0.0)) * 0.7
        + min(safe_float(student.get("lms_logins_per_week", 0.0)) * 8, 100) * 0.3,
        0.0,
        100.0,
    )
    skills = average([
        safe_float(student.get("technical_skill", 0.0)),
        safe_float(student.get("problem_solving", 0.0)),
        safe_float(student.get("teamwork", 0.0)),
        safe_float(student.get("communication_assessment", 0.0)),
    ])
    placement = average([
        safe_float(student.get("aptitude", 0.0)),
        safe_float(student.get("coding", 0.0)),
        safe_float(student.get("mock_interview", 0.0)),
        safe_float(student.get("resume_readiness", 0.0)),
        safe_float(student.get("communication_assessment", 0.0)),
    ])
    engagement = clamp(
        average([
            safe_float(student.get("event_participation", 0.0)),
            safe_float(student.get("club_participation", 0.0)),
            safe_float(student.get("hackathons_attended", 0.0)) * 10,
            safe_float(student.get("certifications_completed", 0.0)) * 12,
            safe_float(student.get("project_participation", 0.0)),
        ]),
        0.0,
        100.0,
    )
    return {
        "academic": round(academic, 1),
        "attendance": round(attendance, 1),
        "lms": round(lms, 1),
        "skills": round(skills, 1),
        "placement": round(placement, 1),
        "engagement": round(engagement, 1),
    }


def evaluate_risk(student: Dict[str, Any]) -> Dict[str, Any]:
    attendance_threshold = RISK_CONFIG["attendance_threshold"]
    academic_threshold = RISK_CONFIG["academic_threshold"]
    cgpa_threshold = RISK_CONFIG["cgpa_threshold"]
    apt_threshold = RISK_CONFIG["aptitude_threshold"]
    coding_threshold = RISK_CONFIG["coding_threshold"]
    interview_threshold = RISK_CONFIG["interview_threshold"]
    assignment_threshold = RISK_CONFIG["assignment_threshold"]
    backlog_threshold = RISK_CONFIG["backlog_threshold"]

    academic_triggers: List[str] = []
    if safe_float(student.get("attendance", 0.0)) < attendance_threshold:
        academic_triggers.append(f"Attendance {student.get('attendance', 0)}% is below {attendance_threshold}%")
    if safe_float(student.get("internal_assessment", 0.0)) < academic_threshold:
        academic_triggers.append(f"Internal assessment {student.get('internal_assessment', 0)}% is below {academic_threshold}%")
    if safe_float(student.get("cgpa", 0.0)) < cgpa_threshold:
        academic_triggers.append(f"CGPA {student.get('cgpa', 0)} is below {cgpa_threshold}")
    if safe_float(student.get("backlog_count", 0.0)) >= backlog_threshold:
        academic_triggers.append(f"Backlog count {student.get('backlog_count', 0)} meets the concern threshold")
    if safe_float(student.get("assignment_completion", 0.0)) < assignment_threshold:
        academic_triggers.append(f"Assignment completion {student.get('assignment_completion', 0)}% is below {assignment_threshold}%")
    if safe_float(student.get("performance_trend", 0.0)) < 0:
        academic_triggers.append("Recent performance trend is declining")

    placement_triggers: List[str] = []
    if safe_float(student.get("aptitude", 0.0)) < apt_threshold:
        placement_triggers.append(f"Aptitude score {student.get('aptitude', 0)}% is below {apt_threshold}%")
    if safe_float(student.get("coding", 0.0)) < coding_threshold:
        placement_triggers.append(f"Coding score {student.get('coding', 0)}% is below {coding_threshold}%")
    if safe_float(student.get("mock_interview", 0.0)) < interview_threshold:
        placement_triggers.append(f"Mock interview score {student.get('mock_interview', 0)}% is below {interview_threshold}%")
    if safe_float(student.get("resume_readiness", 0.0)) < 65:
        placement_triggers.append("Resume readiness is below the recommended standard")
    if safe_float(student.get("communication_assessment", 0.0)) < 60:
        placement_triggers.append("Communication assessment indicates a skill gap")

    academic_risk = "Low"
    if len(academic_triggers) >= 3:
        academic_risk = "High"
    elif len(academic_triggers) >= 1:
        academic_risk = "Moderate"

    placement_risk = "Low"
    if len(placement_triggers) >= 3:
        placement_risk = "High"
    elif len(placement_triggers) >= 1:
        placement_risk = "Moderate"

    return {
        "academic_risk": academic_risk,
        "placement_risk": placement_risk,
        "academic_triggers": academic_triggers,
        "placement_triggers": placement_triggers,
    }


def classify_segments(student: Dict[str, Any]) -> List[str]:
    segments: List[str] = []
    score = safe_float(student.get("success_score", 0.0))
    academic = safe_float(student.get("components", {}).get("academic", 0.0))
    placement = safe_float(student.get("components", {}).get("placement", 0.0))
    attendance = safe_float(student.get("attendance", 0.0))
    engagement = safe_float(student.get("components", {}).get("engagement", 0.0))
    if academic >= 80 and placement >= 80:
        segments.append("Strong Academics + Strong Placement Readiness")
    if academic >= 80 and placement < 55:
        segments.append("Strong Academics + Low Placement Readiness")
    if academic < 60 and engagement >= 70:
        segments.append("Low Academics + Strong Engagement")
    if attendance < 70 and academic < 65:
        segments.append("Low Attendance + Academic Concern")
    if engagement >= 70 and safe_float(student.get("performance_trend", 0.0)) > 0:
        segments.append("Strong Engagement + Improving Performance")
    if safe_float(student.get("aptitude", 0.0)) < 60 or safe_float(student.get("coding", 0.0)) < 60 or safe_float(student.get("communication_assessment", 0.0)) < 60:
        segments.append("Placement Skill Gaps")
    if safe_float(student.get("backlog_count", 0.0)) >= 2 or academic < 50:
        segments.append("Multiple Backlogs or Significant Academic Concern")
    if calculate_completeness(student) < 70:
        segments.append("Incomplete Data — Assessment Required")
    return segments or ["General Support Track"]


def recommend_interventions(student: Dict[str, Any]) -> List[Dict[str, Any]]:
    interventions: List[Dict[str, Any]] = []
    if safe_float(student.get("attendance", 0.0)) < 75:
        interventions.append({
            "title": "Attendance Recovery Plan",
            "role": "Faculty",
            "priority": "High",
            "status": "Suggested",
            "description": "Schedule a check-in and attendance recovery plan with the student before the next progress review.",
        })
    if safe_float(student.get("internal_assessment", 0.0)) < 60 or safe_float(student.get("cgpa", 0.0)) < 6:
        interventions.append({
            "title": "Academic Mentorship",
            "role": "Faculty",
            "priority": "High",
            "status": "Assigned",
            "description": "Assign mentoring and targeted revision sessions for courses with falling performance.",
        })
    if safe_float(student.get("assignment_completion", 0.0)) < 60:
        interventions.append({
            "title": "LMS Follow-Up",
            "role": "Faculty",
            "priority": "Medium",
            "status": "In Progress",
            "description": "Support LMS engagement with reminders, resource recommendations, and assignment checklists.",
        })
    if safe_float(student.get("aptitude", 0.0)) < 60 or safe_float(student.get("coding", 0.0)) < 60:
        interventions.append({
            "title": "Placement Preparation Sprint",
            "role": "Placement Officer",
            "priority": "High",
            "status": "Suggested",
            "description": "Recommend aptitude drills, coding practice sets, and mock interviews tailored to the role objective.",
        })
    if safe_float(student.get("communication_assessment", 0.0)) < 60:
        interventions.append({
            "title": "Communication Skills Workshop",
            "role": "Placement Officer",
            "priority": "Medium",
            "status": "Suggested",
            "description": "Provide guided communication coaching and structured practice for interview readiness.",
        })
    if not interventions:
        interventions.append({
            "title": "Positive Growth Track",
            "role": "Faculty",
            "priority": "Low",
            "status": "Completed",
            "description": "Maintain current momentum and monitor improvement over the next assessment cycle.",
        })
    return interventions


def build_student_record(student: Dict[str, Any]) -> Dict[str, Any]:
    components = compute_component_scores(student)
    score = (
        0.30 * components["academic"]
        + 0.20 * components["attendance"]
        + 0.15 * components["lms"]
        + 0.15 * components["skills"]
        + 0.15 * components["placement"]
        + 0.05 * components["engagement"]
    )
    student = {**student, "components": components, "success_score": round(score, 1)}
    risks = evaluate_risk(student)
    student.update(risks)
    student["segments"] = classify_segments(student)
    student["interventions"] = recommend_interventions(student)
    student["data_completeness"] = calculate_completeness(student)
    return student


def generate_demo_students() -> List[Dict[str, Any]]:
    departments = ["Computer Science", "Electronics", "Mechanical", "MBA", "Civil", "Electrical"]
    names = [
        "Aarav", "Ananya", "Riya", "Vihaan", "Meera", "Kabir", "Nisha", "Ishaan", "Tanvi", "Arjun",
        "Saanvi", "Dhruv", "Priya", "Yash", "Neha", "Rohit", "Aditi", "Karan", "Pooja", "Harsh",
        "Ira", "Aditya", "Mira", "Kush", "Diya", "Om", "Srushti", "Dev", "Tara", "Shivam",
    ]
    students: List[Dict[str, Any]] = []
    student_counter = 1
    for dept_index, dept in enumerate(departments):
        for year in [1, 2, 3, 4]:
            for student_idx in range(20):
                name = names[(student_counter + student_idx) % len(names)]
                attendance = random.randint(52, 97)
                internal = random.randint(42, 94)
                cgpa = round(random.uniform(4.2, 9.4), 2)
                backlog_count = random.randint(0, 3)
                assignment_completion = random.randint(35, 98)
                lms_login = random.randint(1, 8)
                aptitude = random.randint(35, 96)
                coding = random.randint(40, 97)
                mock = random.randint(30, 95)
                resume = random.randint(45, 100)
                communication = random.randint(35, 96)
                technical = random.randint(40, 95)
                problem = random.randint(38, 96)
                teamwork = random.randint(44, 95)
                engagement = random.randint(25, 95)
                event = random.randint(0, 90)
                club = random.randint(0, 70)
                hack = random.randint(0, 4)
                cert = random.randint(0, 5)
                project = random.randint(0, 80)
                performance_trend = round(random.uniform(-15, 18), 1)

                if dept == "MBA":
                    attendance = random.randint(60, 96)
                    internal = random.randint(55, 95)
                    cgpa = round(random.uniform(5.2, 9.2), 2)
                if year == 1 and dept_index % 2 == 0:
                    attendance += 5

                if student_counter % 11 == 0:
                    attendance -= 18
                    internal -= 18
                    cgpa = max(4.0, cgpa - 0.8)
                    assignment_completion -= 20
                    aptitude -= 15
                    coding -= 12
                if student_counter % 17 == 0:
                    assignment_completion = max(30, assignment_completion - 10)
                    communication = max(30, communication - 10)
                    resume = max(30, resume - 15)

                student = {
                    "student_id": f"EDU{student_counter:04d}",
                    "name": f"{name} {student_counter}",
                    "department": dept,
                    "degree": "B.Tech" if dept not in ["MBA"] else "MBA",
                    "year": year,
                    "semester": (year - 1) * 2 + 1,
                    "cgpa": round(max(2.0, min(9.8, cgpa)), 2),
                    "internal_assessment": max(0, min(100, internal)),
                    "backlog_count": backlog_count,
                    "attendance": max(0, min(100, attendance)),
                    "assignment_completion": max(0, min(100, assignment_completion)),
                    "lms_logins_per_week": lms_login,
                    "event_participation": max(0, min(100, event)),
                    "club_participation": max(0, min(100, club)),
                    "hackathons_attended": hack,
                    "certifications_completed": cert,
                    "project_participation": max(0, min(100, project)),
                    "aptitude": max(0, min(100, aptitude)),
                    "coding": max(0, min(100, coding)),
                    "mock_interview": max(0, min(100, mock)),
                    "resume_readiness": max(0, min(100, resume)),
                    "communication_assessment": max(0, min(100, communication)),
                    "technical_skill": max(0, min(100, technical)),
                    "problem_solving": max(0, min(100, problem)),
                    "teamwork": max(0, min(100, teamwork)),
                    "engagement_score": max(0, min(100, engagement)),
                    "performance_trend": round(performance_trend, 1),
                    "insights": "Synthetic demo record generated for hackathon demonstration.",
                    "last_updated": datetime.utcnow().isoformat(),
                }
                students.append(build_student_record(student))
                student_counter += 1

    if not DATA_PATH.parent.exists():
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(students, indent=2), encoding="utf-8")
    return students


def get_demo_students() -> List[Dict[str, Any]]:
    if DATA_PATH.exists():
        try:
            data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return data
        except Exception:
            pass
    return generate_demo_students()


def build_dashboard_payload(students: List[Dict[str, Any]], filters: Dict[str, Any]) -> Dict[str, Any]:
    filtered = list(students)
    if filters.get("department") and filters["department"] != "All":
        filtered = [s for s in filtered if s["department"] == filters["department"]]
    if filters.get("year") and filters["year"] != "All":
        filtered = [s for s in filtered if str(s["year"]) == str(filters["year"])]
    if filters.get("semester") and filters["semester"] != "All":
        filtered = [s for s in filtered if str(s["semester"]) == str(filters["semester"])]
    if filters.get("segment") and filters["segment"] != "All":
        filtered = [s for s in filtered if filters["segment"] in s.get("segments", [])]
    if filters.get("academic_risk") and filters["academic_risk"] != "All":
        filtered = [s for s in filtered if s.get("academic_risk") == filters["academic_risk"]]
    if filters.get("placement_risk") and filters["placement_risk"] != "All":
        filtered = [s for s in filtered if s.get("placement_risk") == filters["placement_risk"]]
    if filters.get("score_min") is not None:
        filtered = [s for s in filtered if s.get("success_score", 0) >= float(filters["score_min"])]
    if filters.get("score_max") is not None:
        filtered = [s for s in filtered if s.get("success_score", 0) <= float(filters["score_max"])]

    kpis = {
        "total_students": len(filtered),
        "average_score": round(average([s.get("success_score", 0) for s in filtered]), 1),
        "high_academic_risk": sum(1 for s in filtered if s.get("academic_risk") == "High"),
        "placement_concerns": sum(1 for s in filtered if s.get("placement_risk") in {"Moderate", "High"}),
        "average_attendance": round(average([s.get("attendance", 0) for s in filtered]), 1),
        "incomplete_data": sum(1 for s in filtered if s.get("data_completeness", 100) < 70),
        "open_interventions": sum(1 for s in filtered for i in s.get("interventions", []) if i.get("status") in {"Suggested", "Assigned", "In Progress"}),
    }

    score_distribution = [
        {"name": "Strong (80-100)", "value": sum(1 for s in filtered if 80 <= s.get("success_score", 0) <= 100)},
        {"name": "Developing (65-79)", "value": sum(1 for s in filtered if 65 <= s.get("success_score", 0) <= 79)},
        {"name": "Needs attention (50-64)", "value": sum(1 for s in filtered if 50 <= s.get("success_score", 0) <= 64)},
        {"name": "Priority support (<50)", "value": sum(1 for s in filtered if s.get("success_score", 0) < 50)},
    ]

    risk_distribution = [
        {"name": "Low", "value": sum(1 for s in filtered if s.get("academic_risk") == "Low")},
        {"name": "Moderate", "value": sum(1 for s in filtered if s.get("academic_risk") == "Moderate")},
        {"name": "High", "value": sum(1 for s in filtered if s.get("academic_risk") == "High")},
    ]

    department_data = []
    departments = sorted({s["department"] for s in filtered})
    for dept in departments:
        dept_students = [s for s in filtered if s["department"] == dept]
        department_data.append({
            "department": dept,
            "avgScore": round(average([s.get("success_score", 0) for s in dept_students]), 1),
            "students": len(dept_students),
        })

    attendance_by_academic = [
        {"attendance": round(s.get("attendance", 0), 1), "academic": round(s.get("components", {}).get("academic", 0), 1), "name": s["name"]}
        for s in filtered[:30]
    ]

    lms_by_academic = [
        {"lms": round(s.get("components", {}).get("lms", 0), 1), "academic": round(s.get("components", {}).get("academic", 0), 1), "name": s["name"]}
        for s in filtered[:30]
    ]

    trend_data = []
    for semester in sorted({s["semester"] for s in filtered}):
        semester_students = [s for s in filtered if s["semester"] == semester]
        trend_data.append({
            "semester": f"Sem {semester}",
            "score": round(average([s.get("success_score", 0) for s in semester_students]), 1),
        })

    intervention_status = [
        {"name": status, "value": sum(1 for s in filtered for i in s.get("interventions", []) if i.get("status") == status)}
        for status in ["Suggested", "Assigned", "In Progress", "Completed"]
    ]

    return {
        "kpis": kpis,
        "score_distribution": score_distribution,
        "risk_distribution": risk_distribution,
        "department_performance": department_data,
        "attendance_vs_academic": attendance_by_academic,
        "lms_vs_academic": lms_by_academic,
        "semester_trend": trend_data,
        "placement_by_department": [
            {
                "department": dept,
                "avgPlacement": round(average([s.get("components", {}).get("placement", 0) for s in filtered if s["department"] == dept]), 1),
            }
            for dept in departments
        ],
        "intervention_status": intervention_status,
        "student_list": filtered,
    }


class LoginRequest(BaseModel):
    role: str
    password: str


app = FastAPI(title="EduPulse AI", version="1.0.0")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/login")
def login(payload: LoginRequest):
    user = DEMO_USERS.get(payload.role.lower())
    if not user:
        raise HTTPException(status_code=404, detail="Unknown role")
    if payload.password != user["password"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": f"demo-token-{payload.role}", "user": {"role": user["role"], "name": user["name"], "id": payload.role.lower()}}


@app.get("/api/demo-roles")
def demo_roles():
    return {"roles": [{"id": key, "name": value["role"], "label": f"{value['role']} Demo"} for key, value in DEMO_USERS.items()]}


@app.get("/api/students")
def get_students(
    department: Optional[str] = None,
    year: Optional[str] = None,
    semester: Optional[str] = None,
    segment: Optional[str] = None,
    academic_risk: Optional[str] = None,
    placement_risk: Optional[str] = None,
    score_min: Optional[float] = None,
    score_max: Optional[float] = None,
):
    students = get_demo_students()
    filters = {
        "department": department,
        "year": year,
        "semester": semester,
        "segment": segment,
        "academic_risk": academic_risk,
        "placement_risk": placement_risk,
        "score_min": score_min,
        "score_max": score_max,
    }
    payload = build_dashboard_payload(students, filters)
    return payload["student_list"]


@app.get("/api/dashboard")
def get_dashboard(
    department: Optional[str] = None,
    year: Optional[str] = None,
    semester: Optional[str] = None,
    segment: Optional[str] = None,
    academic_risk: Optional[str] = None,
    placement_risk: Optional[str] = None,
    score_min: Optional[float] = None,
    score_max: Optional[float] = None,
):
    students = get_demo_students()
    filters = {
        "department": department,
        "year": year,
        "semester": semester,
        "segment": segment,
        "academic_risk": academic_risk,
        "placement_risk": placement_risk,
        "score_min": score_min,
        "score_max": score_max,
    }
    return build_dashboard_payload(students, filters)


@app.get("/api/students/{student_id}")
def get_student(student_id: str):
    for student in get_demo_students():
        if student["student_id"].lower() == student_id.lower():
            return student
    raise HTTPException(status_code=404, detail="Student not found")


@app.get("/api/segments")
def get_segments():
    students = get_demo_students()
    segment_counts = {}
    for student in students:
        for segment in student.get("segments", []):
            segment_counts[segment] = segment_counts.get(segment, 0) + 1
    return [{"name": key, "count": value} for key, value in sorted(segment_counts.items())]


@app.get("/api/score-config")
def get_score_config():
    return {"weights": SCORE_WEIGHTS, "bands": [
        {"label": "Strong current indicators", "min": 80, "max": 100},
        {"label": "Developing", "min": 65, "max": 79},
        {"label": "Needs attention", "min": 50, "max": 64},
        {"label": "Priority support", "min": 0, "max": 49},
    ]}


@app.post("/api/score-config")
def update_score_config(payload: Dict[str, float]):
    total = sum(payload.values())
    if total <= 0:
        raise HTTPException(status_code=400, detail="Weights must sum to a positive number")
    if any(value < 0 for value in payload.values()):
        raise HTTPException(status_code=400, detail="Weights cannot be negative")
    for key in SCORE_WEIGHTS:
        SCORE_WEIGHTS[key] = float(payload.get(key, SCORE_WEIGHTS[key]))
    if round(sum(SCORE_WEIGHTS.values()), 2) != 100.0:
        raise HTTPException(status_code=400, detail="Weights must sum to 100%")
    return {"weights": SCORE_WEIGHTS}


@app.post("/api/scenario")
def scenario_analysis(payload: Dict[str, Any]):
    student_id = payload.get("student_id")
    for student in get_demo_students():
        if student["student_id"] == student_id:
            scenario = dict(student)
            for key, value in payload.get("changes", {}).items():
                if key in scenario:
                    scenario[key] = value
            scenario = build_student_record(scenario)
            return {
                "current_score": student["success_score"],
                "simulated_score": scenario["success_score"],
                "difference": round(scenario["success_score"] - student["success_score"], 1),
                "changes": scenario["components"],
                "risk": {"academic_risk": scenario["academic_risk"], "placement_risk": scenario["placement_risk"]},
                "explanation": f"The updated scenario shifts the student from {student['success_score']} to {scenario['success_score']} based on adjusted performance indicators.",
            }
    raise HTTPException(status_code=404, detail="Student not found")


@app.post("/api/import")
async def import_data(file: UploadFile = File(...)):
    content = await file.read()
    records: List[Dict[str, Any]] = []
    try:
        if file.filename.endswith(".json"):
            parsed = json.loads(content.decode("utf-8"))
            if isinstance(parsed, list):
                records = parsed
            else:
                records = parsed.get("students", [])
        else:
            text = content.decode("utf-8")
            file_obj = io.StringIO(text)
            reader = csv.DictReader(file_obj)
            records = list(reader)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=f"Invalid file format: {exc}") from exc

    valid_records = []
    invalid_rows = []
    for index, row in enumerate(records, start=1):
        try:
            normalized = {
                "student_id": row.get("student_id") or row.get("Student ID") or row.get("id"),
                "name": row.get("name") or row.get("Name") or f"Imported Student {index}",
                "department": row.get("department") or row.get("Department") or "General",
                "cgpa": safe_float(row.get("cgpa"), 0.0),
                "internal_assessment": safe_float(row.get("internal_assessment"), 0.0),
                "attendance": safe_float(row.get("attendance"), 0.0),
                "assignment_completion": safe_float(row.get("assignment_completion"), 0.0),
                "aptitude": safe_float(row.get("aptitude"), 0.0),
                "coding": safe_float(row.get("coding"), 0.0),
                "mock_interview": safe_float(row.get("mock_interview"), 0.0),
                "resume_readiness": safe_float(row.get("resume_readiness"), 0.0),
                "communication_assessment": safe_float(row.get("communication_assessment"), 0.0),
            }
            if not normalized["student_id"]:
                raise ValueError("Missing student_id")
            valid_records.append(build_student_record(normalized))
        except Exception as exc:  # pragma: no cover
            invalid_rows.append({"row": index, "error": str(exc)})

    return {
        "valid_records": len(valid_records),
        "invalid_rows": len(invalid_rows),
        "rejected": invalid_rows,
        "preview": valid_records[:5],
        "summary": "Import reviewed successfully with validation checks and duplicate detection postponed to the server storage layer.",
    }


@app.get("/api/exports/risk-summary")
def export_risk_summary():
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "summary": [
            {"risk": "Low", "count": sum(1 for s in get_demo_students() if s.get("academic_risk") == "Low")},
            {"risk": "Moderate", "count": sum(1 for s in get_demo_students() if s.get("academic_risk") == "Moderate")},
            {"risk": "High", "count": sum(1 for s in get_demo_students() if s.get("academic_risk") == "High")},
        ],
    }


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
