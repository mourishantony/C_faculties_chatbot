from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta
from typing import Optional
from pydantic import BaseModel

from database import engine, get_db, SessionLocal
from models import Base, Faculty, Admin, Department, TimetableEntry, DailyEntry, Syllabus, PeriodTiming, LabProgram
from auth import (
    verify_password, get_password_hash, create_access_token, decode_token,
    get_current_faculty, get_current_admin
)
from chatbot import process_chatbot_query
from chatbot_service import ChatbotService
from chatbot_semantic import SemanticChatbotService

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="C Programming Faculty Management System")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize semantic chatbot service once at startup (load model only once)
semantic_chatbot = None

@app.on_event("startup")
async def startup_event():
    """Load semantic model on startup"""
    global semantic_chatbot
    print("🚀 Loading semantic chatbot model...")
    # Create a dummy db session just to initialize the model
    db = SessionLocal()
    semantic_chatbot = SemanticChatbotService(db)
    db.close()
    print("✅ Semantic chatbot ready!")

# ============ Pydantic Models ============
class FacultyLogin(BaseModel):
    email: str
    password: str

class AdminLogin(BaseModel):
    email: str
    password: str

class DailyEntryCreate(BaseModel):
    department_id: int
    period: int
    class_type: str = "theory"  # theory, lab, mini_project
    
    # For Theory classes
    syllabus_id: Optional[int] = None
    
    # For Lab classes
    lab_program_id: Optional[int] = None
    lab_work_done: Optional[str] = None
    
    # For Mini Project
    mini_project_progress: Optional[str] = None
    
    # For Own Content (when not following syllabus)
    is_own_content: bool = False
    own_content_title: Optional[str] = None
    own_content_summary: Optional[str] = None
    
    # Common fields
    summary: Optional[str] = None
    is_absent: bool = False
    is_swapped: bool = False
    swapped_with: Optional[str] = None

class ChatQuery(BaseModel):
    query: str

class UnifiedLogin(BaseModel):
    email: str
    password: str

# ============ Helper Functions ============
def get_day_name(d: date = None):
    if d is None:
        d = date.today()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[d.weekday()]

# ============ API Routes ============

# ----- Period Timings -----
@app.get("/api/period-timings")
def get_period_timings(db: Session = Depends(get_db)):
    timings = db.query(PeriodTiming).order_by(PeriodTiming.period).all()
    return {t.period: t.display_time for t in timings}

# ----- Authentication -----
@app.post("/api/faculty/login")
def login_faculty(data: FacultyLogin, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.email == data.email).first()
    if not faculty or not verify_password(data.password, faculty.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": str(faculty.id), "type": "faculty"})
    return {"access_token": token, "token_type": "bearer", "faculty_name": faculty.name}

@app.post("/api/admin/login")
def login_admin(data: AdminLogin, db: Session = Depends(get_db)):
    # We treat the admin's email as their username in the DB
    admin = db.query(Admin).filter(Admin.username == data.email).first()
    if not admin or not verify_password(data.password, admin.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": str(admin.id), "type": "admin"})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/login")
def unified_login(data: UnifiedLogin, db: Session = Depends(get_db)):
    """Single login endpoint for both faculty and admin using email."""
    # Try faculty first
    faculty = db.query(Faculty).filter(Faculty.email == data.email).first()
    if faculty and verify_password(data.password, faculty.password):
        token = create_access_token({"sub": str(faculty.id), "type": "faculty"})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_type": "faculty",
            "faculty_name": faculty.name,
        }

    # Then try admin (username stores admin email)
    admin = db.query(Admin).filter(Admin.username == data.email).first()
    if admin and verify_password(data.password, admin.password):
        token = create_access_token({"sub": str(admin.id), "type": "admin"})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_type": "admin",
        }

    raise HTTPException(status_code=401, detail="Invalid credentials")

# ----- Faculty Routes -----
@app.get("/api/faculty/me")
def get_faculty_profile(faculty: Faculty = Depends(get_current_faculty)):
    return {
        "id": faculty.id,
        "name": faculty.name,
        "email": faculty.email,
        "phone": faculty.phone
    }

@app.get("/api/faculty/today-schedule")
def get_today_schedule(faculty: Faculty = Depends(get_current_faculty), db: Session = Depends(get_db)):
    today = date.today()
    day_name = get_day_name(today)
    
    # Get timetable entries for today
    entries = db.query(TimetableEntry).filter(
        TimetableEntry.faculty_id == faculty.id,
        TimetableEntry.day == day_name
    ).order_by(TimetableEntry.period).all()
    
    result = []
    for entry in entries:
        dept = db.query(Department).filter(Department.id == entry.department_id).first()
        
        # Check if already filled
        daily = db.query(DailyEntry).filter(
            DailyEntry.faculty_id == faculty.id,
            DailyEntry.department_id == entry.department_id,
            DailyEntry.date == today,
            DailyEntry.period == entry.period
        ).first()
        
        result.append({
            "timetable_id": entry.id,
            "department_id": entry.department_id,
            "department_name": dept.name,
            "period": entry.period,
            "subject_code": entry.subject_code,
            "subject_name": entry.subject_name,
            "class_type": entry.class_type,  # theory, lab, mini_project
            "is_filled": daily is not None,
            "daily_entry": {
                "id": daily.id if daily else None,
                "class_type": daily.class_type if daily else None,
                "syllabus_id": daily.syllabus_id if daily else None,
                "lab_program_id": daily.lab_program_id if daily else None,
                "lab_work_done": daily.lab_work_done if daily else None,
                "mini_project_progress": daily.mini_project_progress if daily else None,
                "is_own_content": daily.is_own_content if daily else False,
                "own_content_title": daily.own_content_title if daily else None,
                "own_content_summary": daily.own_content_summary if daily else None,
                "summary": daily.summary if daily else None,
                "is_absent": daily.is_absent if daily else False,
                "is_swapped": daily.is_swapped if daily else False,
                "swapped_with": daily.swapped_with if daily else None
            } if daily else None
        })
    
    return {
        "date": today.isoformat(),
        "day": day_name,
        "schedule": result
    }

@app.get("/api/departments")
def get_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).all()
    return [{"id": d.id, "name": d.name, "code": d.code} for d in departments]

@app.get("/api/syllabus")
def get_syllabus(db: Session = Depends(get_db)):
    sessions = db.query(Syllabus).order_by(Syllabus.unit, Syllabus.session_number).all()
    return [{
        "id": s.id,
        "session_number": s.session_number,
        "session_title": s.session_title,
        "unit": s.unit,
        "topics": s.topics,
        "ppt_url": s.ppt_url
    } for s in sessions]

@app.get("/api/lab-programs")
def get_lab_programs(db: Session = Depends(get_db)):
    programs = db.query(LabProgram).order_by(LabProgram.program_number).all()
    return [{
        "id": p.id,
        "program_number": p.program_number,
        "program_title": p.program_title,
        "description": p.description
    } for p in programs]

@app.post("/api/faculty/daily-entry")
def submit_daily_entry(
    entry: DailyEntryCreate,
    faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    today = date.today()
    
    # Check if entry already exists
    existing = db.query(DailyEntry).filter(
        DailyEntry.faculty_id == faculty.id,
        DailyEntry.department_id == entry.department_id,
        DailyEntry.date == today,
        DailyEntry.period == entry.period
    ).first()
    
    if existing:
        # Update existing entry
        existing.class_type = entry.class_type
        existing.syllabus_id = entry.syllabus_id
        existing.lab_program_id = entry.lab_program_id
        existing.lab_work_done = entry.lab_work_done
        existing.mini_project_progress = entry.mini_project_progress
        existing.is_own_content = entry.is_own_content
        existing.own_content_title = entry.own_content_title
        existing.own_content_summary = entry.own_content_summary
        existing.summary = entry.summary
        existing.is_absent = entry.is_absent
        existing.is_swapped = entry.is_swapped
        existing.swapped_with = entry.swapped_with
        db.commit()
        return {"message": "Entry updated successfully", "entry_id": existing.id}
    
    # Create new entry
    daily_entry = DailyEntry(
        faculty_id=faculty.id,
        department_id=entry.department_id,
        date=today,
        period=entry.period,
        class_type=entry.class_type,
        syllabus_id=entry.syllabus_id,
        lab_program_id=entry.lab_program_id,
        lab_work_done=entry.lab_work_done,
        mini_project_progress=entry.mini_project_progress,
        is_own_content=entry.is_own_content,
        own_content_title=entry.own_content_title,
        own_content_summary=entry.own_content_summary,
        summary=entry.summary,
        is_absent=entry.is_absent,
        is_swapped=entry.is_swapped,
        swapped_with=entry.swapped_with
    )
    db.add(daily_entry)
    db.commit()
    db.refresh(daily_entry)
    
    return {"message": "Entry submitted successfully", "entry_id": daily_entry.id}

# ----- Admin Routes -----
@app.get("/api/admin/report")
def get_admin_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Default to today
    if not start_date:
        start_date = date.today().isoformat()
    if not end_date:
        end_date = date.today().isoformat()
    
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    entries = db.query(DailyEntry).filter(
        DailyEntry.date >= start,
        DailyEntry.date <= end
    ).order_by(DailyEntry.date, DailyEntry.period).all()
    
    result = []
    for entry in entries:
        faculty = db.query(Faculty).filter(Faculty.id == entry.faculty_id).first()
        dept = db.query(Department).filter(Department.id == entry.department_id).first()
        syllabus = db.query(Syllabus).filter(Syllabus.id == entry.syllabus_id).first() if entry.syllabus_id else None
        lab_program = db.query(LabProgram).filter(LabProgram.id == entry.lab_program_id).first() if entry.lab_program_id else None
        
        # Determine what was taught based on class type
        if entry.is_own_content:
            topic_info = f"Own Content: {entry.own_content_title}"
        elif entry.class_type == "theory" and syllabus:
            topic_info = f"Session {syllabus.session_number}: {syllabus.session_title}"
        elif entry.class_type == "lab" and lab_program:
            topic_info = f"Lab {lab_program.program_number}: {lab_program.program_title}"
        elif entry.class_type == "mini_project":
            topic_info = "Mini Project"
        else:
            topic_info = "N/A"
        
        result.append({
            "id": entry.id,
            "date": entry.date.isoformat(),
            "period": entry.period,
            "class_type": entry.class_type,
            "faculty_name": faculty.name,
            "department_name": dept.name,
            "topic": topic_info,
            "session_title": syllabus.session_title if syllabus else None,
            "lab_program_title": lab_program.program_title if lab_program else None,
            "lab_work_done": entry.lab_work_done,
            "mini_project_progress": entry.mini_project_progress,
            "is_own_content": entry.is_own_content,
            "own_content_title": entry.own_content_title,
            "own_content_summary": entry.own_content_summary,
            "is_absent": entry.is_absent,
            "is_swapped": entry.is_swapped,
            "swapped_with": entry.swapped_with,
            "summary": entry.summary,
            "ppt_url": syllabus.ppt_url if syllabus else None
        })
    
    return {"entries": result, "total": len(result)}

@app.get("/api/admin/faculties")
def get_all_faculties(db: Session = Depends(get_db)):
    faculties = db.query(Faculty).all()
    return [{
        "id": f.id,
        "name": f.name,
        "email": f.email,
        "phone": f.phone,
        "is_active": f.is_active,
        "image_url": f.image_url,
        "linkedin_url": f.linkedin_url,
        "github_url": f.github_url,
        "department": f.department,
        "experience": f.experience,
        "c_experience": f.c_experience,
        "py_experience": f.py_experience,
        "research_area": f.research_area,
        "personal_email": f.personal_email
    } for f in faculties]

@app.get("/api/admin/today-summary")
def get_today_summary(db: Session = Depends(get_db)):
    today = date.today()
    day_name = get_day_name(today)
    
    # Total scheduled classes today
    total_scheduled = db.query(TimetableEntry).filter(
        TimetableEntry.day == day_name
    ).count()
    
    # Filled entries today
    filled = db.query(DailyEntry).filter(DailyEntry.date == today).count()
    
    # Absent today
    absent = db.query(DailyEntry).filter(
        DailyEntry.date == today,
        DailyEntry.is_absent == True
    ).count()
    
    # Swapped today
    swapped = db.query(DailyEntry).filter(
        DailyEntry.date == today,
        DailyEntry.is_swapped == True
    ).count()
    
    return {
        "date": today.isoformat(),
        "day": day_name,
        "total_scheduled": total_scheduled,
        "filled": filled,
        "pending": total_scheduled - filled,
        "absent": absent,
        "swapped": swapped
    }

@app.get("/api/admin/classes-by-type")
def get_classes_by_type(class_type: str, db: Session = Depends(get_db)):
    """Get all classes filtered by type (theory, lab, mini_project)"""
    # Get all timetable entries of this type
    entries = db.query(TimetableEntry).filter(
        TimetableEntry.class_type == class_type
    ).order_by(TimetableEntry.day, TimetableEntry.period).all()
    
    result = []
    for entry in entries:
        faculty = db.query(Faculty).filter(Faculty.id == entry.faculty_id).first()
        dept = db.query(Department).filter(Department.id == entry.department_id).first()
        
        result.append({
            "id": entry.id,
            "faculty_id": entry.faculty_id,
            "faculty_name": faculty.name if faculty else "Unknown",
            "faculty_email": faculty.email if faculty else None,
            "department_id": entry.department_id,
            "department_name": dept.name if dept else "Unknown",
            "department_code": dept.code if dept else "Unknown",
            "day": entry.day,
            "period": entry.period,
            "subject_code": entry.subject_code,
            "subject_name": entry.subject_name,
            "class_type": entry.class_type
        })
    
    return {
        "class_type": class_type,
        "total_classes": len(result),
        "classes": result
    }

# ----- Chatbot Route -----
@app.post("/api/chatbot")
def chatbot_query(data: ChatQuery, db: Session = Depends(get_db)):
    response = process_chatbot_query(data.query, db)
    return {"response": response}

@app.post("/api/admin/chatbot")
def admin_chatbot_query(data: ChatQuery, db: Session = Depends(get_db)):
    """Admin-specific chatbot endpoint with semantic understanding"""
    # Use pre-loaded semantic chatbot, just update db session
    semantic_chatbot.db = db
    response = semantic_chatbot.process_question(data.query)
    return {"response": response}

# ============ HTML Page Routes ============
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/faculty/dashboard", response_class=HTMLResponse)
def faculty_dashboard_page(request: Request):
    return templates.TemplateResponse("faculty_dashboard.html", {"request": request})

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard_page(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
