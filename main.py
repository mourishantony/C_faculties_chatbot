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
from models import Base, Faculty, Admin, Department, TimetableEntry, DailyEntry, Syllabus
from auth import (
    verify_password, get_password_hash, create_access_token, decode_token,
    get_current_faculty, get_current_admin
)
from chatbot import process_chatbot_query

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="C Programming Faculty Management System")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# ============ Pydantic Models ============
class FacultyLogin(BaseModel):
    email: str
    password: str

class AdminLogin(BaseModel):
    username: str
    password: str

class DailyEntryCreate(BaseModel):
    department_id: int
    period: int
    syllabus_id: Optional[int] = None
    is_absent: bool = False
    is_swapped: bool = False
    swapped_with: Optional[str] = None
    summary: Optional[str] = None
    session_plan: Optional[str] = None

class ChatQuery(BaseModel):
    query: str

# ============ Helper Functions ============
def get_day_name(d: date = None):
    if d is None:
        d = date.today()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[d.weekday()]

# ============ API Routes ============

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
    admin = db.query(Admin).filter(Admin.username == data.username).first()
    if not admin or not verify_password(data.password, admin.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": str(admin.id), "type": "admin"})
    return {"access_token": token, "token_type": "bearer"}

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
            "is_filled": daily is not None,
            "daily_entry": {
                "id": daily.id if daily else None,
                "syllabus_id": daily.syllabus_id if daily else None,
                "is_absent": daily.is_absent if daily else False,
                "is_swapped": daily.is_swapped if daily else False,
                "swapped_with": daily.swapped_with if daily else None,
                "summary": daily.summary if daily else None,
                "session_plan": daily.session_plan if daily else None
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
    topics = db.query(Syllabus).order_by(Syllabus.unit, Syllabus.order_num).all()
    return [{"id": t.id, "topic_name": t.topic_name, "unit": t.unit} for t in topics]

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
        existing.syllabus_id = entry.syllabus_id
        existing.is_absent = entry.is_absent
        existing.is_swapped = entry.is_swapped
        existing.swapped_with = entry.swapped_with
        existing.summary = entry.summary
        existing.session_plan = entry.session_plan
        db.commit()
        return {"message": "Entry updated successfully", "entry_id": existing.id}
    
    # Create new entry
    daily_entry = DailyEntry(
        faculty_id=faculty.id,
        department_id=entry.department_id,
        date=today,
        period=entry.period,
        syllabus_id=entry.syllabus_id,
        is_absent=entry.is_absent,
        is_swapped=entry.is_swapped,
        swapped_with=entry.swapped_with,
        summary=entry.summary,
        session_plan=entry.session_plan
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
        
        result.append({
            "id": entry.id,
            "date": entry.date.isoformat(),
            "period": entry.period,
            "faculty_name": faculty.name,
            "department_name": dept.name,
            "topic": syllabus.topic_name if syllabus else "N/A",
            "is_absent": entry.is_absent,
            "is_swapped": entry.is_swapped,
            "swapped_with": entry.swapped_with,
            "summary": entry.summary,
            "session_plan": entry.session_plan
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
        "department": f.department
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

# ----- Chatbot Route -----
@app.post("/api/chatbot")
def chatbot_query(data: ChatQuery, db: Session = Depends(get_db)):
    response = process_chatbot_query(data.query, db)
    return {"response": response}

# ============ HTML Page Routes ============
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/faculty/login", response_class=HTMLResponse)
def faculty_login_page(request: Request):
    return templates.TemplateResponse("faculty_login.html", {"request": request})

@app.get("/faculty/dashboard", response_class=HTMLResponse)
def faculty_dashboard_page(request: Request):
    return templates.TemplateResponse("faculty_dashboard.html", {"request": request})

@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard_page(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
