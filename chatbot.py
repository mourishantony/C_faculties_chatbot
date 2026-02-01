from datetime import date, datetime
from sqlalchemy.orm import Session
from models import Faculty, Department, TimetableEntry, DailyEntry, Syllabus, PeriodTiming, LabProgram
import re

def get_day_name(d: date = None):
    if d is None:
        d = date.today()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[d.weekday()]

def get_period_time(period: int, db: Session = None) -> str:
    # Try to get from database first
    if db:
        timing = db.query(PeriodTiming).filter(PeriodTiming.period == period).first()
        if timing:
            return timing.display_time
    
    # Fallback to hardcoded values
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

def get_period_ordinal(period: int) -> str:
    ordinals = {
        1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th",
        6: "6th", 7: "7th", 8: "8th", 9: "9th"
    }
    return ordinals.get(period, f"{period}th")

def process_chatbot_query(query: str, db: Session) -> str:
    query_lower = query.lower().strip()
    today = date.today()
    day_name = get_day_name(today)
    
    # Greetings
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    if any(g in query_lower for g in greetings):
        # Check if asking about classes
        if "class" in query_lower or "c programming" in query_lower or "prog c" in query_lower:
            return get_today_classes_response(db, day_name, today)
        return f"Hello! Welcome to C Programming Faculty Management System. How can I help you today? You can ask me about:\n- Today's C programming classes\n- Which faculty has class today\n- What topic will be taught\n- Class schedules for any department"
    
    # What classes today / classes today
    if ("class" in query_lower and "today" in query_lower) or \
       ("c programming" in query_lower and "today" in query_lower) or \
       "what are the" in query_lower:
        return get_today_classes_response(db, day_name, today)
    
    # Ask about specific faculty
    faculty_match = None
    faculties = db.query(Faculty).all()
    for faculty in faculties:
        if faculty.name.lower() in query_lower:
            faculty_match = faculty
            break
        # Check partial name match
        name_parts = faculty.name.lower().split()
        for part in name_parts:
            if len(part) > 3 and part in query_lower:
                faculty_match = faculty
                break
    
    if faculty_match:
        if "topic" in query_lower or "teach" in query_lower or "going to take" in query_lower or "syllabus" in query_lower:
            return get_faculty_topic_response(db, faculty_match, today)
        elif "class" in query_lower or "schedule" in query_lower or "have" in query_lower:
            return get_faculty_schedule_response(db, faculty_match, day_name, today)
        else:
            # Default to schedule if faculty is mentioned
            return get_faculty_schedule_response(db, faculty_match, day_name, today)
    
    # List all faculties - CHECK BEFORE department matching to avoid false matches
    if ("faculty" in query_lower or "faculties" in query_lower or "staff" in query_lower) and \
       ("list" in query_lower or "all" in query_lower or "show" in query_lower):
        return get_all_faculties_response(db)
    
    # Ask about specific department - be more specific in matching
    departments = db.query(Department).all()
    dept_match = None
    for dept in departments:
        dept_code_lower = dept.code.lower()
        # Only match exact code or explicit department name mentions
        # Avoid matching "RA" in "programming" etc.
        if dept_code_lower in query_lower.split() or \
           dept.name.lower() in query_lower or \
           dept_code_lower + " " in query_lower or \
           " " + dept_code_lower in query_lower or \
           dept_code_lower + "?" in query_lower:
            dept_match = dept
            break
    
    if dept_match:
        return get_department_schedule_response(db, dept_match, day_name, today)
    
    # What topic / what will be taught
    if "topic" in query_lower or "what will" in query_lower or "going to teach" in query_lower or "going to take" in query_lower:
        return get_all_topics_today_response(db, today)
    
    # Period specific queries
    period_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*period', query_lower)
    if period_match:
        period = int(period_match.group(1))
        return get_period_class_response(db, period, day_name, today)
    
    # Who is absent today
    if "absent" in query_lower:
        return get_absent_today_response(db, today)
    
    # Today's summary
    if "summary" in query_lower and "today" in query_lower:
        return get_today_summary_response(db, day_name, today)
    
    # Help
    if "help" in query_lower or "what can you" in query_lower:
        return """I can help you with information about C Programming classes. Try asking:

📚 **Class Schedules:**
- "What are the C programming classes today?"
- "Who has class today?"
- "What classes are in the 4th period?"

👨‍🏫 **Faculty Information:**
- "Does [faculty name] have class today?"
- "What topic will [faculty name] teach?"
- "List all faculties"

🏫 **Department Classes:**
- "When is the C class for AIDS-A?"
- "Who teaches CSE-B?"

📖 **Syllabus & Sessions:**
- "What topics are being taught today?"
- "Show session 5" or "What is session 10 about?"
- "List all sessions" or "Show syllabus"
- "Get PPT for session 3"

🔬 **Lab Programs:**
- "List lab programs" or "Show all labs"
- "What is lab 5 about?"
- "Lab programs for arrays"

💡 **Tip:** Just type any faculty name to check their schedule!
"""

    # Session queries
    session_match = re.search(r'session\s*(\d+)', query_lower)
    if session_match:
        session_num = int(session_match.group(1))
        return get_session_info_response(db, session_num)
    
    # PPT/Deck queries
    if "ppt" in query_lower or "deck" in query_lower or "slides" in query_lower or "presentation" in query_lower:
        ppt_session_match = re.search(r'(?:ppt|deck|slides|presentation).*?(?:session|for)?\s*(\d+)', query_lower)
        if ppt_session_match:
            session_num = int(ppt_session_match.group(1))
            return get_session_ppt_response(db, session_num)
        return get_all_ppts_response(db)
    
    # List all sessions / syllabus
    if ("session" in query_lower and ("all" in query_lower or "list" in query_lower or "show" in query_lower)) or \
       "syllabus" in query_lower:
        return get_all_sessions_response(db)
    
    # Lab program queries
    lab_match = re.search(r'lab\s*(?:program)?\s*(\d+)', query_lower)
    if lab_match:
        lab_num = int(lab_match.group(1))
        return get_lab_program_response(db, lab_num)
    
    # List all lab programs
    if ("lab" in query_lower and ("all" in query_lower or "list" in query_lower or "show" in query_lower)) or \
       "lab programs" in query_lower:
        return get_all_lab_programs_response(db)
    
    # Default response
    return f"""I'm sorry, I didn't understand your question. 

Today is **{day_name}, {today.strftime('%B %d, %Y')}**.

You can ask me about:
- Today's C programming classes
- Faculty schedules
- Topics being taught
- Department-wise class timings

Try asking: "What are the C programming classes today?" """


def get_today_classes_response(db: Session, day_name: str, today: date) -> str:
    # Get all timetable entries for today
    entries = db.query(TimetableEntry).filter(TimetableEntry.day == day_name).all()
    
    if not entries:
        return f"📅 No C Programming classes are scheduled for {day_name}."
    
    response = f"📚 **C Programming Classes for Today ({day_name}, {today.strftime('%B %d, %Y')}):**\n\n"
    
    # Sort by period
    entries = sorted(entries, key=lambda x: x.period)
    
    for entry in entries:
        faculty = db.query(Faculty).filter(Faculty.id == entry.faculty_id).first()
        dept = db.query(Department).filter(Department.id == entry.department_id).first()
        
        # Check if there's a daily entry for today
        daily = db.query(DailyEntry).filter(
            DailyEntry.faculty_id == entry.faculty_id,
            DailyEntry.department_id == entry.department_id,
            DailyEntry.date == today,
            DailyEntry.period == entry.period
        ).first()
        
        status = ""
        topic = ""
        ppt_url = ""
        if daily:
            if daily.is_absent:
                status = " ❌ (Faculty Absent)"
            elif daily.is_swapped:
                status = f" 🔄 (Swapped with {daily.swapped_with})"
            if daily.syllabus:
                topic = f"\n   📖 Session {daily.syllabus.session_number}: {daily.syllabus.session_title}"
                if daily.syllabus.ppt_url:
                    ppt_url = f"\n   📊 PPT: {daily.syllabus.ppt_url}"
        
        response += f"**{get_period_ordinal(entry.period)} Period** ({get_period_time(entry.period)})\n"
        response += f"   👨‍🏫 {faculty.name} → {dept.name}{status}{topic}{ppt_url}\n\n"
    
    return response


def get_faculty_schedule_response(db: Session, faculty: Faculty, day_name: str, today: date) -> str:
    entries = db.query(TimetableEntry).filter(
        TimetableEntry.faculty_id == faculty.id,
        TimetableEntry.day == day_name
    ).order_by(TimetableEntry.period).all()
    
    if not entries:
        return f"📅 {faculty.name} has no C Programming classes scheduled for {day_name}."
    
    response = f"👨‍🏫 **{faculty.name}'s Schedule for Today ({day_name}):**\n\n"
    
    for entry in entries:
        dept = db.query(Department).filter(Department.id == entry.department_id).first()
        
        daily = db.query(DailyEntry).filter(
            DailyEntry.faculty_id == entry.faculty_id,
            DailyEntry.department_id == entry.department_id,
            DailyEntry.date == today,
            DailyEntry.period == entry.period
        ).first()
        
        status = "✅ Scheduled"
        topic = "Not yet updated"
        ppt_url = None
        if daily:
            if daily.is_absent:
                status = "❌ Absent"
            elif daily.is_swapped:
                status = f"🔄 Swapped with {daily.swapped_with}"
            else:
                status = "✅ Confirmed"
            if daily.syllabus:
                topic = f"Session {daily.syllabus.session_number}: {daily.syllabus.session_title}"
                ppt_url = daily.syllabus.ppt_url
        
        response += f"**{get_period_ordinal(entry.period)} Period** ({get_period_time(entry.period)})\n"
        response += f"   🏫 Department: {dept.name}\n"
        response += f"   📊 Status: {status}\n"
        response += f"   📖 Topic: {topic}\n"
        if ppt_url:
            response += f"   📊 PPT: {ppt_url}\n"
        response += "\n"
    
    return response


def get_faculty_topic_response(db: Session, faculty: Faculty, today: date) -> str:
    day_name = get_day_name(today)
    
    entries = db.query(TimetableEntry).filter(
        TimetableEntry.faculty_id == faculty.id,
        TimetableEntry.day == day_name
    ).order_by(TimetableEntry.period).all()
    
    if not entries:
        return f"📅 {faculty.name} has no C Programming classes scheduled for today."
    
    response = f"📖 **Topics {faculty.name} is going to teach today:**\n\n"
    
    has_topic = False
    for entry in entries:
        dept = db.query(Department).filter(Department.id == entry.department_id).first()
        
        daily = db.query(DailyEntry).filter(
            DailyEntry.faculty_id == entry.faculty_id,
            DailyEntry.department_id == entry.department_id,
            DailyEntry.date == today,
            DailyEntry.period == entry.period
        ).first()
        
        if daily and daily.syllabus and not daily.is_absent:
            has_topic = True
            response += f"**{get_period_ordinal(entry.period)} Period** - {dept.name}\n"
            response += f"   📖 **Session {daily.syllabus.session_number}: {daily.syllabus.session_title}**\n"
            if daily.syllabus.ppt_url:
                response += f"   📊 PPT: {daily.syllabus.ppt_url}\n"
            if daily.summary:
                response += f"   📝 Summary: {daily.summary}\n"
            response += "\n"
    
    if not has_topic:
        response = f"📅 {faculty.name} has classes scheduled today but hasn't updated the topics yet.\n\n"
        response += "Classes scheduled:\n"
        for entry in entries:
            dept = db.query(Department).filter(Department.id == entry.department_id).first()
            response += f"- {get_period_ordinal(entry.period)} Period: {dept.name}\n"
    
    return response


def get_department_schedule_response(db: Session, dept: Department, day_name: str, today: date) -> str:
    entries = db.query(TimetableEntry).filter(
        TimetableEntry.department_id == dept.id,
        TimetableEntry.day == day_name
    ).order_by(TimetableEntry.period).all()
    
    if not entries:
        return f"📅 No C Programming classes scheduled for {dept.name} on {day_name}."
    
    response = f"🏫 **C Programming Schedule for {dept.name} ({day_name}):**\n\n"
    
    for entry in entries:
        faculty = db.query(Faculty).filter(Faculty.id == entry.faculty_id).first()
        
        daily = db.query(DailyEntry).filter(
            DailyEntry.faculty_id == entry.faculty_id,
            DailyEntry.department_id == entry.department_id,
            DailyEntry.date == today,
            DailyEntry.period == entry.period
        ).first()
        
        status = ""
        topic = ""
        ppt_url = ""
        if daily:
            if daily.is_absent:
                status = " ❌ (Faculty Absent)"
            elif daily.is_swapped:
                status = f" 🔄 (Swapped with {daily.swapped_with})"
            if daily.syllabus:
                topic = f"\n   📖 Session {daily.syllabus.session_number}: {daily.syllabus.session_title}"
                if daily.syllabus.ppt_url:
                    ppt_url = f"\n   📊 PPT: {daily.syllabus.ppt_url}"
        
        response += f"**{get_period_ordinal(entry.period)} Period** ({get_period_time(entry.period)})\n"
        response += f"   👨‍🏫 Faculty: {faculty.name}{status}{topic}{ppt_url}\n\n"
    
    return response


def get_period_class_response(db: Session, period: int, day_name: str, today: date) -> str:
    if period < 1 or period > 9:
        return "❌ Invalid period. Please specify a period between 1 and 9."
    
    entries = db.query(TimetableEntry).filter(
        TimetableEntry.day == day_name,
        TimetableEntry.period == period
    ).all()
    
    if not entries:
        return f"📅 No C Programming classes in {get_period_ordinal(period)} period ({get_period_time(period)}) today."
    
    response = f"📚 **C Programming Classes in {get_period_ordinal(period)} Period ({get_period_time(period)}):**\n\n"
    
    for entry in entries:
        faculty = db.query(Faculty).filter(Faculty.id == entry.faculty_id).first()
        dept = db.query(Department).filter(Department.id == entry.department_id).first()
        
        daily = db.query(DailyEntry).filter(
            DailyEntry.faculty_id == entry.faculty_id,
            DailyEntry.department_id == entry.department_id,
            DailyEntry.date == today,
            DailyEntry.period == period
        ).first()
        
        status = ""
        topic = ""
        ppt_info = ""
        if daily:
            if daily.is_absent:
                status = " ❌ (Absent)"
            elif daily.is_swapped:
                status = f" 🔄 (Swapped)"
            if daily.syllabus:
                topic = f" - Session {daily.syllabus.session_number}: {daily.syllabus.session_title}"
                if daily.syllabus.ppt_url:
                    ppt_info = f"\n   📊 PPT: {daily.syllabus.ppt_url}"
        
        response += f"👨‍🏫 {faculty.name} → {dept.name}{status}{topic}{ppt_info}\n"
    
    return response


def get_all_topics_today_response(db: Session, today: date) -> str:
    day_name = get_day_name(today)
    
    daily_entries = db.query(DailyEntry).filter(
        DailyEntry.date == today,
        DailyEntry.is_absent == False
    ).all()
    
    if not daily_entries:
        return "📅 No topics have been updated for today's classes yet. Please ask the faculties to fill their daily schedule."
    
    response = f"📖 **Topics Being Taught Today ({day_name}, {today.strftime('%B %d, %Y')}):**\n\n"
    
    # Sort by period
    daily_entries = sorted(daily_entries, key=lambda x: x.period)
    
    for entry in daily_entries:
        if entry.syllabus:
            faculty = db.query(Faculty).filter(Faculty.id == entry.faculty_id).first()
            dept = db.query(Department).filter(Department.id == entry.department_id).first()
            
            response += f"**{get_period_ordinal(entry.period)} Period**\n"
            response += f"   👨‍🏫 {faculty.name} → {dept.name}\n"
            response += f"   📖 **Session {entry.syllabus.session_number}: {entry.syllabus.session_title}**\n"
            if entry.syllabus.ppt_url:
                response += f"   📊 PPT: {entry.syllabus.ppt_url}\n"
            if entry.summary:
                response += f"   📝 {entry.summary}\n"
            response += "\n"
    
    return response


def get_all_faculties_response(db: Session) -> str:
    faculties = db.query(Faculty).filter(Faculty.is_active == True).all()
    
    response = "👨‍🏫 **C Programming Faculties:**\n\n"
    
    for i, faculty in enumerate(faculties, 1):
        response += f"{i}. **{faculty.name}**\n"
        response += f"   📧 {faculty.email}\n"
        response += f"   📱 {faculty.phone}\n\n"
    
    return response


def get_absent_today_response(db: Session, today: date) -> str:
    day_name = get_day_name(today)
    
    absent_entries = db.query(DailyEntry).filter(
        DailyEntry.date == today,
        DailyEntry.is_absent == True
    ).all()
    
    if not absent_entries:
        # Check if any entries exist for today
        any_entries = db.query(DailyEntry).filter(DailyEntry.date == today).first()
        if not any_entries:
            return f"📅 No daily entries have been filled yet for today ({day_name}, {today.strftime('%B %d, %Y')}). Please ask faculties to update their schedules."
        return f"✅ **Great news!** All faculties are present today ({day_name}, {today.strftime('%B %d, %Y')})! No absences reported."
    
    response = f"❌ **Absent Faculties Today ({day_name}, {today.strftime('%B %d, %Y')}):**\n\n"
    
    # Group by faculty to avoid duplicates
    absent_faculty_ids = set()
    for entry in absent_entries:
        if entry.faculty_id not in absent_faculty_ids:
            absent_faculty_ids.add(entry.faculty_id)
            faculty = db.query(Faculty).filter(Faculty.id == entry.faculty_id).first()
            dept = db.query(Department).filter(Department.id == entry.department_id).first()
            
            response += f"👨‍🏫 **{faculty.name}**\n"
            response += f"   📍 Department: {dept.name}\n"
            response += f"   ⏰ Period: {get_period_ordinal(entry.period)} ({get_period_time(entry.period)})\n"
            if entry.is_swapped and entry.swapped_with:
                response += f"   🔄 Replaced by: {entry.swapped_with}\n"
            response += "\n"
    
    return response


def get_today_summary_response(db: Session, day_name: str, today: date) -> str:
    # Get all timetable entries for today
    timetable_entries = db.query(TimetableEntry).filter(
        TimetableEntry.day == day_name
    ).all()
    
    total_scheduled = len(timetable_entries)
    
    # Get all daily entries for today
    daily_entries = db.query(DailyEntry).filter(
        DailyEntry.date == today
    ).all()
    
    filled_count = len(daily_entries)
    absent_count = len([e for e in daily_entries if e.is_absent])
    present_count = len([e for e in daily_entries if not e.is_absent])
    swapped_count = len([e for e in daily_entries if e.is_swapped])
    topics_covered = len([e for e in daily_entries if e.syllabus_id])
    
    response = f"📊 **Today's Summary ({day_name}, {today.strftime('%B %d, %Y')}):**\n\n"
    
    response += f"📅 **Scheduled Classes:** {total_scheduled}\n"
    response += f"✅ **Entries Filled:** {filled_count}/{total_scheduled}\n"
    response += f"👨‍🏫 **Present Faculties:** {present_count}\n"
    response += f"❌ **Absent Faculties:** {absent_count}\n"
    response += f"🔄 **Classes Swapped:** {swapped_count}\n"
    response += f"📖 **Topics Updated:** {topics_covered}\n\n"
    
    if filled_count == 0:
        response += "⚠️ No faculty has filled their schedule yet today."
    elif filled_count < total_scheduled:
        pending = total_scheduled - filled_count
        response += f"⚠️ {pending} class(es) still pending to be updated."
    else:
        response += "✅ All schedules have been filled for today!"
    
    return response


# ===== Session & Syllabus Functions =====

def get_session_info_response(db: Session, session_num: int) -> str:
    session = db.query(Syllabus).filter(Syllabus.session_number == session_num).first()
    
    if not session:
        total = db.query(Syllabus).count()
        return f"❌ Session {session_num} not found. The syllabus has sessions 1 to {total}."
    
    response = f"📚 **Session {session.session_number}: {session.session_title}**\n\n"
    response += f"📗 **Unit:** {session.unit}\n\n"
    
    if session.topics:
        response += f"📖 **Topics Covered:**\n{session.topics}\n\n"
    
    if session.ppt_url:
        response += f"📊 **PPT/Deck:** {session.ppt_url}\n"
    else:
        response += "📊 **PPT/Deck:** Not available yet\n"
    
    return response


def get_session_ppt_response(db: Session, session_num: int) -> str:
    session = db.query(Syllabus).filter(Syllabus.session_number == session_num).first()
    
    if not session:
        total = db.query(Syllabus).count()
        return f"❌ Session {session_num} not found. The syllabus has sessions 1 to {total}."
    
    if session.ppt_url:
        response = f"📊 **PPT for Session {session.session_number}**\n\n"
        response += f"📚 Topic: {session.session_title}\n"
        response += f"🔗 Link: {session.ppt_url}\n"
        return response
    else:
        return f"📊 The PPT for Session {session_num} ({session.session_title}) is not available yet."


def get_all_ppts_response(db: Session) -> str:
    sessions_with_ppt = db.query(Syllabus).filter(Syllabus.ppt_url != None).order_by(Syllabus.session_number).all()
    
    if not sessions_with_ppt:
        return "📊 No PPTs are currently available in the system."
    
    response = f"📊 **Available PPTs/Decks ({len(sessions_with_ppt)} sessions):**\n\n"
    
    current_unit = 0
    for session in sessions_with_ppt:
        if session.unit != current_unit:
            current_unit = session.unit
            response += f"\n**Unit {current_unit}:**\n"
        response += f"  Session {session.session_number}: {session.session_title}\n"
        response += f"  🔗 {session.ppt_url}\n\n"
    
    return response


def get_all_sessions_response(db: Session) -> str:
    sessions = db.query(Syllabus).order_by(Syllabus.unit, Syllabus.session_number).all()
    
    if not sessions:
        return "📚 No syllabus sessions found in the system."
    
    response = "📚 **C Programming Syllabus - All Sessions:**\n\n"
    
    current_unit = 0
    for session in sessions:
        if session.unit != current_unit:
            current_unit = session.unit
            unit_names = {
                1: "BASICS OF C PROGRAMMING",
                2: "ARRAYS AND STRINGS",
                3: "FUNCTIONS AND POINTERS",
                4: "STRUCTURES AND UNIONS",
                5: "FILE PROCESSING"
            }
            response += f"\n**📗 UNIT {current_unit}: {unit_names.get(current_unit, '')}**\n"
        
        ppt_indicator = "📊" if session.ppt_url else "📄"
        response += f"  {ppt_indicator} Session {session.session_number}: {session.session_title}\n"
    
    response += "\n💡 *Ask about any session for details (e.g., 'Show session 5')*"
    response += "\n💡 *📊 = PPT available, 📄 = No PPT yet*"
    
    return response


# ===== Lab Program Functions =====

def get_lab_program_response(db: Session, program_num: int) -> str:
    program = db.query(LabProgram).filter(LabProgram.program_number == program_num).first()
    
    if not program:
        total = db.query(LabProgram).count()
        return f"❌ Lab program {program_num} not found. There are {total} lab programs available."
    
    response = f"🔬 **Lab Program {program.program_number}: {program.program_title}**\n\n"
    
    if program.description:
        response += f"📝 **Description:**\n{program.description}\n"
    
    return response


def get_all_lab_programs_response(db: Session) -> str:
    programs = db.query(LabProgram).order_by(LabProgram.program_number).all()
    
    if not programs:
        return "🔬 No lab programs found in the system."
    
    response = f"🔬 **C Programming Lab Programs ({len(programs)} total):**\n\n"
    
    # Group by categories based on program number ranges
    categories = [
        (1, 5, "Basic I/O & Arithmetic"),
        (6, 14, "Control Structures & Patterns"),
        (15, 20, "Arrays & Matrices"),
        (21, 24, "Strings"),
        (25, 30, "Functions, Recursion & Pointers"),
        (31, 35, "Structures & Linked Lists"),
        (36, 40, "File Handling & Mini Project")
    ]
    
    for start, end, category_name in categories:
        cat_programs = [p for p in programs if start <= p.program_number <= end]
        if cat_programs:
            response += f"**{category_name}:**\n"
            for prog in cat_programs:
                response += f"  {prog.program_number}. {prog.program_title}\n"
            response += "\n"
    
    response += "💡 *Ask about any lab program for details (e.g., 'Lab 5')*"
    
    return response