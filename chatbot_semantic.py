from sqlalchemy.orm import Session
from models import Faculty, LabProgram, Syllabus, TimetableEntry, Department, DailyEntry, PeriodTiming
from datetime import datetime, date
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import pickle
import os

class SemanticChatbotService:
    def __init__(self, db: Session):
        self.db = db
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight, fast model
        self.index_file = "chatbot_index.faiss"
        self.intents_file = "chatbot_intents.pkl"
        
        # Initialize or load the semantic search index
        if os.path.exists(self.index_file) and os.path.exists(self.intents_file):
            self.load_index()
        else:
            self.build_index()
    
    def build_index(self):
        """Build semantic search index from example questions"""
        # Define intents with example questions
        self.intents = [
            {
                "intent": "get_schedule_today",
                "examples": [
                    "Who has C period today?",
                    "Who is teaching today?",
                    "Show today's classes",
                    "Who has class today?",
                    "Classes for today",
                    "Today's schedule",
                    "Which faculty is teaching today?",
                    "What are the C programming classes today?"
                ]
            },
            {
                "intent": "get_complete_schedule",
                "examples": [
                    "Show today's complete schedule",
                    "Full schedule for today",
                    "All classes today",
                    "Today's timetable",
                    "Complete timetable",
                    "Show all periods today"
                ]
            },
            {
                "intent": "get_absent_faculty",
                "examples": [
                    "Who is absent today?",
                    "Which faculty is absent?",
                    "Show absent teachers",
                    "Who's not present today?",
                    "Faculty on leave today",
                    "Missing faculty today"
                ]
            },
            {
                "intent": "get_lab_program",
                "examples": [
                    "Lab program for week 3",
                    "Show week 5 lab",
                    "What's the lab for week 2?",
                    "Week 7 lab program",
                    "Lab assignment week 4",
                    "Show lab 6"
                ]
            },
            {
                "intent": "get_session_ppt",
                "examples": [
                    "PPT for session 3",
                    "Show deck 5",
                    "Session 7 slides",
                    "Presentation for session 2",
                    "Slide deck 4",
                    "Session 6 PPT"
                ]
            },
            {
                "intent": "get_faculty_by_dept",
                "examples": [
                    "Who is teaching AIDS-A?",
                    "Faculty for CSE-B",
                    "Show teacher for AIML-A",
                    "Who teaches IT-A?",
                    "Faculty assigned to ECE-B",
                    "Teacher for CYS department"
                ]
            },
            {
                "intent": "get_faculty_schedule",
                "examples": [
                    "When does Sathish have class?",
                    "What is Ravi's schedule?",
                    "Show Priya's timetable",
                    "When will Kumar teach?",
                    "What days does Meena have classes?",
                    "Schedule for faculty Arun",
                    "When is teacher John's class?",
                    "What's the timetable for professor Sathish?"
                ]
            },
            {
                "intent": "list_all_faculty",
                "examples": [
                    "List all faculties",
                    "Show all teachers",
                    "Display faculty list",
                    "All instructors",
                    "Faculty members",
                    "Show all staff"
                ]
            },
            {
                "intent": "get_teaching_history",
                "examples": [
                    "What was taught recently?",
                    "Recent classes",
                    "Show teaching history",
                    "What did faculty teach?",
                    "Recent topics covered",
                    "Last class content"
                ]
            },
            {
                "intent": "help",
                "examples": [
                    "Help",
                    "What can you do?",
                    "How to use this?",
                    "Commands",
                    "Guide me",
                    "What are your features?"
                ]
            },
            {
                "intent": "greeting",
                "examples": [
                    "Hello",
                    "Hi",
                    "Hey there",
                    "Good morning",
                    "Greetings",
                    "Hi bot"
                ]
            }
        ]
        
        # Create embeddings for all example questions
        all_examples = []
        intent_map = []
        
        for intent_data in self.intents:
            for example in intent_data["examples"]:
                all_examples.append(example)
                intent_map.append(intent_data["intent"])
        
        # Generate embeddings
        embeddings = self.model.encode(all_examples)
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))
        self.intent_map = intent_map
        
        # Save index and intent mapping
        faiss.write_index(self.index, self.index_file)
        with open(self.intents_file, 'wb') as f:
            pickle.dump({'intent_map': self.intent_map, 'intents': self.intents}, f)
        
        print(f"Built semantic index with {len(all_examples)} examples")
    
    def load_index(self):
        """Load pre-built semantic search index"""
        self.index = faiss.read_index(self.index_file)
        with open(self.intents_file, 'rb') as f:
            data = pickle.load(f)
            self.intent_map = data['intent_map']
            self.intents = data['intents']
        print(f"Loaded semantic index with {len(self.intent_map)} examples")
    
    def process_question(self, question: str) -> str:
        """Process the admin's question using semantic search"""
        # Encode the question
        query_embedding = self.model.encode([question])
        
        # Search for most similar intent
        k = 3  # Get top 3 matches
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Get the best matching intent
        best_match_idx = indices[0][0]
        best_distance = distances[0][0]
        intent = self.intent_map[best_match_idx]
        
        # Debug: Check confidence (lower distance = better match)
        # If distance is too high, the match is poor
        confidence_threshold = 0.8  # Stricter threshold
        
        if best_distance > confidence_threshold:
            return f"I'm not sure I understood that question.\n\n{self._get_help_message()}"
        
        # Get today's info
        today = date.today()
        today_name = datetime.now().strftime("%A")
        
        # Route to appropriate handler based on intent
        if intent == "get_schedule_today":
            return self._get_faculty_with_class_today(today_name)
        
        elif intent == "get_complete_schedule":
            return self._get_todays_schedule(today_name)
        
        elif intent == "get_absent_faculty":
            return self._get_absent_faculties(today_name)
        
        elif intent == "get_lab_program":
            # Extract week number using basic pattern
            import re
            match = re.search(r'\d+', question)
            if match:
                week_num = int(match.group())
                return self._get_lab_program(week_num)
            return "Please specify a week number (e.g., 'Lab program for week 3')"
        
        elif intent == "get_session_ppt":
            # Extract session number
            import re
            match = re.search(r'\d+', question)
            if match:
                session_num = int(match.group())
                return self._get_session_ppt(session_num)
            return "Please specify a session number (e.g., 'PPT for session 5')"
        
        elif intent == "get_faculty_by_dept":
            # Extract department code
            dept_codes = ["AIDS-A", "AIDS-B", "AIML-A", "AIML-B", "CSE-A", "CSE-B", 
                         "CSBS", "CYS", "ECE-A", "ECE-B", "IT-A", "IT-B", "MECH", "RA"]
            for code in dept_codes:
                if code.lower().replace("-", "").replace(" ", "") in question.lower().replace("-", "").replace(" ", ""):
                    return self._get_faculty_by_department(code, today_name)
            return "Please specify a department (e.g., 'Who is teaching AIDS-A?')"
        
        elif intent == "get_faculty_schedule":
            # Extract faculty name from question
            return self._get_faculty_schedule_by_name(question)
        
        elif intent == "list_all_faculty":
            return self._list_all_faculties()
        
        elif intent == "get_teaching_history":
            return self._get_recent_daily_entries()
        
        elif intent == "help":
            return self._get_help_message()
        
        elif intent == "greeting":
            return f"Hello Admin! How can I assist you today?\n\n{self._get_help_message()}"
        
        return self._get_help_message()
    
    # ==================== Database Query Methods ====================
    
    def _get_faculty_schedule_by_name(self, question: str) -> str:
        """Get schedule for a specific faculty member by name"""
        # Get all active faculties
        faculties = self.db.query(Faculty).filter_by(is_active=True).all()
        
        # Find faculty whose name appears in the question
        question_lower = question.lower()
        matched_faculty = None
        
        for faculty in faculties:
            # Check if any part of the faculty name is in the question
            name_parts = faculty.name.lower().split()
            if any(part in question_lower for part in name_parts if len(part) > 2):
                matched_faculty = faculty
                break
        
        if not matched_faculty:
            return "I couldn't find that faculty member. Please check the name and try again, or type 'list all faculties' to see all faculty names."
        
        # Get their timetable entries
        entries = self.db.query(TimetableEntry, Department)\
            .join(Department, TimetableEntry.department_id == Department.id)\
            .filter(TimetableEntry.faculty_id == matched_faculty.id)\
            .order_by(TimetableEntry.day, TimetableEntry.period)\
            .all()
        
        if not entries:
            return f"**{matched_faculty.name}** has no scheduled classes."
        
        response = f"**Schedule for {matched_faculty.name}:**\n\n"
        
        # Group by day
        from collections import defaultdict
        schedule_by_day = defaultdict(list)
        
        for entry, dept in entries:
            schedule_by_day[entry.day].append((entry.period, dept.name))
        
        # Display schedule
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        for day in days_order:
            if day in schedule_by_day:
                periods = sorted(schedule_by_day[day])
                period_str = ", ".join([f"Period {p[0]} ({p[1]})" for p in periods])
                response += f"**{day}:** {period_str}\n"
        
        return response
    
    def _get_absent_faculties(self, day: str) -> str:
        """Check which faculties are absent"""
        scheduled_faculties = self.db.query(Faculty)\
            .join(TimetableEntry, TimetableEntry.faculty_id == Faculty.id)\
            .filter(TimetableEntry.day == day)\
            .distinct()\
            .all()
        
        if not scheduled_faculties:
            return f"No classes scheduled for {day}, so no faculty absences to track."
        
        response = f"**Faculty Status for {day}:**\n\n"
        response += f"**All {len(scheduled_faculties)} scheduled faculties are present:**\n\n"
        
        for faculty in scheduled_faculties:
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
        
        response = f"**Faculties with classes on {day}:**\n\n"
        faculty_seen = set()
        
        for entry, faculty, dept in entries:
            if faculty.id not in faculty_seen:
                periods = [e.period for e, f, d in entries if f.id == faculty.id]
                period_str = ", ".join(map(str, sorted(periods)))
                response += f"• **{faculty.name}** - Period(s): {period_str} ({dept.name})\n"
                faculty_seen.add(faculty.id)
        
        return response
    
    def _get_lab_program(self, week_num: int) -> str:
        """Get lab program for specific week"""
        program = self.db.query(LabProgram).filter(LabProgram.program_number == week_num).first()
        
        if not program:
            return f"No lab program found for week {week_num}."
        
        response = f"**Lab Program - Week {week_num}:**\n\n"
        response += f"**Title:** {program.program_title}\n"
        response += f"**Description:** {program.description}\n"
        
        if program.moodle_url:
            response += f"**Moodle Link:** {program.moodle_url}\n"
        else:
            response += f"**Moodle Link:** Not available yet\n"
        
        return response
    
    def _get_session_ppt(self, session_num: int) -> str:
        """Get PPT for specific session"""
        session = self.db.query(Syllabus).filter(Syllabus.session_number == session_num).first()
        
        if not session:
            return f"No session {session_num} found in syllabus."
        
        response = f"**Session {session_num}:**\n\n"
        response += f"**Topic:** {session.topic}\n"
        response += f"**Subtopics:** {session.subtopics}\n"
        
        if session.ppt_url:
            response += f"**PPT Link:** {session.ppt_url}\n"
        else:
            response += f"**PPT Link:** Not available yet\n"
        
        return response
    
    def _get_faculty_by_department(self, dept_code: str, day: str) -> str:
        """Get faculty teaching specific department"""
        entry = self.db.query(TimetableEntry, Faculty, Department)\
            .join(Faculty, TimetableEntry.faculty_id == Faculty.id)\
            .join(Department, TimetableEntry.department_id == Department.id)\
            .filter(Department.code == dept_code, TimetableEntry.day == day)\
            .first()
        
        if not entry:
            return f"No faculty assigned to {dept_code} for {day}."
        
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
        for entry, faculty, dept in entries:
            response += f"**Period {entry.period}** - {faculty.name} ({dept.name})\n"
        
        return response
    
    def _get_recent_daily_entries(self, limit: int = 5) -> str:
        """Get recent teaching entries"""
        entries = self.db.query(DailyEntry, Faculty, Department)\
            .join(Faculty, DailyEntry.faculty_id == Faculty.id)\
            .join(Department, DailyEntry.department_id == Department.id)\
            .order_by(DailyEntry.date.desc())\
            .limit(limit)\
            .all()
        
        if not entries:
            return "No recent teaching records found."
        
        response = f"**Recent Teaching Entries:**\n\n"
        for entry, faculty, dept in entries:
            response += f"**{entry.date.strftime('%Y-%m-%d')}** - {faculty.name} ({dept.name})\n"
            response += f"  Period: {entry.period}, Type: {entry.class_type}\n\n"
        
        return response
    
    def _get_help_message(self) -> str:
        """Return help message"""
        return """**I can help you with:**

**Schedule Queries:**
• "Who has C period today?"
• "Show today's complete schedule"
• "Monday schedule" / "Friday schedule"
• "Who is absent today?"
• "When does Sathish have class?"

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

I understand natural language - just ask!"""
