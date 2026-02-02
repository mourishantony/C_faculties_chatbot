from sqlalchemy.orm import Session
from models import Faculty, LabProgram, Syllabus, TimetableEntry, Department, DailyEntry, PeriodTiming
from datetime import datetime, date
import re

class ChatbotService:
    def __init__(self, db: Session):
        self.db = db
    
    def process_question(self, question: str) -> str:
        """Process the admin's question and return an answer"""
        question = question.lower().strip()
        
        # Get today's date and day
        today = date.today()
        today_name = datetime.now().strftime("%A")
        
        # Intent 0: Absence queries
        if any(word in question for word in ["absent", "leave", "not present", "missing", "away"]):
            if "today" in question:
                return self._get_absent_faculties(today_name)
        
        # Intent 1: Who has class today / Schedule queries
        schedule_keywords = ["who has", "who is having", "who got", "classes today", "teaching today", 
                           "class today", "schedule today", "today class", "today schedule"]
        if any(keyword in question for keyword in schedule_keywords):
            if "c period" in question or "c programming" in question or "period" in question:
                return self._get_faculty_with_class_today(today_name)
            elif "schedule" in question or "all" in question or "complete" in question:
                return self._get_todays_schedule(today_name)
        
        # Intent 2: Lab program queries (multiple patterns)
        lab_patterns = [
            r"lab\s*(?:program)?\s*(?:for)?\s*week\s*(\d+)",
            r"week\s*(\d+)\s*lab",
            r"w(\d+)\s*lab",
            r"inlab\s*(\d+)",
            r"lab\s*(\d+)"
        ]
        for pattern in lab_patterns:
            match = re.search(pattern, question)
            if match:
                week_num = int(match.group(1))
                return self._get_lab_program(week_num)
        
        # Intent 3: PPT/Deck/Session queries (multiple patterns)
        session_patterns = [
            r"session\s*(\d+)",
            r"ses\s*(\d+)",
            r"deck\s*(\d+)",
            r"ppt\s*(?:for)?\s*(?:session)?\s*(\d+)",
            r"slide\s*(\d+)"
        ]
        if any(word in question for word in ["ppt", "deck", "session", "slide", "presentation"]):
            for pattern in session_patterns:
                match = re.search(pattern, question)
                if match:
                    session_num = int(match.group(1))
                    return self._get_session_ppt(session_num)
        
        # Intent 4: Moodle link queries
        if "moodle" in question:
            match = re.search(r"week\s*(\d+)", question)
            if match:
                week_num = int(match.group(1))
                return self._get_lab_program(week_num)
        
        # Intent 5: Faculty by department
        dept_codes = ["AIDS-A", "AIDS-B", "AIML-A", "AIML-B", "CSE-A", "CSE-B", 
                     "CSBS", "CYS", "ECE-A", "ECE-B", "IT-A", "IT-B", "MECH", "RA"]
        if any(word in question for word in ["faculty", "teacher", "teaching", "instructor", "who"]):
            for code in dept_codes:
                # Match variations like "aids a", "aidsa", "aids-a"
                code_normalized = code.lower().replace("-", "").replace(" ", "")
                question_normalized = question.replace("-", "").replace(" ", "")
                if code_normalized in question_normalized:
                    return self._get_faculty_by_department(code, today_name)
        
        # Intent 6: List/Show all faculties
        list_keywords = ["list", "show", "all", "every", "display"]
        faculty_keywords = ["facult", "teacher", "instructor", "staff"]
        if any(l in question for l in list_keywords) and any(f in question for f in faculty_keywords):
            return self._list_all_faculties()
        
        # Intent 7: Recent teaching/daily entries
        if any(phrase in question for phrase in ["what was taught", "what did", "recently taught", 
                                                  "recent class", "last class", "previous class",
                                                  "teaching history", "class history"]):
            return self._get_recent_daily_entries()
        
        # Intent 8: Specific day schedule
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in days:
            if day in question and "schedule" in question:
                return self._get_todays_schedule(day.capitalize())
        
        # Intent 9: Help/What can you do
        if any(word in question for word in ["help", "what can", "how to", "guide", "commands"]):
            return self._get_help_message()
        
        # Intent 10: Greetings
        if any(word in question for word in ["hi", "hello", "hey", "greetings"]):
            return f"Hello Admin! How can I assist you today?\n\n{self._get_help_message()}"
        
        # Default: Try to be helpful
        return f"I'm not sure I understood that question. {self._get_help_message()}"
    
    def _get_absent_faculties(self, day: str) -> str:
        """Check which faculties are absent (scheduled but not present)"""
        # Get all faculties who have classes scheduled today
        scheduled_faculties = self.db.query(Faculty)\
            .join(TimetableEntry, TimetableEntry.faculty_id == Faculty.id)\
            .filter(TimetableEntry.day == day)\
            .distinct()\
            .all()
        
        if not scheduled_faculties:
            return f"No classes scheduled for {day}, so no faculty absences to track."
        
        # For now, we assume all scheduled faculty are present
        # In a real system, you'd have an Attendance or Absence table
        response = f"**Faculty Status for {day}:**\n\n"
        response += f"**All {len(scheduled_faculties)} scheduled faculties are present:**\n\n"
        
        for faculty in scheduled_faculties:
            # Get their periods
            periods = self.db.query(TimetableEntry)\
                .filter(TimetableEntry.faculty_id == faculty.id, TimetableEntry.day == day)\
                .all()
            
            period_list = ", ".join([f"Period {p.period}" for p in periods])
            response += f"• **{faculty.name}** - {period_list}\n"
        
        response += "\n*Note: To track absences, mark faculty as absent in the system.*"
        return response
    
    def _get_faculty_with_class_today(self, day: str) -> str:
        """Get all faculties who have classes today"""
        entries = self.db.query(TimetableEntry, Faculty, Department)\
            .join(Faculty, TimetableEntry.faculty_id == Faculty.id)\
            .join(Department, TimetableEntry.department_id == Department.id)\
            .filter(TimetableEntry.day == day)\
            .order_by(TimetableEntry.period)\
            .all()
        
        if not entries:
            return f"No C Programming classes scheduled for {day}."
        
        response = f"**C Programming Classes on {day}:**\n\n"
        for entry, faculty, dept in entries:
            timing = self.db.query(PeriodTiming).filter_by(period=entry.period).first()
            time_str = timing.display_time if timing else f"Period {entry.period}"
            response += f"• **{faculty.name}** - {dept.name}\n"
            response += f"  Period {entry.period} ({time_str}) - {entry.class_type.title()}\n\n"
        
        return response
    
    def _get_lab_program(self, week_num: int) -> str:
        """Get lab program details for a specific week"""
        program = self.db.query(LabProgram).filter_by(program_number=week_num).first()
        
        if not program:
            return f"No lab program found for Week {week_num}."
        
        response = f"**Lab Program - Week {week_num}:**\n\n"
        response += f"**Title:** {program.program_title}\n\n"
        response += f"**Description:** {program.description}\n\n"
        if program.moodle_url:
            response += f"**Moodle Link:** {program.moodle_url}\n"
        else:
            response += "**Moodle Link:** Not available yet\n"
        
        return response
    
    def _get_session_ppt(self, session_num: int) -> str:
        """Get PPT/deck details for a specific session"""
        session = self.db.query(Syllabus).filter_by(session_number=session_num).first()
        
        if not session:
            return f"No session found for Session {session_num}."
        
        response = f"**Session {session_num}:**\n\n"
        response += f"**Title:** {session.session_title}\n"
        response += f"**Unit:** {session.unit}\n\n"
        response += f"**Topics:** {session.topics}\n\n"
        if session.ppt_url:
            response += f"**PPT Link:** {session.ppt_url}\n"
        else:
            response += "**PPT Link:** Not available yet\n"
        
        return response
    
    def _get_faculty_by_department(self, dept_code: str, day: str) -> str:
        """Get faculty teaching a specific department"""
        entry = self.db.query(TimetableEntry, Faculty, Department)\
            .join(Faculty, TimetableEntry.faculty_id == Faculty.id)\
            .join(Department, TimetableEntry.department_id == Department.id)\
            .filter(Department.code == dept_code)\
            .filter(TimetableEntry.day == day)\
            .first()
        
        if not entry:
            return f"No faculty found teaching {dept_code} on {day}."
        
        timetable, faculty, dept = entry
        
        response = f"**Faculty for {dept.name}:**\n\n"
        response += f"**Name:** {faculty.name}\n"
        response += f"**Email:** {faculty.email}\n"
        response += f"**Phone:** {faculty.phone}\n"
        response += f"**Experience:** {faculty.experience} years\n"
        if faculty.research_area:
            response += f"**Research Area:** {faculty.research_area}\n"
        
        return response
    
    def _list_all_faculties(self) -> str:
        """List all faculties"""
        faculties = self.db.query(Faculty).filter_by(is_active=True).all()
        
        if not faculties:
            return "No faculties found."
        
        response = f"**All Faculties ({len(faculties)}):**\n\n"
        for fac in faculties:
            response += f"• **{fac.name}** ({fac.department})\n"
            response += f"  {fac.email} | {fac.phone}\n\n"
        
        return response
    
    def _get_todays_schedule(self, day: str) -> str:
        """Get complete schedule for today"""
        entries = self.db.query(TimetableEntry, Faculty, Department)\
            .join(Faculty, TimetableEntry.faculty_id == Faculty.id)\
            .join(Department, TimetableEntry.department_id == Department.id)\
            .filter(TimetableEntry.day == day)\
            .order_by(TimetableEntry.period)\
            .all()
        
        if not entries:
            return f"No classes scheduled for {day}."
        
        response = f"**Complete Schedule for {day}:**\n\n"
        
        # Group by department
        dept_schedule = {}
        for entry, faculty, dept in entries:
            if dept.name not in dept_schedule:
                dept_schedule[dept.name] = []
            dept_schedule[dept.name].append((entry, faculty))
        
        for dept_name, schedule in dept_schedule.items():
            response += f"**{dept_name}:**\n"
            for entry, faculty in schedule:
                timing = self.db.query(PeriodTiming).filter_by(period=entry.period).first()
                time_str = timing.display_time if timing else f"Period {entry.period}"
                response += f"  • Period {entry.period} ({time_str}) - {faculty.name} - {entry.class_type.title()}\n"
            response += "\n"
        
        return response
    
    def _get_recent_daily_entries(self) -> str:
        """Get recent daily entries (what was taught)"""
        entries = self.db.query(DailyEntry, Faculty, Department)\
            .join(Faculty, DailyEntry.faculty_id == Faculty.id)\
            .join(Department, DailyEntry.department_id == Department.id)\
            .order_by(DailyEntry.date.desc())\
            .limit(10)\
            .all()
        
        if not entries:
            return "No recent teaching entries found."
        
        response = f"**Recent Teaching Entries:**\n\n"
        for entry, faculty, dept in entries:
            response += f"**{entry.date.strftime('%Y-%m-%d')}** - {faculty.name} ({dept.name})\n"
            if entry.summary:
                response += f"  Summary: {entry.summary}\n"
            response += "\n"
        
        return response
    
    def _get_help_message(self) -> str:
        """Return help message with example questions"""
        return """**I can help you with:**

**Schedule Queries:**
• "Who has C period today?"
• "Show today's complete schedule"
• "Monday schedule" / "Friday schedule"
• "Who is absent today?"

**Lab Programs:**
• "Lab program for week 5"
• "Show week 3 lab" / "W3 lab"
• "Moodle link for week 2"

**Session Materials:**
• "PPT for session 3"
• "Show deck 5" / "Session 7 slides"

**Faculty Information:**
• "Who is teaching AIDS-A?"
• "Faculty for CSE-B today"
• "List all faculties"

**Teaching History:**
• "What was taught recently?"
• "Show recent classes"

Just ask naturally - I understand variations!"""
