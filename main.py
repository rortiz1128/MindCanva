import os
from datetime import datetime, timezone
from typing import List, Optional, Literal

from fastapi import FastAPI, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "dev-key-change-me")

# -------- Security (simple API key in header) --------
def require_api_key(x_api_key: str = Header(default=None, alias="X-API-Key")):
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
    return True

app = FastAPI(
    title="MindCanvas Teacher Actions",
    version="1.0.0",
    description="API for educational planning, assessment, and analytics actions used by MindCanvas.",
    contact={"name": "MindCanvas", "url": "https://chatgpt.com/g/g-6810c3ef6f90819186228fd4196113b3-mindcanvas"},
)

# --------- Models ---------
class LessonPlanReq(BaseModel):
    subject: str
    grade_level: str
    standards: Optional[List[str]] = None
    duration_minutes: int = Field(ge=15)
    learning_objectives: Optional[List[str]] = None
    differentiation: Optional[bool] = False

class LessonPlanResp(BaseModel):
    lesson_plan: dict

class QuizReq(BaseModel):
    topic: str
    grade_level: Optional[str] = None
    question_types: List[Literal["mcq", "true_false", "short_answer"]]
    num_questions: int = Field(ge=1, le=50)
    difficulty: Optional[Literal["easy", "medium", "hard", "mixed"]] = "mixed"
    include_rationales: Optional[bool] = False

class QuizResp(BaseModel):
    questions: List[dict]
    answer_key: List[str]

class RubricLevel(BaseModel):
    label: str
    points: float
    descriptor: Optional[str] = None

class RubricCriterion(BaseModel):
    criterion: str
    levels: List[RubricLevel]
    weight: Optional[float] = Field(default=1.0, ge=0)

class GradeWithRubricReq(BaseModel):
    rubric: List[RubricCriterion]
    student_response: str
    max_total_points: Optional[float] = None

class GradeWithRubricResp(BaseModel):
    total_points: float
    criteria: List[dict]
    feedback: str

class MapObjectivesReq(BaseModel):
    frameworks: Optional[List[Literal["CCSS", "NGSS", "TEKS", "CA-ELA", "CA-Math", "Other"]]] = None
    objectives: List[str]

class MapObjectivesResp(BaseModel):
    mappings: List[dict]

class AvailabilityBlock(BaseModel):
    start_iso: str
    end_iso: str

class ScheduleConferenceReq(BaseModel):
    student_name: str
    guardians: List[str]
    preferred_modalities: Optional[List[Literal["in_person", "zoom", "phone"]]] = None
    teacher_availability_blocks: List[AvailabilityBlock]
    language: Optional[str] = "English"

class ScheduleConferenceResp(BaseModel):
    proposals: List[dict]
    invite_draft: str

class ProgressEntry(BaseModel):
    date: str
    standard: str
    score: float = Field(ge=0)
    max_score: float = Field(gt=0)
    assessment_type: Optional[Literal["quiz", "project", "exit_ticket", "test", "other"]] = "other"
    notes: Optional[str] = None

class TrackProgressReq(BaseModel):
    student_id: str
    entries: List[ProgressEntry]
    rollup_window: Optional[Literal["unit", "quarter", "semester", "year"]] = "unit"

class TrackProgressResp(BaseModel):
    mastery: List[dict]

class AnalyzeExitReq(BaseModel):
    prompt: str
    responses: List[str]
    num_groups: Optional[int] = Field(default=3, ge=2, le=8)
    return_exemplars_per_group: Optional[int] = Field(default=1, ge=0, le=5)

class AnalyzeExitResp(BaseModel):
    groups: List[dict]
    misconceptions: List[str]

# --------- Helpers (toy logic; replace with real) ---------
def now_iso():
    return datetime.now(timezone.utc).isoformat()

def simple_mcq(i: int, topic: str):
    return {
        "id": f"Q{i+1}",
        "type": "mcq",
        "stem": f"Which statement about {topic} is correct?",
        "choices": ["A", "B", "C", "D"],
        "answer": "A",
    }

# --------- Endpoints ---------
@app.post("/create-lesson-plan", response_model=LessonPlanResp, dependencies=[Depends(require_api_key)])
def create_lesson_plan(body: LessonPlanReq):
    plan = {
        "meta": {
            "generated_at": now_iso(),
            "subject": body.subject,
            "grade_level": body.grade_level,
            "duration_minutes": body.duration_minutes,
            "standards": body.standards or [],
        },
        "objectives": body.learning_objectives or ["Students will ..."],
        "materials": ["Projector", "Slides", "Handout"],
        "sequence": [
            {"phase": "Do Now", "minutes": 5, "activity": "Warm-up prompt"},
            {"phase": "Mini-lesson", "minutes": 15, "activity": "Direct instruction"},
            {"phase": "Guided Practice", "minutes": 20, "activity": "Partner work"},
            {"phase": "Independent Practice", "minutes": body.duration_minutes - 45, "activity": "Task"},
            {"phase": "Exit Ticket", "minutes": 5, "activity": "Quick check"},
        ],
        "assessment": {"type": "exit_ticket", "criteria": ["Accuracy", "Reasoning"]},
        "differentiation": {"enabled": bool(body.differentiation), "notes": "Scaffolds and extensions suggested."},
    }
    return {"lesson_plan": plan}

@app.post("/generate-quiz", response_model=QuizResp, dependencies=[Depends(require_api_key)])
def generate_quiz(body: QuizReq):
    qs = []
    ak = []
    for i in range(body.num_questions):
        qt = body.question_types[i % len(body.question_types)]
        if qt == "mcq":
            q = simple_mcq(i, body.topic)
            qs.append(q)
            ak.append(q["answer"])
        elif qt == "true_false":
            qs.append({"id": f"Q{i+1}", "type": "true_false", "stem": f"{body.topic}: True or False?", "answer": True})
            ak.append("True")
        else:  # short_answer
            qs.append({"id": f"Q{i+1}", "type": "short_answer", "stem": f"Briefly explain {body.topic}."})
            ak.append("<free-response>")
    return {"questions": qs, "answer_key": ak}

@app.post("/grade-with-rubric", response_model=GradeWithRubricResp, dependencies=[Depends(require_api_key)])
def grade_with_rubric(body: GradeWithRubricReq):
    # naive scoring: pick highest level per criterion * weight
    total = 0.0
    details = []
    for c in body.rubric:
        top = max(c.levels, key=lambda lvl: lvl.points)
        pts = top.points * (c.weight or 1.0)
        total += pts
        details.append({"criterion": c.criterion, "selected_level": top.label, "points_awarded": pts})
    if body.max_total_points:
        total = min(total, body.max_total_points)
    feedback = "Good structure; consider adding more specific evidence."
    return {"total_points": total, "criteria": details, "feedback": feedback}

@app.post("/map-objectives-to-standards", response_model=MapObjectivesResp, dependencies=[Depends(require_api_key)])
def map_objectives_to_standards(body: MapObjectivesReq):
    fw = body.frameworks or ["CCSS"]
    mappings = []
    for obj in body.objectives:
        mappings.append({"objective": obj, "framework": fw[0], "suggested_standard": "RL.5.2", "confidence": 0.72})
    return {"mappings": mappings}

@app.post("/schedule-parent-conference", response_model=ScheduleConferenceResp, dependencies=[Depends(require_api_key)])
def schedule_parent_conference(body: ScheduleConferenceReq):
    proposals = []
    for blk in body.teacher_availability_blocks[:3]:
        proposals.append({
            "start_iso": blk.start_iso,
            "end_iso": blk.end_iso,
            "modality": (body.preferred_modalities or ["zoom"])[0],
        })
    invite = (
        f"Hello {', '.join(body.guardians)},\n\n"
        f"I'd like to meet regarding {body.student_name}. Here are some proposed times:\n"
        + "\n".join([f"- {p['start_iso']} to {p['end_iso']} ({p['modality']})" for p in proposals])
        + "\n\nBest,\nMindCanvas"
    )
    return {"proposals": proposals, "invite_draft": invite}

@app.post("/track-student-progress", response_model=TrackProgressResp, dependencies=[Depends(require_api_key)])
def track_student_progress(body: TrackProgressReq):
    # naive rollup by standard: % correct
    by_std = {}
    for e in body.entries:
        pct = e.score / e.max_score
        by_std.setdefault(e.standard, []).append(pct)
    mastery = [{"standard": s, "avg_mastery": round(sum(v) / len(v), 3), "samples": len(v)} for s, v in by_std.items()]
    return {"mastery": mastery}

@app.post("/analyze-exit-tickets", response_model=AnalyzeExitResp, dependencies=[Depends(require_api_key)])
def analyze_exit_tickets(body: AnalyzeExitReq):
    # toy clustering by length parity
    groups = [
        {"group": 1, "label": "Concise", "responses": [r for r in body.responses if len(r) < 50]},
        {"group": 2, "label": "Detailed", "responses": [r for r in body.responses if len(r) >= 50]},
    ]
    misconceptions = ["Confuses chlorophyll with sugar synthesis"]
    return {"groups": groups, "misconceptions": misconceptions}

@app.get("/", include_in_schema=False)
def root():
    return {"status": "ok", "service": "MindCanvas Teacher Actions", "time": now_iso()}
