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
    
    faculty = relationship("Faculty", back_populates="timetable_entries")
    department = relationship("Department")

class Syllabus(Base):
    __tablename__ = "syllabus"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_name = Column(String(200), nullable=False)
    unit = Column(Integer, nullable=False)
    order_num = Column(Integer, nullable=False)

class DailyEntry(Base):
    __tablename__ = "daily_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    date = Column(Date, nullable=False)
    period = Column(Integer, nullable=False)
    syllabus_id = Column(Integer, ForeignKey("syllabus.id"), nullable=True)
    is_absent = Column(Boolean, default=False)
    is_swapped = Column(Boolean, default=False)
    swapped_with = Column(String(100), nullable=True)
    summary = Column(Text, nullable=True)
    session_plan = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    faculty = relationship("Faculty", back_populates="daily_entries")
    department = relationship("Department")
    syllabus = relationship("Syllabus")
