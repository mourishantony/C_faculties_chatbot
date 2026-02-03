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
        
        # 3. PRIORITY: Check if asking about a specific faculty member BY NAME
        faculty_response = self._check_faculty_name_query(question_lower, day_name)
        if faculty_response:
            return faculty_response
        
        # 4. Check for department-specific queries
        dept_response = self._check_department_query(question_lower, day_name)
        if dept_response:
            return dept_response
        
        # 5. Check for lab-specific queries (who has lab today, lab schedule, etc.)
        lab_response = self._check_lab_query(question_lower, day_name)
        if lab_response:
            return lab_response
        
        # 6. Check for theory-specific queries (who has theory today, etc.)
        theory_response = self._check_theory_query(question_lower, day_name)
        if theory_response:
            return theory_response
        
        # 7. Check for topics query (what topics are covered today)
        if self._is_topics_query(question_lower):
            return self._get_topics_today(day_name)
        
        # 8. Check for absent faculty query
        if self._is_absent_query(question_lower):
            return self._get_absent_faculty(day_name)
        
        # 9. Check for today's summary query
        if self._is_summary_query(question_lower):
            return self._get_today_summary(day_name)
        
        # 10. Check for general schedule queries (only if no specific faculty/dept mentioned)
        if self._is_general_schedule_query(question_lower):
            return self._get_schedule_response(day_name, question_lower)
        
        # 11. Check for "list all faculty" type queries
        if self._is_list_faculty_query(question_lower):
            return self._list_all_faculties()
        
        # 12. Check for lab program queries
        lab_match = re.search(r'(?:lab|week|w)\s*(?:program)?\s*(\d+)', question_lower)
        if lab_match:
            week_num = int(lab_match.group(1))
            return self._get_lab_program(week_num)
        
        # 13. Check for session/PPT queries
        session_match = re.search(r'(?:session|deck|ppt|slide)\s*(\d+)', question_lower)
        if session_match:
            session_num = int(session_match.group(1))
            return self._get_session_ppt(session_num)
        
        # 14. Check for period-specific queries (e.g., "period 3", "3rd period")
        period_response = self._check_period_query(question_lower, day_name)
        if period_response:
            return period_response
        
        # 15. Check for day-specific queries (e.g., "Monday schedule", "Tuesday classes")
        day_response = self._check_day_query(question_lower)
        if day_response:
            return day_response
        
        # 16. Search FAQs in database
        faq_response = self._search_faqs(question_lower)
        if faq_response:
            return faq_response
        
        # 17. Default response
        return self._default_response()
    
    def _check_period_query(self, question: str, day_name: str) -> str:
        """Check if asking about a specific period"""
        # Match patterns like "period 3", "3rd period", "period3", "in the 4th period", "what class 4th period"
        period_match = re.search(r'(?:period\s*(\d+)|(\d+)(?:st|nd|rd|th)?\s*period|in\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)?)', question)
        if period_match:
            period_num = int(period_match.group(1) or period_match.group(2) or period_match.group(3))
            return self._get_period_schedule(period_num, day_name)
        return None
    
    def _get_period_schedule(self, period: int, day_name: str) -> str:
        """Get schedule for a specific period"""
        entries = self.db.query(TimetableEntry, Faculty, Department)\
            .join(Faculty, TimetableEntry.faculty_id == Faculty.id)\
            .join(Department, TimetableEntry.department_id == Department.id)\
            .filter(TimetableEntry.day == day_name, TimetableEntry.period == period)\
            .all()
        
        if not entries:
            return f"📅 No C Programming classes in **Period {period}** on **{day_name}**."
        
        period_time = get_period_time(period, self.db)
        response = f"📅 **Period {period} ({period_time}) - {day_name}:**\n\n"
        
        for entry, faculty, dept in entries:
            response += f"• **{faculty.name}** - {dept.code} ({entry.class_type})\n"
        
        response += f"\n_Total: {len(entries)} class(es) in this period_"
        return response
    
    def _check_day_query(self, question: str) -> str:
        """Check if asking about a specific day's schedule"""
        days = {
            "monday": "Monday", "tuesday": "Tuesday", "wednesday": "Wednesday",
            "thursday": "Thursday", "friday": "Friday", "saturday": "Saturday", "sunday": "Sunday"
        }
        
        for day_key, day_name in days.items():
            if day_key in question:
                return self._get_day_schedule(day_name)
        return None
    
    def _get_day_schedule(self, day_name: str) -> str:
        """Get complete schedule for a specific day"""
        entries = self.db.query(TimetableEntry, Faculty, Department)\
            .join(Faculty, TimetableEntry.faculty_id == Faculty.id)\
            .join(Department, TimetableEntry.department_id == Department.id)\
            .filter(TimetableEntry.day == day_name)\
            .order_by(TimetableEntry.period)\
            .all()
        
        if not entries:
            return f"📅 No C Programming classes scheduled for **{day_name}**."
        
        response = f"📅 **C Programming Classes for {day_name}:**\n\n"
        
        # Group by period
        from collections import defaultdict
        period_classes = defaultdict(list)
        for entry, faculty, dept in entries:
            period_classes[entry.period].append((faculty.name, dept.code, entry.class_type))
        
        for period in sorted(period_classes.keys()):
            period_time = get_period_time(period, self.db)
            response += f"**Period {period}** ({period_time}):\n"
            for faculty_name, dept_code, class_type in period_classes[period]:
                response += f"  • {faculty_name} - {dept_code} ({class_type})\n"
            response += "\n"
        
        return response
    
    def _check_faculty_name_query(self, question: str, day_name: str) -> str:
        """Check if question mentions a specific faculty name and return their schedule"""
        faculties = self.db.query(Faculty).filter_by(is_active=True).all()
        
        for faculty in faculties:
            # Get first name and last name parts
            name_parts = faculty.name.lower().split()
            
            # Check if any significant name part is in the question
            for part in name_parts:
                if len(part) > 2 and part in question:
                    # Found a faculty name match - return their today's schedule
                    return self._get_faculty_today_schedule(faculty, day_name)
        
        return None
    
    def _get_faculty_today_schedule(self, faculty: Faculty, day_name: str) -> str:
        """Get today's schedule for a specific faculty"""
        entries = self.db.query(TimetableEntry, Department)\
            .join(Department, TimetableEntry.department_id == Department.id)\
            .filter(TimetableEntry.faculty_id == faculty.id, TimetableEntry.day == day_name)\
            .order_by(TimetableEntry.period)\
            .all()
        
        if not entries:
            return f"📅 **{faculty.name}** has no classes scheduled for **{day_name}**."
        
        response = f"📅 **{faculty.name}'s Schedule for {day_name}:**\n\n"
        
        for entry, dept in entries:
            period_time = get_period_time(entry.period, self.db)
            response += f"• **Period {entry.period}** ({period_time}) - {dept.code} ({entry.class_type})\n"
        
        response += f"\n_Total: {len(entries)} class(es) today_"
        return response
    
    def _check_department_query(self, question: str, day_name: str) -> str:
        """Check if question asks about a specific department"""
        # Full department codes with hyphens
        dept_codes_with_hyphen = ["AIDS-A", "AIDS-B", "AIML-A", "AIML-B", "CSE-A", "CSE-B", 
                                  "ECE-A", "ECE-B", "IT-A", "IT-B"]
        
        # Single word department codes (need word boundary check)
        single_dept_codes = ["CSBS", "CYS", "MECH", "RA"]
        
        question_normalized = question.replace("-", "").replace(" ", "").lower()
        
        # First check hyphenated codes (more specific)
        for code in dept_codes_with_hyphen:
            code_normalized = code.lower().replace("-", "")
            if code_normalized in question_normalized:
                return self._get_department_schedule(code, day_name)
        
        # For single codes, use word boundary matching
        import re
        for code in single_dept_codes:
            # Match as standalone word (not part of another word like "programming" for "RA")
            pattern = r'\b' + code.lower() + r'\b'
            if re.search(pattern, question):
                return self._get_department_schedule(code, day_name)
        
        return None
    
    def _get_department_schedule(self, dept_code: str, day_name: str) -> str:
        """Get today's schedule for a specific department"""
        entries = self.db.query(TimetableEntry, Faculty, Department)\
            .join(Faculty, TimetableEntry.faculty_id == Faculty.id)\
            .join(Department, TimetableEntry.department_id == Department.id)\
            .filter(Department.code == dept_code, TimetableEntry.day == day_name)\
            .order_by(TimetableEntry.period)\
            .all()
        
        if not entries:
            return f"📅 No C Programming classes for **{dept_code}** on **{day_name}**."
        
        response = f"📅 **{dept_code} Schedule for {day_name}:**\n\n"
        
        for entry, faculty, dept in entries:
            period_time = get_period_time(entry.period, self.db)
            response += f"• **Period {entry.period}** ({period_time}) - {faculty.name} ({entry.class_type})\n"
        
        return response
    
    def _check_lab_query(self, question: str, day_name: str) -> str:
        """Check if question is about lab classes"""
        lab_patterns = [
            "lab today", "today lab", "today's lab", "labs today",
            "who has lab", "who is taking lab", "lab class today",
            "lab schedule", "show lab", "lab classes"
        ]
        
        if any(pattern in question for pattern in lab_patterns):
            return self._get_class_type_schedule("lab", day_name)
        return None
    
    def _check_theory_query(self, question: str, day_name: str) -> str:
        """Check if question is about theory classes"""
        theory_patterns = [
            "theory today", "today theory", "today's theory",
            "who has theory", "who is taking theory", "theory class today",
            "theory schedule", "show theory", "theory classes"
        ]
        
        if any(pattern in question for pattern in theory_patterns):
            return self._get_class_type_schedule("theory", day_name)
        return None
    
    def _get_class_type_schedule(self, class_type: str, day_name: str) -> str:
        """Get schedule for a specific class type (lab, theory, mini_project)"""
        entries = self.db.query(TimetableEntry, Faculty, Department)\
            .join(Faculty, TimetableEntry.faculty_id == Faculty.id)\
            .join(Department, TimetableEntry.department_id == Department.id)\
            .filter(TimetableEntry.day == day_name, TimetableEntry.class_type == class_type)\
            .order_by(TimetableEntry.period)\
            .all()
        
        type_emoji = "🔬" if class_type == "lab" else "📖" if class_type == "theory" else "📝"
        type_title = class_type.replace("_", " ").title()
        
        if not entries:
            return f"{type_emoji} No **{type_title}** classes scheduled for **{day_name}**."
        
        response = f"{type_emoji} **{type_title} Classes for {day_name}:**\n\n"
        
        # Group by period
        from collections import defaultdict
        period_classes = defaultdict(list)
        for entry, faculty, dept in entries:
            period_classes[entry.period].append((faculty.name, dept.code))
        
        for period in sorted(period_classes.keys()):
            period_time = get_period_time(period, self.db)
            response += f"**Period {period}** ({period_time}):\n"
            for faculty_name, dept_code in period_classes[period]:
                response += f"  • {faculty_name} - {dept_code}\n"
            response += "\n"
        
        response += f"_Total: {len(entries)} {class_type} class(es) today_"
        return response
    
    def _is_general_schedule_query(self, question: str) -> bool:
        """Check if question is a general schedule query (no specific faculty/dept)"""
        schedule_patterns = [
            "show schedule", "today schedule", "schedule today", "today's schedule",
            "show classes", "classes today", "today's classes", "today classes",
            "who has class", "who is teaching", "teaching today", "all classes",
            "show timetable", "timetable today", "today's timetable",
            "show today", "today show", "schedule", "shedule",  # common misspelling
            "c programming classes today", "what are the classes", "what classes",
            "c class today", "programming classes"
        ]
        return any(pattern in question for pattern in schedule_patterns)
    
    def _is_absent_query(self, question: str) -> bool:
        """Check if asking about absent faculty"""
        absent_patterns = [
            "who is absent", "absent today", "who's absent", "absent faculty",
            "not teaching", "no class today", "free today", "who is free",
            "who doesn't have class", "who does not have class"
        ]
        return any(pattern in question for pattern in absent_patterns)
    
    def _get_absent_faculty(self, day_name: str) -> str:
        """Get faculty members who marked themselves as absent today"""
        from models import DailyEntry
        today = date.today()
        
        # Get faculty who marked themselves as absent in daily entries
        absent_entries = self.db.query(DailyEntry, Faculty)\
            .join(Faculty, DailyEntry.faculty_id == Faculty.id)\
            .filter(DailyEntry.date == today, DailyEntry.is_absent == True)\
            .distinct(Faculty.id)\
            .all()
        
        if not absent_entries:
            return f"✅ **No absentees today ({day_name})!**\n\nAll faculty members are present."
        
        # Get unique faculty who are absent
        absent_faculty = {}
        for entry, faculty in absent_entries:
            if faculty.id not in absent_faculty:
                absent_faculty[faculty.id] = faculty
        
        response = f"🚫 **Absent Faculty on {day_name}:**\n\n"
        for faculty in absent_faculty.values():
            dept_code = faculty.department if faculty.department else "N/A"
            response += f"• **{faculty.name}** ({dept_code})\n"
        
        response += f"\n_Total: {len(absent_faculty)} faculty member(s) absent today_"
        return response
    
    def _is_summary_query(self, question: str) -> bool:
        """Check if asking for today's summary"""
        summary_patterns = [
            "today's summary", "todays summary", "summary today", "summary",
            "overview today", "today's overview", "daily summary", "day summary"
        ]
        return any(pattern in question for pattern in summary_patterns)
    
    def _get_today_summary(self, day_name: str) -> str:
        """Get a comprehensive summary of today's schedule"""
        # Count total classes
        total_entries = self.db.query(TimetableEntry).filter(TimetableEntry.day == day_name).count()
        
        # Count by class type
        theory_count = self.db.query(TimetableEntry)\
            .filter(TimetableEntry.day == day_name, TimetableEntry.class_type == "theory").count()
        lab_count = self.db.query(TimetableEntry)\
            .filter(TimetableEntry.day == day_name, TimetableEntry.class_type == "lab").count()
        
        # Count faculty teaching today
        faculty_teaching = self.db.query(Faculty.id).join(TimetableEntry)\
            .filter(TimetableEntry.day == day_name).distinct().count()
        
        # Total active faculty
        total_faculty = self.db.query(Faculty).filter_by(is_active=True).count()
        
        # Count departments with classes
        depts_with_classes = self.db.query(TimetableEntry.department_id)\
            .filter(TimetableEntry.day == day_name).distinct().count()
        
        response = f"📊 **Today's Summary ({day_name}):**\n\n"
        response += f"**Classes:**\n"
        response += f"• Total Classes: **{total_entries}**\n"
        response += f"• Theory Classes: **{theory_count}**\n"
        response += f"• Lab Classes: **{lab_count}**\n\n"
        
        response += f"**Faculty:**\n"
        response += f"• Teaching Today: **{faculty_teaching}** of {total_faculty}\n"
        response += f"• Free Today: **{total_faculty - faculty_teaching}**\n\n"
        
        response += f"**Departments:**\n"
        response += f"• With Classes: **{depts_with_classes}**\n\n"
        
        response += "_Ask 'who has class today' or 'who is absent today' for details_"
        return response
    
    def _is_topics_query(self, question: str) -> bool:
        """Check if asking about topics covered today"""
        topic_patterns = [
            "topics today", "today topics", "topics covered", "what topics", 
            "syllabus today", "topics being taught", "what is being taught",
            "what are being taught", "taught today"
        ]
        return any(pattern in question for pattern in topic_patterns)
    
    def _get_topics_today(self, day_name: str) -> str:
        """Get topics being covered today based on daily entries or syllabus"""
        from models import DailyEntry, Syllabus
        today = date.today()
        
        # Get daily entries for today
        entries = self.db.query(DailyEntry, Faculty, Department, Syllabus)\
            .join(Faculty, DailyEntry.faculty_id == Faculty.id)\
            .join(Department, DailyEntry.department_id == Department.id)\
            .outerjoin(Syllabus, DailyEntry.syllabus_id == Syllabus.id)\
            .filter(DailyEntry.date == today)\
            .all()
        
        if not entries:
            # No daily entries yet, show syllabus overview
            syllabus = self.db.query(Syllabus).order_by(Syllabus.session_number).limit(5).all()
            if syllabus:
                response = f"📚 **Topics Overview (No entries for {day_name} yet):**\n\n"
                response += "Faculty members haven't logged their sessions yet. Here are upcoming topics:\n\n"
                for s in syllabus:
                    response += f"• **Session {s.session_number}:** {s.session_title}\n"
                response += "\n_Ask 'session [number]' for detailed topic info._"
                return response
            return "No syllabus information available."
        
        response = f"📚 **Topics Covered on {day_name}:**\n\n"
        
        for entry, faculty, dept, syllabus in entries:
            response += f"• **{faculty.name}** ({dept.code}):\n"
            if syllabus:
                response += f"  Session {syllabus.session_number}: {syllabus.session_title}\n"
            elif entry.own_content_title:
                response += f"  {entry.own_content_title}\n"
            else:
                response += f"  {entry.class_type.capitalize()} class\n"
        
        return response
    
    def _is_list_faculty_query(self, question: str) -> bool:
        """Check if asking to list all faculties"""
        list_patterns = [
            "list all faculty", "all faculty", "list faculty", "show faculty", 
            "faculty list", "all faculties", "list all faculties", "list faculties",
            "c programming faculties", "c programming faculty", "programming faculty",
            "who are the faculty", "who are the faculties"
        ]
        return any(pattern in question for pattern in list_patterns)
    
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
• "[Faculty name]" - e.g., "Sathish" or "Priya"
• "period 3" or "3rd period"
• "Monday schedule" or "Tuesday classes"

**Lab/Theory Queries:**
• "Lab today" or "Who has lab today?"
• "Theory classes today"
• "[Department] schedule" - e.g., "AIDS-A", "CSE-B"

**Faculty Queries:**
• "List all faculty"
• "Who teaches AIDS-A?"

**Lab Programs:**
• "Lab program week 3"
• "Week 5 lab"

**Session/PPT:**
• "Session 3 PPT"
• "Deck 5"

**Topics:**
• "Topics today"

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
        
        # Stop words to filter out
        stop_words = {'the', 'what', 'how', 'are', 'is', 'can', 'do', 'for', 'in', 'on', 'at', 
                     'to', 'a', 'an', 'of', 'and', 'or', 'but', 'who', 'when', 'where', 'why',
                     'this', 'that', 'i', 'you', 'we', 'they', 'it', 'my', 'your'}
        
        question_words = set(question.lower().split())
        question_words = {w for w in question_words if len(w) > 2 and w not in stop_words}
        
        best_match = None
        best_score = 0
        
        for faq in faqs:
            score = 0
            faq_question_lower = faq.question.lower()
            faq_answer_lower = faq.answer.lower()
            
            # Strategy 1: Exact match
            if question == faq_question_lower:
                score = 1000
            
            # Strategy 2: Question contains FAQ question or vice versa
            elif faq_question_lower in question or question in faq_question_lower:
                score = 500
            
            # Strategy 3: Word overlap
            else:
                faq_words = set(faq_question_lower.split())
                faq_words = {w for w in faq_words if len(w) > 2 and w not in stop_words}
                
                common_words = question_words.intersection(faq_words)
                score = len(common_words) * 10
                
                # Bonus: check if keywords appear in answer
                for word in question_words:
                    if word in faq_answer_lower:
                        score += 5
            
            if score > best_score:
                best_score = score
                best_match = faq
        
        # Return if we have a reasonable match
        if best_match and best_score >= 10:
            return f"💡 **{best_match.question}**\n\n{best_match.answer}"
        
        return None


def process_chatbot_query(query: str, db: Session) -> str:
    """Main function to process chatbot queries"""
    chatbot = FAQChatbot(db)
    return chatbot.process_question(query)
