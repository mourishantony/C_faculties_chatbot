from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel

from database import engine, get_db, SessionLocal
from models import Base, Faculty, Admin, Department, TimetableEntry, DailyEntry, Syllabus, PeriodTiming, LabProgram, SuperAdmin, FAQ
from auth import (
    verify_password, get_password_hash, create_access_token, decode_token,
    get_current_faculty, get_current_admin, get_current_super_admin
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
    print(" Loading semantic chatbot model...")
    # Create a dummy db session just to initialize the model
    db = SessionLocal()
    semantic_chatbot = SemanticChatbotService(db)
    db.close()
    print(" Semantic chatbot ready!")

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

# ----- Super Admin Pydantic Models -----
class FacultyCreate(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None
    image_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    department: Optional[str] = None
    experience: Optional[str] = None
    c_experience: Optional[str] = None
    py_experience: Optional[str] = None
    research_area: Optional[str] = None
    personal_email: Optional[str] = None

class FacultyUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    image_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    department: Optional[str] = None
    experience: Optional[str] = None
    c_experience: Optional[str] = None
    py_experience: Optional[str] = None
    research_area: Optional[str] = None
    personal_email: Optional[str] = None
    is_active: Optional[bool] = None

class TimetableCreate(BaseModel):
    faculty_id: int
    department_id: int
    day: str
    period: int
    subject_code: str = "24UCS271"
    subject_name: str = "PROG C"
    class_type: str = "theory"

class TimetableUpdate(BaseModel):
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    day: Optional[str] = None
    period: Optional[int] = None
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    class_type: Optional[str] = None

class SyllabusCreate(BaseModel):
    session_number: int
    session_title: str
    unit: int
    topics: Optional[str] = None
    ppt_url: Optional[str] = None

class SyllabusUpdate(BaseModel):
    session_number: Optional[int] = None
    session_title: Optional[str] = None
    unit: Optional[int] = None
    topics: Optional[str] = None
    ppt_url: Optional[str] = None

class LabProgramCreate(BaseModel):
    program_number: int
    program_title: str
    description: Optional[str] = None
    moodle_url: Optional[str] = None

class LabProgramUpdate(BaseModel):
    program_number: Optional[int] = None
    program_title: Optional[str] = None
    description: Optional[str] = None
    moodle_url: Optional[str] = None

class FAQCreate(BaseModel):
    question: str
    answer: str
    category: Optional[str] = "general"

class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class DepartmentCreate(BaseModel):
    name: str
    code: str

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None

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
    """Single login endpoint for faculty, admin, and super_admin using email."""
    # Try super_admin first
    super_admin = db.query(SuperAdmin).filter(SuperAdmin.username == data.email).first()
    if super_admin and verify_password(data.password, super_admin.password):
        token = create_access_token({"sub": str(super_admin.id), "type": "super_admin"})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_type": "super_admin",
        }
    
    # Try faculty
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

# ============ Super Admin Routes ============

# ----- Faculty CRUD -----
@app.get("/api/super-admin/faculties")
def super_admin_get_faculties(
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
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

@app.post("/api/super-admin/faculties")
def super_admin_create_faculty(
    data: FacultyCreate,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    # Check if email already exists
    existing = db.query(Faculty).filter(Faculty.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    faculty = Faculty(
        name=data.name,
        email=data.email,
        password=get_password_hash(data.password),
        phone=data.phone,
        image_url=data.image_url,
        linkedin_url=data.linkedin_url,
        github_url=data.github_url,
        department=data.department,
        experience=data.experience,
        c_experience=data.c_experience,
        py_experience=data.py_experience,
        research_area=data.research_area,
        personal_email=data.personal_email
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return {"message": "Faculty created successfully", "id": faculty.id}

@app.put("/api/super-admin/faculties/{faculty_id}")
def super_admin_update_faculty(
    faculty_id: int,
    data: FacultyUpdate,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    
    if data.name is not None:
        faculty.name = data.name
    if data.email is not None:
        faculty.email = data.email
    if data.password is not None:
        faculty.password = get_password_hash(data.password)
    if data.phone is not None:
        faculty.phone = data.phone
    if data.image_url is not None:
        faculty.image_url = data.image_url
    if data.linkedin_url is not None:
        faculty.linkedin_url = data.linkedin_url
    if data.github_url is not None:
        faculty.github_url = data.github_url
    if data.department is not None:
        faculty.department = data.department
    if data.experience is not None:
        faculty.experience = data.experience
    if data.c_experience is not None:
        faculty.c_experience = data.c_experience
    if data.py_experience is not None:
        faculty.py_experience = data.py_experience
    if data.research_area is not None:
        faculty.research_area = data.research_area
    if data.personal_email is not None:
        faculty.personal_email = data.personal_email
    if data.is_active is not None:
        faculty.is_active = data.is_active
    
    db.commit()
    return {"message": "Faculty updated successfully"}

@app.delete("/api/super-admin/faculties/{faculty_id}")
def super_admin_delete_faculty(
    faculty_id: int,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    
    # Delete related entries first
    db.query(TimetableEntry).filter(TimetableEntry.faculty_id == faculty_id).delete()
    db.query(DailyEntry).filter(DailyEntry.faculty_id == faculty_id).delete()
    db.delete(faculty)
    db.commit()
    return {"message": "Faculty deleted successfully"}

# ----- Timetable CRUD -----
@app.get("/api/super-admin/timetable")
def super_admin_get_timetable(
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    entries = db.query(TimetableEntry).all()
    result = []
    for e in entries:
        faculty = db.query(Faculty).filter(Faculty.id == e.faculty_id).first()
        dept = db.query(Department).filter(Department.id == e.department_id).first()
        result.append({
            "id": e.id,
            "faculty_id": e.faculty_id,
            "faculty_name": faculty.name if faculty else "Unknown",
            "department_id": e.department_id,
            "department_name": dept.name if dept else "Unknown",
            "department_code": dept.code if dept else "Unknown",
            "day": e.day,
            "period": e.period,
            "subject_code": e.subject_code,
            "subject_name": e.subject_name,
            "class_type": e.class_type
        })
    return result

@app.post("/api/super-admin/timetable")
def super_admin_create_timetable(
    data: TimetableCreate,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    entry = TimetableEntry(
        faculty_id=data.faculty_id,
        department_id=data.department_id,
        day=data.day,
        period=data.period,
        subject_code=data.subject_code,
        subject_name=data.subject_name,
        class_type=data.class_type
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"message": "Timetable entry created successfully", "id": entry.id}

@app.put("/api/super-admin/timetable/{entry_id}")
def super_admin_update_timetable(
    entry_id: int,
    data: TimetableUpdate,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    entry = db.query(TimetableEntry).filter(TimetableEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
    
    if data.faculty_id is not None:
        entry.faculty_id = data.faculty_id
    if data.department_id is not None:
        entry.department_id = data.department_id
    if data.day is not None:
        entry.day = data.day
    if data.period is not None:
        entry.period = data.period
    if data.subject_code is not None:
        entry.subject_code = data.subject_code
    if data.subject_name is not None:
        entry.subject_name = data.subject_name
    if data.class_type is not None:
        entry.class_type = data.class_type
    
    db.commit()
    return {"message": "Timetable entry updated successfully"}

@app.delete("/api/super-admin/timetable/{entry_id}")
def super_admin_delete_timetable(
    entry_id: int,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    entry = db.query(TimetableEntry).filter(TimetableEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
    
    db.delete(entry)
    db.commit()
    return {"message": "Timetable entry deleted successfully"}

# ----- Syllabus CRUD -----
@app.get("/api/super-admin/syllabus")
def super_admin_get_syllabus(
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    sessions = db.query(Syllabus).order_by(Syllabus.unit, Syllabus.session_number).all()
    return [{
        "id": s.id,
        "session_number": s.session_number,
        "session_title": s.session_title,
        "unit": s.unit,
        "topics": s.topics,
        "ppt_url": s.ppt_url
    } for s in sessions]

@app.post("/api/super-admin/syllabus")
def super_admin_create_syllabus(
    data: SyllabusCreate,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    session = Syllabus(
        session_number=data.session_number,
        session_title=data.session_title,
        unit=data.unit,
        topics=data.topics,
        ppt_url=data.ppt_url
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"message": "Syllabus session created successfully", "id": session.id}

@app.put("/api/super-admin/syllabus/{session_id}")
def super_admin_update_syllabus(
    session_id: int,
    data: SyllabusUpdate,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    session = db.query(Syllabus).filter(Syllabus.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Syllabus session not found")
    
    if data.session_number is not None:
        session.session_number = data.session_number
    if data.session_title is not None:
        session.session_title = data.session_title
    if data.unit is not None:
        session.unit = data.unit
    if data.topics is not None:
        session.topics = data.topics
    if data.ppt_url is not None:
        session.ppt_url = data.ppt_url
    
    db.commit()
    return {"message": "Syllabus session updated successfully"}

@app.delete("/api/super-admin/syllabus/{session_id}")
def super_admin_delete_syllabus(
    session_id: int,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    session = db.query(Syllabus).filter(Syllabus.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Syllabus session not found")
    
    db.delete(session)
    db.commit()
    return {"message": "Syllabus session deleted successfully"}

# ----- Lab Programs CRUD -----
@app.get("/api/super-admin/lab-programs")
def super_admin_get_lab_programs(
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    programs = db.query(LabProgram).order_by(LabProgram.program_number).all()
    return [{
        "id": p.id,
        "program_number": p.program_number,
        "program_title": p.program_title,
        "description": p.description,
        "moodle_url": p.moodle_url
    } for p in programs]

@app.post("/api/super-admin/lab-programs")
def super_admin_create_lab_program(
    data: LabProgramCreate,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    program = LabProgram(
        program_number=data.program_number,
        program_title=data.program_title,
        description=data.description,
        moodle_url=data.moodle_url
    )
    db.add(program)
    db.commit()
    db.refresh(program)
    return {"message": "Lab program created successfully", "id": program.id}

@app.put("/api/super-admin/lab-programs/{program_id}")
def super_admin_update_lab_program(
    program_id: int,
    data: LabProgramUpdate,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    program = db.query(LabProgram).filter(LabProgram.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Lab program not found")
    
    if data.program_number is not None:
        program.program_number = data.program_number
    if data.program_title is not None:
        program.program_title = data.program_title
    if data.description is not None:
        program.description = data.description
    if data.moodle_url is not None:
        program.moodle_url = data.moodle_url
    
    db.commit()
    return {"message": "Lab program updated successfully"}

@app.delete("/api/super-admin/lab-programs/{program_id}")
def super_admin_delete_lab_program(
    program_id: int,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    program = db.query(LabProgram).filter(LabProgram.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Lab program not found")
    
    db.delete(program)
    db.commit()
    return {"message": "Lab program deleted successfully"}

# ----- FAQ CRUD -----
@app.get("/api/super-admin/faqs")
def super_admin_get_faqs(
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    faqs = db.query(FAQ).order_by(FAQ.category, FAQ.id).all()
    return [{
        "id": f.id,
        "question": f.question,
        "answer": f.answer,
        "category": f.category,
        "is_active": f.is_active,
        "created_at": f.created_at.isoformat() if f.created_at else None,
        "updated_at": f.updated_at.isoformat() if f.updated_at else None
    } for f in faqs]

@app.get("/api/faqs")
def get_active_faqs(db: Session = Depends(get_db)):
    """Public endpoint for getting active FAQs"""
    faqs = db.query(FAQ).filter(FAQ.is_active == True).order_by(FAQ.category, FAQ.id).all()
    return [{
        "id": f.id,
        "question": f.question,
        "answer": f.answer,
        "category": f.category
    } for f in faqs]

@app.post("/api/super-admin/faqs")
def super_admin_create_faq(
    data: FAQCreate,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    faq = FAQ(
        question=data.question,
        answer=data.answer,
        category=data.category
    )
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return {"message": "FAQ created successfully", "id": faq.id}

@app.put("/api/super-admin/faqs/{faq_id}")
def super_admin_update_faq(
    faq_id: int,
    data: FAQUpdate,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    if data.question is not None:
        faq.question = data.question
    if data.answer is not None:
        faq.answer = data.answer
    if data.category is not None:
        faq.category = data.category
    if data.is_active is not None:
        faq.is_active = data.is_active
    
    db.commit()
    return {"message": "FAQ updated successfully"}

@app.delete("/api/super-admin/faqs/{faq_id}")
def super_admin_delete_faq(
    faq_id: int,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    db.delete(faq)
    db.commit()
    return {"message": "FAQ deleted successfully"}

# ----- Departments CRUD -----
@app.get("/api/super-admin/departments")
def super_admin_get_departments(
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    departments = db.query(Department).all()
    return [{"id": d.id, "name": d.name, "code": d.code} for d in departments]

@app.post("/api/super-admin/departments")
def super_admin_create_department(
    data: DepartmentCreate,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(Department).filter(Department.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department code already exists")
    
    dept = Department(name=data.name, code=data.code)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return {"message": "Department created successfully", "id": dept.id}

@app.put("/api/super-admin/departments/{dept_id}")
def super_admin_update_department(
    dept_id: int,
    data: DepartmentUpdate,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    if data.name is not None:
        dept.name = data.name
    if data.code is not None:
        dept.code = data.code
    
    db.commit()
    return {"message": "Department updated successfully"}

@app.delete("/api/super-admin/departments/{dept_id}")
def super_admin_delete_department(
    dept_id: int,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Check if department is used in timetable
    in_use = db.query(TimetableEntry).filter(TimetableEntry.department_id == dept_id).first()
    if in_use:
        raise HTTPException(status_code=400, detail="Department is in use in timetable entries")
    
    db.delete(dept)
    db.commit()
    return {"message": "Department deleted successfully"}

# ----- Super Admin Dashboard Stats -----
@app.get("/api/super-admin/stats")
def super_admin_get_stats(
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    return {
        "total_faculties": db.query(Faculty).count(),
        "active_faculties": db.query(Faculty).filter(Faculty.is_active == True).count(),
        "total_departments": db.query(Department).count(),
        "total_timetable_entries": db.query(TimetableEntry).count(),
        "total_syllabus_sessions": db.query(Syllabus).count(),
        "total_lab_programs": db.query(LabProgram).count(),
        "total_faqs": db.query(FAQ).count(),
        "active_faqs": db.query(FAQ).filter(FAQ.is_active == True).count()
    }

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

@app.get("/super-admin/dashboard", response_class=HTMLResponse)
def super_admin_dashboard_page(request: Request):
    return templates.TemplateResponse("super_admin_dashboard.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
