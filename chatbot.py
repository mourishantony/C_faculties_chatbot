"""
Simple FAQ-based Chatbot for C Programming Faculty Management System.
Uses FAQ data stored in the database for answering questions.
"""

from datetime import date, datetime
from sqlalchemy.orm import Session
from models import Faculty, Department, TimetableEntry, DailyEntry, Syllabus, PeriodTiming, LabProgram, FAQ
import re


def get_day_name(d: date = None):
    """Get the day name for a given date"""
    if d is None:
        d = date.today()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[d.weekday()]


def get_period_time(period: int, db: Session = None) -> str:
    """Get the time range for a period"""
    if db:
        timing = db.query(PeriodTiming).filter(PeriodTiming.period == period).first()
        if timing:
            return timing.display_time
    
    # Fallback
    period_times = {
        1: "08:00 AM - 08:45 AM",
        2: "08:45 AM - 09:30 AM",
        3: "09:45 AM - 10:30 AM",
        4: "10:30 AM - 11:15 AM",
        5: "11:15 AM - 12:00 PM",
        6: "01:00 PM - 01:45 PM",
        7: "01:45 PM - 02:30 PM",
        8: "02:30 PM - 03:15 PM",
        9: "03:30 PM - 04:15 PM"
    }
    return period_times.get(period, "Unknown")


class FAQChatbot:
    """Simple FAQ-based chatbot that searches FAQs in the database"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def process_question(self, question: str) -> str:
        """Process user question and return appropriate response"""
        question_lower = question.lower().strip()
        today = date.today()
        day_name = get_day_name(today)
        
        # 1. Check for greetings
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "hii", "hiii"]
        if any(question_lower == g or question_lower.startswith(g + " ") for g in greetings):
            return self._greeting_response()
        
        # 2. Check for help
        if question_lower in ["help", "?", "commands", "what can you do"]:
            return self._help_response()
        
        # 3. Check for schedule queries
        if self._is_schedule_query(question_lower):
            return self._get_schedule_response(day_name, question_lower)
        
        # 4. Check for faculty queries
        if self._is_faculty_query(question_lower):
            return self._get_faculty_response(question_lower, day_name)
        
        # 5. Check for lab program queries
        lab_match = re.search(r'(?:lab|week|w)\s*(?:program)?\s*(\d+)', question_lower)
        if lab_match or "lab" in question_lower:
            if lab_match:
                week_num = int(lab_match.group(1))
                return self._get_lab_program(week_num)
        
        # 6. Check for session/PPT queries
        session_match = re.search(r'(?:session|deck|ppt|slide)\s*(\d+)', question_lower)
        if session_match:
            session_num = int(session_match.group(1))
            return self._get_session_ppt(session_num)
        
        # 7. Search FAQs in database
        faq_response = self._search_faqs(question_lower)
        if faq_response:
            return faq_response
        
        # 8. Default response
        return self._default_response()
    
    def _is_schedule_query(self, question: str) -> bool:
        """Check if question is about schedule"""
        schedule_keywords = ["schedule", "class", "today", "classes", "teaching", "period", "timetable"]
        return any(kw in question for kw in schedule_keywords)
    
    def _is_faculty_query(self, question: str) -> bool:
        """Check if question is about faculty"""
        faculty_keywords = ["faculty", "teacher", "professor", "who is", "who teaches", "list all", "all faculty"]
        return any(kw in question for kw in faculty_keywords)
    
    def _greeting_response(self) -> str:
        """Return greeting message"""
        return """👋 **Hello! Welcome to C Programming Assistant!**

I can help you with:
• Today's class schedule
• Faculty information
• Lab programs
• Session/PPT materials
• FAQs

Type **help** to see all commands!"""
    
    def _help_response(self) -> str:
        """Return help message"""
        return """📚 **C Programming Chatbot - Help**

**Schedule Queries:**
• "Who has class today?"
• "Today's schedule"
• "Show classes"

**Faculty Queries:**
• "List all faculty"
• "Who teaches AIDS-A?"

**Lab Programs:**
• "Lab program week 3"
• "Week 5 lab"

**Session/PPT:**
• "Session 3 PPT"
• "Deck 5"

**General:**
• Ask any question about C Programming!"""
    
    def _default_response(self) -> str:
        """Return default response when no match found"""
        return """🤔 I couldn't find an answer to that question.

Try asking about:
• Today's schedule
• Faculty information
• Lab programs (e.g., "week 3 lab")
• Session materials (e.g., "session 5 ppt")

Or type **help** for more options!"""
    
    def _get_schedule_response(self, day_name: str, question: str) -> str:
        """Get schedule for today"""
        entries = self.db.query(TimetableEntry, Faculty, Department)\
            .join(Faculty, TimetableEntry.faculty_id == Faculty.id)\
            .join(Department, TimetableEntry.department_id == Department.id)\
            .filter(TimetableEntry.day == day_name)\
            .order_by(TimetableEntry.period)\
            .all()
        
        if not entries:
            return f"📅 No C Programming classes scheduled for **{day_name}**."
        
        response = f"📅 **C Programming Classes for {day_name}:**\n\n"
        
        faculty_seen = set()
        for entry, faculty, dept in entries:
            if faculty.id not in faculty_seen:
                periods = [e.period for e, f, d in entries if f.id == faculty.id]
                period_str = ", ".join(map(str, sorted(periods)))
                response += f"• **{faculty.name}** ({dept.code}) - Period {period_str}\n"
                faculty_seen.add(faculty.id)
        
        response += f"\n_Total: {len(faculty_seen)} faculty members teaching today_"
        return response
    
    def _get_faculty_response(self, question: str, day_name: str) -> str:
        """Get faculty information"""
        # Check if asking for specific department
        dept_codes = ["AIDS-A", "AIDS-B", "AIML-A", "AIML-B", "CSE-A", "CSE-B", 
                     "CSBS", "CYS", "ECE-A", "ECE-B", "IT-A", "IT-B", "MECH", "RA"]
        
        for code in dept_codes:
            if code.lower().replace("-", "") in question.replace("-", "").replace(" ", ""):
                return self._get_faculty_by_department(code, day_name)
        
        # List all faculties
        if "list" in question or "all" in question:
            return self._list_all_faculties()
        
        # Search by name
        faculties = self.db.query(Faculty).filter_by(is_active=True).all()
        for faculty in faculties:
            name_parts = faculty.name.lower().split()
            if any(part in question for part in name_parts if len(part) > 2):
                return self._get_faculty_schedule(faculty, day_name)
        
        return self._list_all_faculties()
    
    def _get_faculty_by_department(self, dept_code: str, day_name: str) -> str:
        """Get faculty for a specific department"""
        entry = self.db.query(TimetableEntry, Faculty, Department)\
            .join(Faculty, TimetableEntry.faculty_id == Faculty.id)\
            .join(Department, TimetableEntry.department_id == Department.id)\
            .filter(Department.code == dept_code, TimetableEntry.day == day_name)\
            .first()
        
        if not entry:
            return f"No faculty assigned to **{dept_code}** for {day_name}."
        
        _, faculty, dept = entry
        
        response = f"👨‍🏫 **Faculty for {dept.name}:**\n\n"
        response += f"**Name:** {faculty.name}\n"
        response += f"**Email:** {faculty.email}\n"
        response += f"**Phone:** {faculty.phone}\n"
        if faculty.experience:
            response += f"**Experience:** {faculty.experience} years\n"
        
        return response
    
    def _get_faculty_schedule(self, faculty: Faculty, day_name: str) -> str:
        """Get schedule for a specific faculty"""
        entries = self.db.query(TimetableEntry, Department)\
            .join(Department, TimetableEntry.department_id == Department.id)\
            .filter(TimetableEntry.faculty_id == faculty.id)\
            .order_by(TimetableEntry.day, TimetableEntry.period)\
            .all()
        
        if not entries:
            return f"**{faculty.name}** has no scheduled classes."
        
        response = f"👨‍🏫 **Schedule for {faculty.name}:**\n\n"
        
        from collections import defaultdict
        schedule_by_day = defaultdict(list)
        
        for entry, dept in entries:
            schedule_by_day[entry.day].append((entry.period, dept.code))
        
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        for day in days_order:
            if day in schedule_by_day:
                periods = sorted(schedule_by_day[day])
                period_str = ", ".join([f"P{p[0]} ({p[1]})" for p in periods])
                response += f"**{day}:** {period_str}\n"
        
        return response
    
    def _list_all_faculties(self) -> str:
        """List all active faculties"""
        faculties = self.db.query(Faculty).filter_by(is_active=True).all()
        
        if not faculties:
            return "No faculties found."
        
        response = f"👥 **All Faculties ({len(faculties)}):**\n\n"
        for i, fac in enumerate(faculties, 1):
            response += f"{i}. **{fac.name}** - {fac.department or 'N/A'}\n"
        
        return response
    
    def _get_lab_program(self, week_num: int) -> str:
        """Get lab program for a specific week"""
        program = self.db.query(LabProgram).filter(LabProgram.program_number == week_num).first()
        
        if not program:
            return f"No lab program found for week {week_num}."
        
        response = f"🔬 **Lab Program - Week {week_num}:**\n\n"
        response += f"**Title:** {program.program_title}\n"
        if program.description:
            response += f"**Description:** {program.description}\n"
        if program.moodle_url:
            response += f"**Moodle:** {program.moodle_url}\n"
        
        return response
    
    def _get_session_ppt(self, session_num: int) -> str:
        """Get PPT for a specific session"""
        session = self.db.query(Syllabus).filter(Syllabus.session_number == session_num).first()
        
        if not session:
            return f"No session {session_num} found."
        
        response = f"📊 **Session {session_num}:**\n\n"
        response += f"**Topic:** {session.session_title}\n"
        response += f"**Unit:** {session.unit}\n"
        if session.topics:
            response += f"**Subtopics:** {session.topics}\n"
        if session.ppt_url:
            response += f"**PPT Link:** {session.ppt_url}\n"
        else:
            response += f"**PPT:** Not available yet\n"
        
        return response
    
    def _search_faqs(self, question: str) -> str:
        """Search FAQs in database for matching answer"""
        # Get all active FAQs
        faqs = self.db.query(FAQ).filter(FAQ.is_active == True).all()
        
        if not faqs:
            return None
        
        # Simple keyword matching
        question_words = set(question.lower().split())
        best_match = None
        best_score = 0
        
        for faq in faqs:
            faq_words = set(faq.question.lower().split())
            # Calculate overlap score
            common_words = question_words.intersection(faq_words)
            # Filter out common words
            common_words = {w for w in common_words if len(w) > 2 and w not in ['the', 'what', 'how', 'are', 'is', 'can', 'do', 'for']}
            score = len(common_words)
            
            if score > best_score:
                best_score = score
                best_match = faq
        
        # Return if we have a reasonable match (at least 2 meaningful words)
        if best_match and best_score >= 2:
            return f"💡 **{best_match.question}**\n\n{best_match.answer}"
        
        return None


def process_chatbot_query(query: str, db: Session) -> str:
    """Main function to process chatbot queries"""
    chatbot = FAQChatbot(db)
    return chatbot.process_question(query)
