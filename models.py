from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Faculty(Base):
    __tablename__ = "faculties"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    phone = Column(String(15))
    image_url = Column(String(255), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    github_url = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)
    experience = Column(String(20), nullable=True)  # Total experience in years
    c_experience = Column(String(20), nullable=True)  # C programming experience
    py_experience = Column(String(20), nullable=True)  # Python experience
    research_area = Column(String(255), nullable=True)  # Research area
    personal_email = Column(String(100), nullable=True)  # Personal email
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    timetable_entries = relationship("TimetableEntry", back_populates="faculty")
    daily_entries = relationship("DailyEntry", back_populates="faculty")

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)

class TimetableEntry(Base):
    __tablename__ = "timetable_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    day = Column(String(20), nullable=False)  # Monday, Tuesday, etc.
    period = Column(Integer, nullable=False)  # 1-9
    subject_code = Column(String(20), default="24UCS271")
    subject_name = Column(String(50), default="PROG C")
    class_type = Column(String(20), default="theory")  # theory, lab, mini_project
    
    faculty = relationship("Faculty", back_populates="timetable_entries")
    department = relationship("Department")

class Syllabus(Base):
    __tablename__ = "syllabus"
    
    id = Column(Integer, primary_key=True, index=True)
    session_number = Column(Integer, nullable=False)  # Session 1, 2, 3...
    session_title = Column(String(200), nullable=False)  # e.g., "Introduction to C Programming"
    unit = Column(Integer, nullable=False)
    topics = Column(Text, nullable=True)  # Topics/Content outline
    ppt_url = Column(String(255), nullable=True)  # PPT Resource URL

class LabProgram(Base):
    __tablename__ = "lab_programs"
    
    id = Column(Integer, primary_key=True, index=True)
    program_number = Column(Integer, nullable=False)
    program_title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    moodle_url = Column(String(255), nullable=True)

class PeriodTiming(Base):
    __tablename__ = "period_timings"
    
    id = Column(Integer, primary_key=True, index=True)
    period = Column(Integer, unique=True, nullable=False)  # 1-9
    start_time = Column(String(20), nullable=False)  # e.g., "08:00 AM"
    end_time = Column(String(20), nullable=False)  # e.g., "08:45 AM"
    display_time = Column(String(50), nullable=False)  # e.g., "08:00 AM - 08:45 AM"

class DailyEntry(Base):
    __tablename__ = "daily_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    date = Column(Date, nullable=False)
    period = Column(Integer, nullable=False)
    class_type = Column(String(20), default="theory")  # theory, lab, mini_project
    
    # For Theory classes
    syllabus_id = Column(Integer, ForeignKey("syllabus.id"), nullable=True)
    
    # For Lab classes
    lab_program_id = Column(Integer, ForeignKey("lab_programs.id"), nullable=True)
    lab_work_done = Column(Text, nullable=True)  # What was done in this lab period
    
    # For Mini Project
    mini_project_progress = Column(Text, nullable=True)
    
    # For Own Content (when not from syllabus)
    is_own_content = Column(Boolean, default=False)
    own_content_title = Column(String(255), nullable=True)
    own_content_summary = Column(Text, nullable=True)
    
    # Common fields
    summary = Column(Text, nullable=True)
    is_absent = Column(Boolean, default=False)
    is_swapped = Column(Boolean, default=False)
    swapped_with = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    faculty = relationship("Faculty", back_populates="daily_entries")
    department = relationship("Department")
    syllabus = relationship("Syllabus")
    lab_program = relationship("LabProgram")
