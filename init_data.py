from database import engine, SessionLocal
from models import Base, Department, Syllabus, Admin, Faculty, TimetableEntry, PeriodTiming, LabProgram, SuperAdmin, FAQ
from passlib.context import CryptContext
from sqlalchemy import inspect, text

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _column_exists(table_name, column_name):
    """Check if a column exists in a table (works for both SQLite and PostgreSQL)"""
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns

def init_database():
    """Initialize database with all tables and seed data.
    
    This function handles both:
    1. Fresh database initialization (all tables and data)
    2. Adding missing tables/data to existing database (e.g., SuperAdmin, FAQ)
    """
    # Create all tables (won't affect existing tables)
    Base.metadata.create_all(bind=engine)
    
    # Add room_number column if missing (for existing databases)
    _add_room_number_column_if_missing()
    
    # Add extra class columns if missing (for existing databases)
    _add_extra_class_columns_if_missing()
    
    db = SessionLocal()
    
    # Check if this is a fresh database or existing one
    is_fresh_db = db.query(Department).first() is None
    
    if is_fresh_db:
        print("Initializing fresh database...")
        _init_all_data(db)
    else:
        print("Database exists. Checking for missing data...")
        _add_missing_data(db)
    
    db.close()

def _add_room_number_column_if_missing():
    """Add room_number column to departments table if it doesn't exist"""
    if not _column_exists("departments", "room_number"):
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE departments ADD COLUMN room_number VARCHAR(20)"))
            conn.commit()
            print("✓ Added room_number column to departments table")

def _add_extra_class_columns_if_missing():
    """Add extra class columns to daily_entries table if they don't exist"""
    # Add is_extra_class column if missing
    if not _column_exists("daily_entries", "is_extra_class"):
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE daily_entries ADD COLUMN is_extra_class BOOLEAN DEFAULT FALSE"))
            conn.commit()
            print("✓ Added is_extra_class column to daily_entries table")
    
    # Add extra_class_subject_code column if missing
    if not _column_exists("daily_entries", "extra_class_subject_code"):
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE daily_entries ADD COLUMN extra_class_subject_code VARCHAR(20)"))
            conn.commit()
            print("✓ Added extra_class_subject_code column to daily_entries table")
    
    # Add extra_class_subject_name column if missing
    if not _column_exists("daily_entries", "extra_class_subject_name"):
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE daily_entries ADD COLUMN extra_class_subject_name VARCHAR(50)"))
            conn.commit()
            print("✓ Added extra_class_subject_name column to daily_entries table")

def _add_missing_data(db):
    """Add missing tables/data to existing database (e.g., SuperAdmin, FAQ)"""
    added_something = False
    
    # Check and add SuperAdmin if missing
    if not db.query(SuperAdmin).first():
        super_admin = SuperAdmin(
            username="super_admin@gmail.com",
            password=pwd_context.hash("superadmin123")
        )
        db.add(super_admin)
        db.commit()
        print("✓ Super Admin added: super_admin@gmail.com / superadmin123")
        added_something = True
    else:
        print("✓ Super Admin already exists")
    
    # Check and add FAQs if missing
    if not db.query(FAQ).first():
        _add_default_faqs(db)
        print("✓ Default FAQs added")
        added_something = True
    else:
        print("✓ FAQs already exist")
    
    # Update department room numbers if missing
    _update_department_room_numbers(db)
    
    if not added_something:
        print("All data is up to date!")

def _update_department_room_numbers(db):
    """Update existing departments with room numbers"""
    room_numbers = {
        "AI&DS-A": "315(2nd floor)",
        "AI&DS-B": "316(2nd floor)",
        "AI&ML-A": "414(3rd floor)",
        "AI&ML-B": "415(3rd floor)",
        "CSBS": "416(3rd floor)",
        "CSE-A": "411A(3rd floor)",
        "CSE-B": "412(3rd floor)",
        "CYS": "301(2nd floor)",
        "ECE-A": "312(2nd floor)",
        "ECE-B": "313(2nd floor)",
        "IT-A": "310A1(2nd floor)",
        "IT-B": "311(2nd floor)",
        "MECH": "303(2nd floor)",
        "RA": "302(2nd floor)",
    }
    
    updated_count = 0
    for code, room in room_numbers.items():
        dept = db.query(Department).filter(Department.code == code).first()
        if dept and (not hasattr(dept, 'room_number') or dept.room_number != room):
            dept.room_number = room
            updated_count += 1
    
    if updated_count > 0:
        db.commit()
        print(f"✓ Updated room numbers for {updated_count} department(s)")
    else:
        print("✓ Department room numbers already up to date")

def _add_default_faqs(db):
    """Add default FAQ entries"""
    default_faqs = [
        # Class Schedule & Timing FAQs - General guidance only (dynamic queries handle specifics)
        {"question": "What are today's C programming classes?", "answer": "Type 'show schedule' or 'today classes' to see today's C programming classes with faculty and periods.", "category": "schedule"},
        {"question": "Who has class in a specific period?", "answer": "Type 'period [number]' (e.g., 'period 3', 'period 4', '5th period') to see who has class in that period.", "category": "schedule"},
        {"question": "When is the C programming class for a department?", "answer": "Type the department code (e.g., 'AI&DS-A', 'CSE-B', 'IT-A') to see their C programming schedule.", "category": "schedule"},
        {"question": "What time does the 1st period start?", "answer": "The 1st period starts at 08:00 AM and ends at 08:45 AM.", "category": "schedule"},
        {"question": "Show me the complete timetable for a day", "answer": "Type the day name (e.g., 'Monday', 'Tuesday schedule', 'Wednesday classes') to see the complete schedule for that day.", "category": "schedule"},
        {"question": "Which faculty is teaching a department?", "answer": "Type the department code (e.g., 'CSE-B', 'AI&DS-A') to see which faculty is assigned.", "category": "schedule"},
        {"question": "Is there any lab class today?", "answer": "Lab classes are typically scheduled for 2-3 consecutive periods. Check today's schedule to see lab sessions.", "category": "schedule"},
        {"question": "What are the theory class timings?", "answer": "Theory classes are 45 minutes each. Periods: 1(8:00-8:45), 2(8:45-9:30), 3(9:45-10:30), 4(10:30-11:15), 5(11:15-12:00), 6(1:00-1:45), 7(1:45-2:30), 8(2:30-3:15), 9(3:30-4:15).", "category": "schedule"},
        {"question": "How many periods are there in a day?", "answer": "There are 9 periods in a day. Morning: Periods 1-5 (8:00 AM - 12:00 PM), Afternoon: Periods 6-9 (1:00 PM - 4:15 PM).", "category": "schedule"},
        {"question": "When does the college start and end?", "answer": "College starts at 8:00 AM (1st period) and ends at 4:15 PM (9th period).", "category": "schedule"},
        {"question": "Is there class on Saturday?", "answer": "Saturday classes depend on the timetable. Type 'Saturday' to check if there are any C programming classes.", "category": "schedule"},
        {"question": "What is the lunch break timing?", "answer": "Lunch break is from 12:00 PM to 1:00 PM (between 5th and 6th periods).", "category": "schedule"},
        {"question": "Show me all classes for this week", "answer": "Type the day name (Monday, Tuesday, etc.) to see classes for that day, or 'show schedule' for today.", "category": "schedule"},
        {"question": "Which departments have C programming today?", "answer": "Type 'show schedule' to see all departments that have C programming classes today.", "category": "schedule"},
        {"question": "What classes are scheduled after lunch break?", "answer": "After lunch (1:00 PM onwards), periods 6-9 have classes. Type 'period 6' or 'period 7' etc. to see specific classes.", "category": "schedule"},
        {"question": "What are the topics to be covered?", "answer": "Topics covered depend on the syllabus session. Type 'session [number]' (e.g., 'session 5') to see specific topic details.", "category": "schedule"},
        {"question": "Which class is handling lab today?", "answer": "Lab sessions are marked as 'lab' type in the timetable. Type 'show schedule' to identify lab classes.", "category": "schedule"},
        
        # Faculty FAQs
        {"question": "Who is teaching C programming?", "answer": "We have 14 dedicated faculty members teaching C programming across different departments. Type 'list all faculty' to see them.", "category": "faculty"},
        {"question": "List all faculty members", "answer": "Type 'list all faculty' to see all 14 faculty members with their departments.", "category": "faculty"},
        {"question": "Who teaches AI&DS-A?", "answer": "Type 'AI&DS-A' to see the faculty assigned to AI&DS-A department for C programming.", "category": "faculty"},
        
        # Topics & Syllabus FAQs
        {"question": "What topics are covered in Unit 1?", "answer": "Unit 1 covers Basics of C Programming: Introduction to C, History, Features, Structure of C program, Compilation Process, Tokens, Keywords, Identifiers, Variables, Data Types, Operators, and Control Flow.", "category": "topics"},
        {"question": "What topics are covered in Unit 2?", "answer": "Unit 2 covers Arrays and Strings: One-dimensional arrays, Multi-dimensional arrays, String handling, String functions, Array operations.", "category": "topics"},
        {"question": "What topics are covered in Unit 3?", "answer": "Unit 3 covers Functions: Function declaration, definition, calling, recursion, storage classes, and scope rules.", "category": "topics"},
        {"question": "What topics are covered in Unit 4?", "answer": "Unit 4 covers Pointers: Pointer basics, pointer arithmetic, pointers with arrays, pointers with functions, dynamic memory allocation.", "category": "topics"},
        {"question": "What topics are covered in Unit 5?", "answer": "Unit 5 covers Structures and File Handling: Structures, Unions, Typedef, File operations, file pointers, reading and writing files.", "category": "topics"},
        {"question": "How can I access the PPT materials?", "answer": "Type 'session [number] ppt' (e.g., 'session 3 ppt') to get the PPT link for that session.", "category": "topics"},
        {"question": "What lab programs are available?", "answer": "There are 10 lab programs. Type 'week [number] lab' (e.g., 'week 3 lab') to see specific lab program details.", "category": "topics"},
        
        # General FAQs
        {"question": "What is the course code?", "answer": "The course code for C Programming is 24UCS271 (PROG C).", "category": "general"},
        {"question": "How to use this chatbot?", "answer": "You can ask about: faculty schedules (e.g., 'Sathish today'), department classes (e.g., 'CSE-A'), lab programs (e.g., 'week 3 lab'), or PPT materials (e.g., 'session 5 ppt'). Type 'help' for more commands.", "category": "general"},
        {"question": "Who is absent today?", "answer": "Check the 'Absent Today' section in the dashboard to see which faculty members are absent today.", "category": "general"},
    ]
    
    for faq_data in default_faqs:
        faq = FAQ(
            question=faq_data["question"],
            answer=faq_data["answer"],
            category=faq_data["category"]
        )
        db.add(faq)
    db.commit()

def _init_all_data(db):
    """Initialize all data for a fresh database"""
    # Add Departments with Room Numbers
    departments = [
        {"name": " AI&DS - A", "code": "AI&DS-A", "room_number": "315(2nd floor)"},
        {"name": " AI&DS - B", "code": "AI&DS-B", "room_number": "316(2nd floor)"},
        {"name": " AI&ML - A", "code": "AI&ML-A", "room_number": "414(3rd floor)"},
        {"name": " AI&ML - B", "code": "AI&ML-B", "room_number": "415(3rd floor)"},
        {"name": " CSBS", "code": "CSBS", "room_number": "416(3rd floor)"},
        {"name": " CSE - A", "code": "CSE-A", "room_number": "411A(3rd floor)"},
        {"name": " CSE - B", "code": "CSE-B", "room_number": "412(3rd floor)"},
        {"name": " CYS", "code": "CYS", "room_number": "301(2nd floor)"},
        {"name": " ECE - A", "code": "ECE-A", "room_number": "312(2nd floor)"},
        {"name": " ECE - B", "code": "ECE-B", "room_number": "313(2nd floor)"},
        {"name": " IT - A", "code": "IT-A", "room_number": "310A1(2nd floor)"},
        {"name": " IT - B", "code": "IT-B", "room_number": "311(2nd floor)"},
        {"name": " MECH", "code": "MECH", "room_number": "303(2nd floor)"},
        {"name": " RA", "code": "RA", "room_number": "302(2nd floor)"}
    ]
    
    for dept in departments:
        db.add(Department(**dept))
    
    # Add Period Timings
    period_timings = [
        {"period": 1, "start_time": "08:00 AM", "end_time": "08:45 AM", "display_time": "08:00 AM - 08:45 AM"},
        {"period": 2, "start_time": "08:45 AM", "end_time": "09:30 AM", "display_time": "08:45 AM - 09:30 AM"},
        {"period": 3, "start_time": "09:45 AM", "end_time": "10:30 AM", "display_time": "09:45 AM - 10:30 AM"},
        {"period": 4, "start_time": "10:30 AM", "end_time": "11:15 AM", "display_time": "10:30 AM - 11:15 AM"},
        {"period": 5, "start_time": "11:15 AM", "end_time": "12:00 PM", "display_time": "11:15 AM - 12:00 PM"},
        {"period": 6, "start_time": "01:00 PM", "end_time": "01:45 PM", "display_time": "01:00 PM - 01:45 PM"},
        {"period": 7, "start_time": "01:45 PM", "end_time": "02:30 PM", "display_time": "01:45 PM - 02:30 PM"},
        {"period": 8, "start_time": "02:30 PM", "end_time": "03:15 PM", "display_time": "02:30 PM - 03:15 PM"},
        {"period": 9, "start_time": "03:30 PM", "end_time": "04:15 PM", "display_time": "03:30 PM - 04:15 PM"},
    ]
    
    for timing in period_timings:
        db.add(PeriodTiming(**timing))
    
    # Add C Programming Syllabus - Sessions with PPT URLs
    syllabus_sessions = [
        # UNIT 1: BASICS OF C PROGRAMMING
        {"session_number": 1, "session_title": "Introduction to C Programming", "unit": 1,
         "topics": "What is C? Why C still matters (systems, OS, embedded). Difference between Python and C (compiled vs interpreted, performance, control). Structure of a C program: #include, main(), braces, statements.",
         "ppt_url": "http://tiny.cc/CSes01Deck"},
        {"session_number": 2, "session_title": "Compilation Process & Preprocessor Directives", "unit": 1,
         "topics": "Phases of C program compilation: preprocessing, compilation, linking, execution. Role of compiler and linker. Preprocessor directives: #include, #define. Macros vs variables.",
         "ppt_url": "http://tiny.cc/CSes02Deck"},
        {"session_number": 3, "session_title": "Tokens, Keywords & Data Types", "unit": 1,
         "topics": "C tokens overview. Character set and basic syntax rules. Keywords vs identifiers. Data types overview (int, float, char, double).",
         "ppt_url": "http://tiny.cc/CSes03Deck"},
        {"session_number": 4, "session_title": "Variables, Constants & I/O", "unit": 1,
         "topics": "Constants and variables: declaration vs definition. printf, scanf (format specifiers). Common I/O mistakes.",
         "ppt_url": "http://tiny.cc/CSes04Deck"},
        {"session_number": 5, "session_title": "Operators & Expressions", "unit": 1,
         "topics": "Arithmetic, relational, logical, assignment operators. Expressions and evaluation. Increment/decrement operators (++, --) - prefix vs postfix.",
         "ppt_url": "http://tiny.cc/CSes05Deck"},
        {"session_number": 6, "session_title": "Operator Precedence & Associativity", "unit": 1,
         "topics": "Why precedence matters in C more than Python. Precedence hierarchy. Associativity rules. Expression tracing step-by-step.",
         "ppt_url": "http://tiny.cc/CSes06Deck"},
        {"session_number": 7, "session_title": "Branching Statements", "unit": 1,
         "topics": "if, if-else, nested if. else-if ladder. switch-case: syntax, break, fall-through behavior.",
         "ppt_url": "http://tiny.cc/CSes07Deck"},
        {"session_number": 8, "session_title": "Looping Statements", "unit": 1,
         "topics": "while, do-while, for loops. Entry-controlled vs exit-controlled loops.",
         "ppt_url": "http://tiny.cc/CSes08Deck"},
        {"session_number": 9, "session_title": "Control Flow Integration", "unit": 1,
         "topics": "Combining branching and looping. Nested loops (patterns, counting logic). break, continue, and goto.",
         "ppt_url": "http://tiny.cc/CSes09Deck"},
        
        # UNIT 2: ARRAYS AND STRINGS
        {"session_number": 10, "session_title": "Introduction to Arrays", "unit": 2,
         "topics": "Why arrays are needed (limitations of scalar variables). One-dimensional arrays: declaration and syntax. Array indexing and zero-based indexing. Accessing and modifying elements.",
         "ppt_url": "http://tiny.cc/CSes10Deck"},
        {"session_number": 11, "session_title": "1D Array - Basic Operations", "unit": 2,
         "topics": "Array initialization methods (compile-time, run-time). Reading values into arrays using loops. Printing array elements.",
         "ppt_url": "http://tiny.cc/CSes11Deck"},
        {"session_number": 12, "session_title": "2D Arrays and Multidimensional Arrays", "unit": 2,
         "topics": "Declaration and initialization of 2D arrays. Row-column indexing logic. Traversing 2D arrays using nested loops. Multidimensional arrays beyond 2D.",
         "ppt_url": "http://tiny.cc/CSes12Deck"},
        {"session_number": 13, "session_title": "Searching & Sorting", "unit": 2,
         "topics": "Linear Search: Finding an element in a 1D array. Bubble Sort. Logic vs. Syntax: manual swapping using a temporary variable.",
         "ppt_url": "http://tiny.cc/CSes13Deck"},
        {"session_number": 14, "session_title": "Introduction to Strings in C", "unit": 2,
         "topics": "What is a string in C? (character array + null terminator). Difference between character and string. Declaring and initializing strings. Importance of '\\0'.",
         "ppt_url": "http://tiny.cc/CSes14Deck"},
        {"session_number": 15, "session_title": "Reading & Writing Strings", "unit": 2,
         "topics": "Reading strings using scanf() and gets(). Using fgets() for safer input. Writing strings using printf() and puts().",
         "ppt_url": "http://tiny.cc/CSes15Deck"},
        {"session_number": 16, "session_title": "String Operations - Built-in Functions", "unit": 2,
         "topics": "String length: strlen(). String copy: strcpy(). String concatenation: strcat(). String comparison: strcmp(). Header file <string.h>.",
         "ppt_url": "http://tiny.cc/CSes16Deck"},
        {"session_number": 17, "session_title": "String Manipulation", "unit": 2,
         "topics": "Manual string length calculation. String copy using loops. String comparison logic.",
         "ppt_url": "http://tiny.cc/CSes17Deck"},
        {"session_number": 18, "session_title": "Arrays of Strings", "unit": 2,
         "topics": "Concept of arrays of strings (2D character arrays). Declaration and initialization. Reading and displaying multiple strings.",
         "ppt_url": "http://tiny.cc/CSes18Deck"},
        
        # UNIT 3: FUNCTIONS AND POINTERS
        {"session_number": 19, "session_title": "Introduction to Functions", "unit": 3,
         "topics": "Why functions are needed (modularity, reuse). Difference between function declaration and definition. Built-in functions overview. Writing and calling simple user-defined functions.",
         "ppt_url": None},
        {"session_number": 20, "session_title": "Function Prototypes & Parameter Passing", "unit": 3,
         "topics": "Function prototypes and why they exist. Call by value (default in C). Understanding data flow between functions.",
         "ppt_url": None},
        {"session_number": 21, "session_title": "Passing Arrays to Functions & Variable Scope", "unit": 3,
         "topics": "Passing 1D arrays to functions. Array parameters and size handling. Scope of variables: local vs global. Lifetime of variables.",
         "ppt_url": None},
        {"session_number": 22, "session_title": "Recursion", "unit": 3,
         "topics": "What is recursion and why it is used. Base condition and recursive call. Recursive vs iterative solutions. Examples: factorial, Fibonacci, sum of digits.",
         "ppt_url": None},
        {"session_number": 23, "session_title": "Introduction to Pointers", "unit": 3,
         "topics": "What is a pointer and why it exists. Pointer declaration and initialization. Address-of (&) and dereferencing (*) operators. Call by reference.",
         "ppt_url": None},
        {"session_number": 24, "session_title": "Pointer Arithmetic & Pointers with Arrays", "unit": 3,
         "topics": "Pointer arithmetic concepts. Relationship between arrays and pointers. Accessing array elements using pointers.",
         "ppt_url": None},
        {"session_number": 25, "session_title": "Advanced Pointer Concepts", "unit": 3,
         "topics": "Pointer to pointer (double pointer). Use cases. Pointers to functions.",
         "ppt_url": None},
        {"session_number": 26, "session_title": "Pointers with Strings & Arrays", "unit": 3,
         "topics": "Strings as character pointers. Pointer-based string traversal. Difference between char[] and char*. Arrays of pointers.",
         "ppt_url": None},
        {"session_number": 27, "session_title": "Dynamic Memory Allocation", "unit": 3,
         "topics": "Need for dynamic memory. malloc(), calloc(), realloc(), free(). Memory leaks and dangling pointers.",
         "ppt_url": None},
        
        # UNIT 4: STRUCTURES AND UNIONS
        {"session_number": 28, "session_title": "Introduction to Structures", "unit": 4,
         "topics": "Why structures are needed (limitations of arrays and variables). Structure declaration and definition. Accessing structure members using dot (.) operator.",
         "ppt_url": None},
        {"session_number": 29, "session_title": "Initialization & Array of Structures", "unit": 4,
         "topics": "Structure initialization (compile-time and run-time). Array of structures: declaration and usage. Reading and displaying multiple structure records.",
         "ppt_url": None},
        {"session_number": 30, "session_title": "Nested Structures", "unit": 4,
         "topics": "Concept of nested structures. Accessing members of nested structures.",
         "ppt_url": None},
        {"session_number": 31, "session_title": "Pointers and Structures", "unit": 4,
         "topics": "Need for pointers with structures. Pointer to structure declaration. Accessing members using arrow (->) operator. Passing structures to functions.",
         "ppt_url": None},
        {"session_number": 32, "session_title": "Self-Referential Structures", "unit": 4,
         "topics": "What is a self-referential structure and why it exists. Syntax and memory visualization. Role in dynamic data structures.",
         "ppt_url": None},
        {"session_number": 33, "session_title": "Singly Linked List - Creation", "unit": 4,
         "topics": "What is a linked list and why arrays fail. Node structure definition. Linking nodes together.",
         "ppt_url": None},
        {"session_number": 34, "session_title": "Singly Linked List - Operations", "unit": 4,
         "topics": "Traversing a linked list. Insertion/deletion at beginning, in-between and end. Displaying linked list elements.",
         "ppt_url": None},
        {"session_number": 35, "session_title": "Union", "unit": 4,
         "topics": "Union declaration and usage. Memory sharing concept. Structure vs union comparison.",
         "ppt_url": None},
        {"session_number": 36, "session_title": "Storage Classes", "unit": 4,
         "topics": "Storage classes: auto, static, extern, register. Scope, lifetime, and visibility.",
         "ppt_url": None},
        
        # UNIT 5: FILE PROCESSING
        {"session_number": 37, "session_title": "Introduction to Files", "unit": 5,
         "topics": "Need for files in C (permanent storage). Difference between RAM and file storage. Types of file processing: sequential and random access.",
         "ppt_url": None},
        {"session_number": 38, "session_title": "File Operations & File Modes", "unit": 5,
         "topics": "File pointer (FILE *). Opening and closing files: fopen(), fclose(). File modes: r, w, a, r+, w+, a+.",
         "ppt_url": None},
        {"session_number": 39, "session_title": "Sequential Access Files - Reading & Writing", "unit": 5,
         "topics": "Writing data to sequential files. Reading data from sequential files. Functions: fprintf(), fscanf(), fgets(), fputs().",
         "ppt_url": None},
        {"session_number": 40, "session_title": "Sequential Access File Applications", "unit": 5,
         "topics": "Finding average of numbers stored in a file. Processing numeric data from files.",
         "ppt_url": None},
        {"session_number": 41, "session_title": "Random Access Files", "unit": 5,
         "topics": "Need for random access files. File positioning functions: fseek, ftell, rewind. Difference between sequential and random access.",
         "ppt_url": None},
        {"session_number": 42, "session_title": "Random Access Files with Structures", "unit": 5,
         "topics": "Storing structure records in files. Reading and writing structure data (fread, fwrite). Calculating record size. Accessing specific records.",
         "ppt_url": None},
        {"session_number": 43, "session_title": "Transaction Processing using Random Access Files", "unit": 5,
         "topics": "What is transaction processing. Insert, update, and delete operations on records. Simple record-based applications.",
         "ppt_url": None},
        {"session_number": 44, "session_title": "File Error Handling", "unit": 5,
         "topics": "Checking file open failures. Common runtime file errors. Safe file handling practices.",
         "ppt_url": None},
        {"session_number": 45, "session_title": "Command Line Arguments", "unit": 5,
         "topics": "What are command line arguments. argc and argv parameters. Accessing command line input.",
         "ppt_url": None},
    ]
    
    for session in syllabus_sessions:
        db.add(Syllabus(**session))
    
    # Add Lab Programs - Only In-Lab Programs (Week 1-10)
    lab_programs = [
        {"program_number": 1, "program_title": "In-Lab W1: Student Marks Calculator", 
         "description": "A student enters marks obtained in three subjects. Write a C program that: 1) Reads the student's roll number, 2) Reads marks of three subjects, 3) Calculates total marks and average marks. This problem combines input/output handling, arithmetic operators, and expression evaluation into a single application.",
         "moodle_url": "https://moodle2.kgkite.ac.in/mod/vpl/view.php?id=2739"},
        
        {"program_number": 2, "program_title": "In-Lab W2: Employee Performance Evaluation System", 
         "description": "Design a C program for a basic employee performance evaluation system used in a company HR department. The program should: Read an employee ID, read performance scores in three criteria (Technical Skill, Communication, and Teamwork), calculate total and average score, determine the performance grade using branching rules: If any criterion score is less than 50 => Poor Performance, Else if average ≥ 75 => Outstanding, Else if average ≥ 60 => Satisfactory, Else => Needs Improvement.",
         "moodle_url": "https://moodle2.kgkite.ac.in/mod/vpl/view.php?id=2749"},
        
        {"program_number": 3, "program_title": "In-Lab W3: FizzBuzz Analyzer", 
         "description": "FizzBuzz looks playful, but it quietly tests deep understanding of loops, conditions, and control flow. Write a C program that processes numbers from 1 to N and applies the following rules: If the number is divisible by 3, print Fizz; If the number is divisible by 5, print Buzz; If the number is divisible by both 3 and 5, print FizzBuzz; Otherwise, print the number itself. This problem integrates for loop iteration, if-else and nested conditions, logical reasoning with operators, and clean output formatting.",
         "moodle_url": "https://moodle2.kgkite.ac.in/mod/vpl/view.php?id=2751"},
        
        {"program_number": 4, "program_title": "In-Lab W4: Student Marks Analysis System", 
         "description": "A class consists of N students, each evaluated in three subjects. Write a C program that: 1) Reads marks of all students into a 2D array (N × 3), 2) Calculates the total marks for each student, 3) Calculates the class average for each subject, 4) Displays all results neatly. This problem integrates 2D arrays, nested loops, array-based accumulation and comparison, and clean tabular output.",
         "moodle_url": None},
        
        {"program_number": 5, "program_title": "In-Lab W5: Username Processing System", 
         "description": "A simple system is required to process user names entered during registration. Write a C program that: 1) Reads a user's first name and last name as strings, 2) Displays the length of each name, 3) Checks whether both names are identical, 4) Creates a username by concatenating the first name and last name. This problem combines string input/output, length calculation, string comparison, and string concatenation. All operations must use standard string functions.",
         "moodle_url": None},
        
        {"program_number": 6, "program_title": "In-Lab W6: Prime Factorization Using Functions", 
         "description": "Write a C program that: Uses a function to find the prime factors of a given number n, uses an array to store the prime factors in non-decreasing order, uses a function to return the total number of prime factors found, and displays the prime factors from main(). Each task must be handled by a separate function, and the array must be passed between functions.",
         "moodle_url": None},
        
        {"program_number": 7, "program_title": "In-Lab W7: Binary Search Using Recursion", 
         "description": "Write a C program that: Uses a recursive function to perform binary search on a sorted array, uses a function to read N elements into an array in ascending order, uses a recursive function to search for a given key, and displays whether the search element is found or not from main().",
         "moodle_url": None},
        
        {"program_number": 8, "program_title": "In-Lab W8: Array Element Swap Using Pointers", 
         "description": "Write a C program that: Uses a function to read N integers into an array, uses a function to swap two array elements using pointers, uses pointer notation to access and modify array elements, and displays the array before and after swapping from main(). The swapping operation must be performed only using pointers, not array indexing.",
         "moodle_url": None},
        
        {"program_number": 9, "program_title": "In-Lab W9: Library Book Record Management System", 
         "description": "A library maintains records of books issued to students. Each record contains: Book ID, Book title, Student details, and Issue date. Write a C program that: 1) Uses a nested structure to represent issue date, 2) Uses a structure for student details, 3) Stores multiple records using an array of structures, 4) Uses a pointer to structure to traverse and display records. This models how structured data is organized in real systems.",
         "moodle_url": None},
        
        {"program_number": 10, "program_title": "In-Lab W10: Student Report File System", 
         "description": "A college department wants to store student academic details in a file so that the data is not lost when the program ends. Write a C program that: 1) Writes student details to a file, 2) Appends subject marks to the same file, 3) Reads and displays the complete file content, 4) Uses a file pointer to re-read the file from the beginning.",
         "moodle_url": None},
    ]
    
    for prog in lab_programs:
        db.add(LabProgram(**prog))
    
    # Add default admin (email-style username for unified login)
    admin = Admin(
        username="mail-admin@gmail.com",
        password=pwd_context.hash("admin123")
    )
    db.add(admin)
    
    # Add default super admin
    super_admin = SuperAdmin(
        username="super_admin@gmail.com",
        password=pwd_context.hash("superadmin123")
    )
    db.add(super_admin)
    
    # Add default FAQs
    _add_default_faqs(db)
    
    # Add faculties (14 faculties from DATAS.TXT)
    # Images should be stored in static/images/ folder with filenames like: faculty1.jpg, faculty2.jpg, etc.
    faculties_data = [
        {
            "name": "Sathish R",
            "email": "r.sathish@kgkite.ac.in",
            "phone": "9791406167",
            "dept": "AI&DS-A",
            "image": "faculty1.jpg",
            "linkedin": "https://www.linkedin.com/in/sathish-ramanujam-96545313a",
            "github": "https://github.com/Professor-Sathish",
            "experience": "13",
            "c_exp": "1",
            "py_exp": "9",
            "research": "Machine Learning",
            "personal_email": "sathishse13@gmail.com"
        },
        {
            "name": "Sikkandhar Batcha J",
            "email": "sikkandharbatcha.j@kgkite.ac.in",
            "phone": "9486429598",
            "dept": "AI&DS-B",
            "image": "faculty2.jpg",
            "linkedin": "https://www.linkedin.com/in/sikkandhar-batcha-j-bb585271",
            "github": "https://github.com/sssbatcha",
            "experience": "9",
            "c_exp": "1",
            "py_exp": "2",
            "research": "Deep Learning",
            "personal_email": "sssbatcha@gmail.com"
        },
        {
            "name": "Raakesh M",
            "email": "raakesh.m@kgkite.ac.in",
            "phone": "9360758406",
            "dept": "AI&ML-A",
            "image": "faculty3.jpg",
            "linkedin": "https://www.linkedin.com/in/raakesh-muthuvel",
            "github": "https://github.com/Raa96",
            "experience": "0.2",
            "c_exp": "0",
            "py_exp": "0",
            "research": "Data Science & ML",
            "personal_email": "raakeshmuthuvel@gmail.com"
        },
        {
            "name": "Aruna R",
            "email": "aruna.r@kgkite.ac.in",
            "phone": "9585458088",
            "dept": "AI&ML-B",
            "image": "faculty4.jpg",
            "linkedin": "https://www.linkedin.com/in/aruna-deepa-0957b9201/",
            "github": "https://github.com/arunacse867-design",
            "experience": "11.5",
            "c_exp": "2",
            "py_exp": "1",
            "research": "Data Science",
            "personal_email": "arunacse867@gmail.com"
        },
        {
            "name": "Janani S",
            "email": "janani.s@kgkite.ac.in",
            "phone": "9786282598",
            "dept": "CSE-A",
            "image": "faculty5.jpg",
            "linkedin": "https://www.linkedin.com/in/janani-s",
            "github": "https://github.com/JANANI441992",
            "experience": "9.5",
            "c_exp": "4",
            "py_exp": "3",
            "research": "Deep Learning & Neural Networks",
            "personal_email": "janani441992@gmail.com"
        },
        {
            "name": "Indhumathi S",
            "email": "indhumathi.s@kgkite.ac.in",
            "phone": "7708146489",
            "dept": "CSE-B",
            "image": "faculty6.jpg",
            "linkedin": "https://www.linkedin.com/in/indhumathi-subramaniam-35a770289",
            "github": "https://github.com/IndhumathiSubramaniam",
            "experience": "8",
            "c_exp": "1",
            "py_exp": "2",
            "research": "Machine Learning & Deep Learning",
            "personal_email": "indhumathisme@gmail.com"
        },
        {
            "name": "Saranya S",
            "email": "saranya.sh@kgkite.ac.in",
            "phone": "7339511127",
            "dept": "CSBS",
            "image": "faculty7.jpg",
            "linkedin": "https://www.linkedin.com/in/saranya-prabhakaran-2639a719b",
            "github": "https://github.com/saranyaethvik/saran",
            "experience": "0.4",
            "c_exp": "0",
            "py_exp": "0",
            "research": "AI",
            "personal_email": "saranyamtech12@gmail.com"
        },
        {
            "name": "Anusha S",
            "email": "anusha.s@kgkite.ac.in",
            "phone": "8056008866",
            "dept": "CYS",
            "image": "faculty8.jpg",
            "linkedin": "",
            "github": "https://github.com/Anusha-1989",
            "experience": "12.5",
            "c_exp": "0",
            "py_exp": "1",
            "research": "Data Science",
            "personal_email": "anusha76anu@gmail.com"
        },
        {
            "name": "Kiruthikaa R",
            "email": "kiruthikaa.r@kgkite.ac.in",
            "phone": "6382754523",
            "dept": "ECE-A",
            "image": "faculty9.jpg",
            "linkedin": "https://www.linkedin.com/in/kiruthikaa-r-42596a332/",
            "github": "https://github.com/Kiruthikaa06",
            "experience": "8.5",
            "c_exp": "1",
            "py_exp": "1",
            "research": "IoT & Embedded Systems",
            "personal_email": "kiruthikaar27@gmail.com"
        },
        {
            "name": "Janani R",
            "email": "janani.r@kgkite.ac.in",
            "phone": "9488762688",
            "dept": "ECE-B",
            "image": "faculty10.jpg",
            "linkedin": "https://www.linkedin.com/in/janani-ramannachetty-43b892137/",
            "github": "https://github.com/Jananir22",
            "experience": "2.5",
            "c_exp": "0",
            "py_exp": "0",
            "research": "Machine Learning",
            "personal_email": "jananiramannachetty@gmail.com"
        },
        {
            "name": "Venkatesh Babu S",
            "email": "Venkateshbabu.s@kgkite.ac.in",
            "phone": "9790197267",
            "dept": "IT-A",
            "image": "faculty11.jpg",
            "linkedin": "https://www.linkedin.com/in/venkateshbabusakthinarayanan/",
            "github": "",
            "experience": "20",
            "c_exp": "",
            "py_exp": "",
            "research": "",
            "personal_email": ""
        },
        {
            "name": "Dhamayanthi P",
            "email": "dhamayanthi.p@kgkite.ac.in",
            "phone": "8220279253",
            "dept": "IT-B",
            "image": "faculty12.jpg",
            "linkedin": "https://www.linkedin.com/in/dhamayanthi-satishkumar-580135104",
            "github": "https://github.com/Dhamayanthi-ME/Dhamayanthi",
            "experience": "5.1",
            "c_exp": "0",
            "py_exp": "0",
            "research": "Machine Learning",
            "personal_email": "damyanti.me@gmail.com"
        },
        {
            "name": "Pradeep G",
            "email": "pradeep.g@kgkite.ac.in",
            "phone": "9600018957",
            "dept": "MECH",
            "image": "faculty13.jpg",
            "linkedin": "https://www.linkedin.com/in/pradeep-g-b7275b46/",
            "github": "https://github.com/pradeepgkite",
            "experience": "9",
            "c_exp": "0",
            "py_exp": "0",
            "research": "Deep Learning",
            "personal_email": "pradeep.be2012@gmail.com"
        },
        {
            "name": "Madhan S",
            "email": "madhan.m@kgkite.ac.in",
            "phone": "8344108003",
            "dept": "RA",
            "image": "faculty14.jpg",
            "linkedin": "https://www.linkedin.com/in/madhan-m-9a0ba639/",
            "github": "",
            "experience": "0.4",
            "c_exp": "0",
            "py_exp": "0",
            "research": "Deep Learning",
            "personal_email": "madhanagathyam@gmail.com"
        },
    ]
    
    for faculty_data in faculties_data:
        faculty = Faculty(
            name=faculty_data["name"],
            email=faculty_data["email"],
            password=pwd_context.hash("Kgisl@12345"),  # Default password
            phone=faculty_data["phone"],
            image_url=f"/static/images/{faculty_data['image']}",
            linkedin_url=faculty_data["linkedin"],
            github_url=faculty_data["github"],
            department=faculty_data["dept"],
            experience=faculty_data["experience"],
            c_experience=faculty_data["c_exp"],
            py_experience=faculty_data["py_exp"],
            research_area=faculty_data["research"],
            personal_email=faculty_data["personal_email"]
        )
        db.add(faculty)
    
    db.commit()
    
    # Now add mock timetable entries
    # Get faculty and department IDs
    faculties = db.query(Faculty).all()
    departments = db.query(Department).all()
        
    # class_type: "theory" (1 period), "lab" (3 consecutive periods), "mini_project" (1 period)
    mock_timetable = [
        # Faculty 1 - Mr. Sathish R handles AI&DS-A
        # Tuesday: Theory (1 period)
        {"faculty_id": 1, "dept_code": "AI&DS-A", "day": "Tuesday", "period": 7, "class_type": "theory"},
        # Wednesday: mini_project (1 period) + Lab (3 periods)                  
        {"faculty_id": 1, "dept_code": "AI&DS-A", "day": "Wednesday", "period": 5, "class_type": "mini_project"},
        {"faculty_id": 1, "dept_code": "AI&DS-A", "day": "Wednesday", "period": 6, "class_type": "lab"},
        {"faculty_id": 1, "dept_code": "AI&DS-A", "day": "Wednesday", "period": 7, "class_type": "lab"},
        {"faculty_id": 1, "dept_code": "AI&DS-A", "day": "Wednesday", "period": 8, "class_type": "lab"},
        # Thursday: Theory(2 periods)
        {"faculty_id": 1, "dept_code": "AI&DS-A", "day": "Thursday", "period": 8, "class_type": "theory"},
        # Friday: Theory
        {"faculty_id": 1, "dept_code": "AI&DS-A", "day": "Friday", "period": 5, "class_type": "theory"},
        # Saturday: Theory
        {"faculty_id": 1, "dept_code": "AI&DS-A", "day": "Saturday", "period": 7, "class_type": "theory"},
        
        # Faculty 2 - Dr. Sikkandhar Batcha J handles AI&DS-B
        {"faculty_id": 2, "dept_code": "AI&DS-B", "day": "Monday", "period": 5, "class_type": "theory"},
        {"faculty_id": 2, "dept_code": "AI&DS-B", "day": "Wednesday", "period": 3, "class_type": "lab"},
        {"faculty_id": 2, "dept_code": "AI&DS-B", "day": "Wednesday", "period": 4, "class_type": "lab"},
        {"faculty_id": 2, "dept_code": "AI&DS-B", "day": "Wednesday", "period": 5, "class_type": "lab"},
        {"faculty_id": 2, "dept_code": "AI&DS-B", "day": "Wednesday", "period": 7, "class_type": "mini_project"},
        {"faculty_id": 2, "dept_code": "AI&DS-B", "day": "Thursday", "period": 2, "class_type": "theory"},
        {"faculty_id": 2, "dept_code": "AI&DS-B", "day": "Friday", "period": 4, "class_type": "theory"},
        {"faculty_id": 2, "dept_code": "AI&DS-B", "day": "Saturday", "period": 5, "class_type": "theory"},
        
        # Faculty 3 - Mr. Raakesh M handles AI&ML-A
        {"faculty_id": 3, "dept_code": "AI&ML-A", "day": "Monday", "period": 5, "class_type": "theory"},
        {"faculty_id": 3, "dept_code": "AI&ML-A", "day": "Tuesday", "period": 7, "class_type": "theory"},
        {"faculty_id": 3, "dept_code": "AI&ML-A", "day": "Thursday", "period": 2, "class_type": "mini_project"},
        {"faculty_id": 3, "dept_code": "AI&ML-A", "day": "Thursday", "period": 3, "class_type": "lab"},
        {"faculty_id": 3, "dept_code": "AI&ML-A", "day": "Thursday", "period": 4, "class_type": "lab"},
        {"faculty_id": 3, "dept_code": "AI&ML-A", "day": "Thursday", "period": 5, "class_type": "lab"},
        {"faculty_id": 3, "dept_code": "AI&ML-A", "day": "Friday", "period": 2, "class_type": "theory"},
        {"faculty_id": 3, "dept_code": "AI&ML-A", "day": "Saturday", "period": 8, "class_type": "theory"},
        
        # Faculty 4 - Dr. Aruna R handles AI&ML-B
        {"faculty_id": 4, "dept_code": "AI&ML-B", "day": "Monday", "period": 5, "class_type": "theory"},
        {"faculty_id": 4, "dept_code": "AI&ML-B", "day": "Tuesday", "period": 6, "class_type": "theory"},
        {"faculty_id": 4, "dept_code": "AI&ML-B", "day": "Wednesday", "period": 7, "class_type": "mini_project"},
        {"faculty_id": 4, "dept_code": "AI&ML-B", "day": "Wednesday", "period": 8, "class_type": "theory"},
        {"faculty_id": 4, "dept_code": "AI&ML-B", "day": "Thursday", "period": 6, "class_type": "lab"},
        {"faculty_id": 4, "dept_code": "AI&ML-B", "day": "Thursday", "period": 7, "class_type": "lab"},
        {"faculty_id": 4, "dept_code": "AI&ML-B", "day": "Thursday", "period": 8, "class_type": "lab"},
        {"faculty_id": 4, "dept_code": "AI&ML-B", "day": "Saturday", "period": 2, "class_type": "theory"},
        
        # Faculty 5 - Ms. Janani S handles CSE-A
        {"faculty_id": 5, "dept_code": "CSE-A", "day": "Monday", "period": 2, "class_type": "theory"},
        {"faculty_id": 5, "dept_code": "CSE-A", "day": "Wednesday", "period": 2, "class_type": "mini_project"},
        {"faculty_id": 5, "dept_code": "CSE-A", "day": "Wednesday", "period": 6, "class_type": "lab"},
        {"faculty_id": 5, "dept_code": "CSE-A", "day": "Wednesday", "period": 7, "class_type": "lab"},
        {"faculty_id": 5, "dept_code": "CSE-A", "day": "Wednesday", "period": 8, "class_type": "lab"},
        {"faculty_id": 5, "dept_code": "CSE-A", "day": "Thursday", "period": 3, "class_type": "theory"},
        {"faculty_id": 5, "dept_code": "CSE-A", "day": "Friday", "period": 6, "class_type": "theory"},
        {"faculty_id": 5, "dept_code": "CSE-A", "day": "Saturday", "period": 6, "class_type": "theory"},
        # Faculty 6 - Ms. Indhumathi S handles CSE-B
        {"faculty_id": 6, "dept_code": "CSE-B", "day": "Monday", "period": 2, "class_type": "theory"},
        {"faculty_id": 6, "dept_code": "CSE-B", "day": "Wednesday", "period": 5, "class_type": "theory"},
        {"faculty_id": 6, "dept_code": "CSE-B", "day": "Thursday", "period": 3, "class_type": "theory"},
        {"faculty_id": 6, "dept_code": "CSE-B", "day": "Friday", "period": 2, "class_type": "mini_project"},
        {"faculty_id": 6, "dept_code": "CSE-B", "day": "Friday", "period": 3, "class_type": "lab"},
        {"faculty_id": 6, "dept_code": "CSE-B", "day": "Friday", "period": 4, "class_type": "lab"},
        {"faculty_id": 6, "dept_code": "CSE-B", "day": "Friday", "period": 5, "class_type": "lab"},
        {"faculty_id": 6, "dept_code": "CSE-B", "day": "Saturday", "period": 7, "class_type": "theory"},
        
        # Faculty 7 - Ms. Saranya S handles CSBS
        {"faculty_id": 7, "dept_code": "CSBS", "day": "Tuesday", "period": 2, "class_type": "theory"},
        {"faculty_id": 7, "dept_code": "CSBS", "day": "Wednesday", "period": 2, "class_type": "mini_project"},
        {"faculty_id": 7, "dept_code": "CSBS", "day": "Wednesday", "period": 3, "class_type": "lab"},
        {"faculty_id": 7, "dept_code": "CSBS", "day": "Wednesday", "period": 4, "class_type": "lab"},
        {"faculty_id": 7, "dept_code": "CSBS", "day": "Wednesday", "period": 5, "class_type": "lab"},
        {"faculty_id": 7, "dept_code": "CSBS", "day": "Thursday", "period": 8, "class_type": "theory"},
        {"faculty_id": 7, "dept_code": "CSBS", "day": "Friday", "period": 5, "class_type": "theory"},
        {"faculty_id": 7, "dept_code": "CSBS", "day": "Saturday", "period": 7, "class_type": "theory"},
        
        # Faculty 8 - Ms. Anusha S handles CYS
        {"faculty_id": 8, "dept_code": "CYS", "day": "Monday", "period": 8, "class_type": "theory"},
        {"faculty_id": 8, "dept_code": "CYS", "day": "Wednesday", "period": 3, "class_type": "theory"},
        {"faculty_id": 8, "dept_code": "CYS", "day": "Thursday", "period": 2, "class_type": "mini_project"},
        {"faculty_id": 8, "dept_code": "CYS", "day": "Thursday", "period": 3, "class_type": "lab"},
        {"faculty_id": 8, "dept_code": "CYS", "day": "Thursday", "period": 4, "class_type": "lab"},
        {"faculty_id": 8, "dept_code": "CYS", "day": "Thursday", "period": 5, "class_type": "lab"},
        {"faculty_id": 8, "dept_code": "CYS", "day": "Friday", "period": 6, "class_type": "theory"},
        {"faculty_id": 8, "dept_code": "CYS", "day": "Saturday", "period": 3, "class_type": "theory"},
        
        # Faculty 9 - Ms. Kiruthikaa R handles ECE-A
        {"faculty_id": 9, "dept_code": "ECE-A", "day": "Tuesday", "period": 3, "class_type": "lab"},
        {"faculty_id": 9, "dept_code": "ECE-A", "day": "Tuesday", "period": 4, "class_type": "lab"},
        {"faculty_id": 9, "dept_code": "ECE-A", "day": "Tuesday", "period": 5, "class_type": "lab"},

        {"faculty_id": 9, "dept_code": "ECE-A", "day": "Tuesday", "period": 6, "class_type": "mini_project"},

        {"faculty_id": 9, "dept_code": "ECE-A", "day": "Wednesday", "period": 2, "class_type": "theory"},

        {"faculty_id": 9, "dept_code": "ECE-A", "day": "Thursday", "period": 6, "class_type": "theory"},

        {"faculty_id": 9, "dept_code": "ECE-A", "day": "Friday", "period": 5, "class_type": "theory"},

        {"faculty_id": 9, "dept_code": "ECE-A", "day": "Saturday", "period": 6, "class_type": "theory"},

        
        # Faculty 10 - Ms. Janani R handles ECE-B
        {"faculty_id": 10, "dept_code": "ECE-B", "day": "Monday", "period": 6, "class_type": "theory"},
        {"faculty_id": 10, "dept_code": "ECE-B", "day": "Tuesday", "period": 7, "class_type": "theory"},
        {"faculty_id": 10, "dept_code": "ECE-B", "day": "Wednesday", "period": 5, "class_type": "mini_project"},
        {"faculty_id": 10, "dept_code": "ECE-B", "day": "Wednesday", "period": 6, "class_type": "lab"},
        {"faculty_id": 10, "dept_code": "ECE-B", "day": "Wednesday", "period": 7, "class_type": "lab"},
        {"faculty_id": 10, "dept_code": "ECE-B", "day": "Wednesday", "period": 8, "class_type": "lab"},
        {"faculty_id": 10, "dept_code": "ECE-B", "day": "Thursday", "period": 2, "class_type": "theory"},
        {"faculty_id": 10, "dept_code": "ECE-B", "day": "Saturday", "period": 5, "class_type": "theory"},
        
        # Faculty 11 - Mr. Venkatesh Babu S handles IT-A
        {"faculty_id": 11, "dept_code": "IT-A", "day": "Tuesday", "period": 2, "class_type": "theory"},
        {"faculty_id": 11, "dept_code": "IT-A", "day": "Tuesday", "period": 5, "class_type": "mini_project"},
        {"faculty_id": 11, "dept_code": "IT-A", "day": "Tuesday", "period": 6, "class_type": "lab"},
        {"faculty_id": 11, "dept_code": "IT-A", "day": "Tuesday", "period": 7, "class_type": "lab"},
        {"faculty_id": 11, "dept_code": "IT-A", "day": "Tuesday", "period": 8, "class_type": "lab"},
        {"faculty_id": 11, "dept_code": "IT-A", "day": "Wednesday", "period": 5, "class_type": "theory"},
        {"faculty_id": 11, "dept_code": "IT-A", "day": "Friday", "period": 6, "class_type": "theory"},
        {"faculty_id": 11, "dept_code": "IT-A", "day": "Saturday", "period": 8, "class_type": "theory"},
        
        # Faculty 12 - Ms. Dhamayanthi P handles IT-B   
        {"faculty_id": 12, "dept_code": "IT-B", "day": "Monday", "period": 8, "class_type": "theory"},
        {"faculty_id": 12, "dept_code": "IT-B", "day": "Wednesday", "period": 2, "class_type": "theory"},
        {"faculty_id": 12, "dept_code": "IT-B", "day": "Thursday", "period": 5, "class_type": "mini_project"},
        {"faculty_id": 12, "dept_code": "IT-B", "day": "Thursday", "period": 6, "class_type": "lab"},
        {"faculty_id": 12, "dept_code": "IT-B", "day": "Thursday", "period": 7, "class_type": "lab"},
        {"faculty_id": 12, "dept_code": "IT-B", "day": "Thursday", "period": 8, "class_type": "lab"},
        {"faculty_id": 12, "dept_code": "IT-B", "day": "Friday", "period": 6, "class_type": "theory"},
        {"faculty_id": 12, "dept_code": "IT-B", "day": "Saturday", "period":7, "class_type": "theory"},
        
        # Faculty 13 - Mr. Pradeep G handles MECH
        {"faculty_id": 13, "dept_code": "MECH", "day": "Monday", "period": 3, "class_type": "theory"},
        {"faculty_id": 13, "dept_code": "MECH", "day": "Monday", "period": 7, "class_type": "theory"},
        {"faculty_id": 13, "dept_code": "MECH", "day": "Thursday", "period": 6, "class_type": "theory"},
        {"faculty_id": 13, "dept_code": "MECH", "day": "Friday", "period": 5, "class_type": "mini_project"},
        {"faculty_id": 13, "dept_code": "MECH", "day": "Friday", "period": 6, "class_type": "lab"},
        {"faculty_id": 13, "dept_code": "MECH", "day": "Friday", "period": 7, "class_type": "lab"},
        {"faculty_id": 13, "dept_code": "MECH", "day": "Friday", "period": 8, "class_type": "lab"},
        {"faculty_id": 13, "dept_code": "MECH", "day": "Saturday", "period": 4, "class_type": "theory"},

        # Faculty 14 - Mr. Madhan S handles RA
        {"faculty_id": 14, "dept_code": "RA", "day": "Monday", "period": 2, "class_type": "theory"},
        {"faculty_id": 14, "dept_code": "RA", "day": "Tuesday", "period": 4, "class_type": "theory"},
        {"faculty_id": 14, "dept_code": "RA", "day": "Tuesday", "period": 8, "class_type": "theory"},
        {"faculty_id": 14, "dept_code": "RA", "day": "Friday", "period": 5, "class_type": "mini_project"},
        {"faculty_id": 14, "dept_code": "RA", "day": "Friday", "period": 6, "class_type": "lab"},
        {"faculty_id": 14, "dept_code": "RA", "day": "Friday", "period": 7, "class_type": "lab"},
        {"faculty_id": 14, "dept_code": "RA", "day": "Friday", "period": 8, "class_type": "lab"},
        {"faculty_id": 14, "dept_code": "RA", "day": "Saturday", "period": 2, "class_type": "theory"},              
    ]
    
    dept_map = {d.code: d.id for d in departments}
    
    for entry in mock_timetable:
        timetable = TimetableEntry(
            faculty_id=entry["faculty_id"],
            department_id=dept_map[entry["dept_code"]],
            day=entry["day"],
            period=entry["period"],
            subject_code="24UCS271",
            subject_name="C Programming",
            class_type=entry["class_type"]
        )
        db.add(timetable)
    
    db.commit()
    print("✓ Database initialized successfully!")
    print("\n" + "="*50)
    print("SECRET URLs (Share only with authorized users):")
    print("="*50)
    print("\n📋 Admin Dashboard (Public View):")
    print("   /cprog_admin_view_x7k9")
    print("\n🔐 Faculty & Super Admin Login:")
    print("   /cprog_portal_m2p8")
    print("\n👨‍🏫 Faculty Dashboard (after login):")
    print("   /cprog_faculty_dash_q4w1")
    print("\n👑 Super Admin Dashboard (after login):")
    print("   /cprog_super_dash_z9y3")
    print("\n" + "="*50)
    print("Login Credentials:")
    print("="*50)
    print("  Super Admin: super_admin@gmail.com / superadmin123")
    print("  Faculty: <email> / Kgisl@12345")
    print("\n⚠️  Old URLs (/, /login, /admin, etc.) return 404!")

if __name__ == "__main__":
    init_database()
