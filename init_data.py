from database import engine, SessionLocal
from models import Base, Department, Syllabus, Admin, Faculty, TimetableEntry
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if data already exists
    if db.query(Department).first():
        print("Database already initialized!")
        db.close()
        return
    
    # Add Departments
    departments = [
        {"name": "B.Tech AI&DS - A", "code": "AIDS-A"},
        {"name": "B.Tech AI&DS - B", "code": "AIDS-B"},
        {"name": "B.Tech AI&ML - A", "code": "AIML-A"},
        {"name": "B.Tech AI&ML - B", "code": "AIML-B"},
        {"name": "B.Tech CSBS", "code": "CSBS"},
        {"name": "B.Tech CSE - A", "code": "CSE-A"},
        {"name": "B.Tech CSE - B", "code": "CSE-B"},
        {"name": "B.Tech CYS", "code": "CYS"},
        {"name": "B.Tech ECE - A", "code": "ECE-A"},
        {"name": "B.Tech ECE - B", "code": "ECE-B"},
        {"name": "B.Tech IT - A", "code": "IT-A"},
        {"name": "B.Tech IT - B", "code": "IT-B"},
        {"name": "B.Tech MECH", "code": "MECH"},
        {"name": "B.Tech RA", "code": "RA"},
    ]
    
    for dept in departments:
        db.add(Department(**dept))
    
    # Add C Programming Syllabus Topics
    syllabus_topics = [
        # Unit 1 - Introduction
        {"topic_name": "Introduction to C Programming", "unit": 1, "order_num": 1},
        {"topic_name": "History and Features of C", "unit": 1, "order_num": 2},
        {"topic_name": "Structure of C Program", "unit": 1, "order_num": 3},
        {"topic_name": "Compilation and Execution", "unit": 1, "order_num": 4},
        {"topic_name": "Variables and Constants", "unit": 1, "order_num": 5},
        {"topic_name": "Data Types in C", "unit": 1, "order_num": 6},
        {"topic_name": "Operators in C", "unit": 1, "order_num": 7},
        {"topic_name": "Type Conversion and Casting", "unit": 1, "order_num": 8},
        
        # Unit 2 - Control Statements
        {"topic_name": "Decision Making - if statement", "unit": 2, "order_num": 9},
        {"topic_name": "Decision Making - if-else statement", "unit": 2, "order_num": 10},
        {"topic_name": "Decision Making - nested if-else", "unit": 2, "order_num": 11},
        {"topic_name": "Decision Making - switch statement", "unit": 2, "order_num": 12},
        {"topic_name": "Loops - for loop", "unit": 2, "order_num": 13},
        {"topic_name": "Loops - while loop", "unit": 2, "order_num": 14},
        {"topic_name": "Loops - do-while loop", "unit": 2, "order_num": 15},
        {"topic_name": "Break and Continue statements", "unit": 2, "order_num": 16},
        {"topic_name": "Goto statement", "unit": 2, "order_num": 17},
        
        # Unit 3 - Arrays and Strings
        {"topic_name": "Introduction to Arrays", "unit": 3, "order_num": 18},
        {"topic_name": "One Dimensional Arrays", "unit": 3, "order_num": 19},
        {"topic_name": "Two Dimensional Arrays", "unit": 3, "order_num": 20},
        {"topic_name": "Multi Dimensional Arrays", "unit": 3, "order_num": 21},
        {"topic_name": "Introduction to Strings", "unit": 3, "order_num": 22},
        {"topic_name": "String Functions", "unit": 3, "order_num": 23},
        {"topic_name": "String Manipulation Programs", "unit": 3, "order_num": 24},
        
        # Unit 4 - Functions
        {"topic_name": "Introduction to Functions", "unit": 4, "order_num": 25},
        {"topic_name": "Function Declaration and Definition", "unit": 4, "order_num": 26},
        {"topic_name": "Function Call - Call by Value", "unit": 4, "order_num": 27},
        {"topic_name": "Function Call - Call by Reference", "unit": 4, "order_num": 28},
        {"topic_name": "Recursion", "unit": 4, "order_num": 29},
        {"topic_name": "Storage Classes", "unit": 4, "order_num": 30},
        
        # Unit 5 - Pointers
        {"topic_name": "Introduction to Pointers", "unit": 5, "order_num": 31},
        {"topic_name": "Pointer Declaration and Initialization", "unit": 5, "order_num": 32},
        {"topic_name": "Pointer Arithmetic", "unit": 5, "order_num": 33},
        {"topic_name": "Pointers and Arrays", "unit": 5, "order_num": 34},
        {"topic_name": "Pointers and Strings", "unit": 5, "order_num": 35},
        {"topic_name": "Pointers and Functions", "unit": 5, "order_num": 36},
        {"topic_name": "Pointer to Pointer", "unit": 5, "order_num": 37},
        {"topic_name": "Dynamic Memory Allocation", "unit": 5, "order_num": 38},
        
        # Unit 6 - Structures and Unions
        {"topic_name": "Introduction to Structures", "unit": 6, "order_num": 39},
        {"topic_name": "Structure Declaration and Initialization", "unit": 6, "order_num": 40},
        {"topic_name": "Accessing Structure Members", "unit": 6, "order_num": 41},
        {"topic_name": "Array of Structures", "unit": 6, "order_num": 42},
        {"topic_name": "Nested Structures", "unit": 6, "order_num": 43},
        {"topic_name": "Structures and Functions", "unit": 6, "order_num": 44},
        {"topic_name": "Structures and Pointers", "unit": 6, "order_num": 45},
        {"topic_name": "Introduction to Unions", "unit": 6, "order_num": 46},
        {"topic_name": "Difference between Structure and Union", "unit": 6, "order_num": 47},
        
        # Unit 7 - File Handling
        {"topic_name": "Introduction to File Handling", "unit": 7, "order_num": 48},
        {"topic_name": "File Opening and Closing", "unit": 7, "order_num": 49},
        {"topic_name": "Reading from Files", "unit": 7, "order_num": 50},
        {"topic_name": "Writing to Files", "unit": 7, "order_num": 51},
        {"topic_name": "File Positioning", "unit": 7, "order_num": 52},
        {"topic_name": "Error Handling in Files", "unit": 7, "order_num": 53},
    ]
    
    for topic in syllabus_topics:
        db.add(Syllabus(**topic))
    
    # Add default admin
    admin = Admin(
        username="admin",
        password=pwd_context.hash("admin123")
    )
    db.add(admin)
    
    # Add mock faculties (14 faculties)
    mock_faculties = [
        {"name": "Dr. Ramesh Kumar", "email": "ramesh@college.edu", "phone": "9876543210"},
        {"name": "Ms. Priya Sharma", "email": "priya@college.edu", "phone": "9876543211"},
        {"name": "Mr. Arun Prakash", "email": "arun@college.edu", "phone": "9876543212"},
        {"name": "Dr. Lakshmi Narayanan", "email": "lakshmi@college.edu", "phone": "9876543213"},
        {"name": "Ms. N. Backiyalakshmi", "email": "backiya@college.edu", "phone": "9876543214"},
        {"name": "Mr. Senthil Kumar", "email": "senthil@college.edu", "phone": "9876543215"},
        {"name": "Dr. Vijay Anand", "email": "vijay@college.edu", "phone": "9876543216"},
        {"name": "Ms. Deepa Krishnan", "email": "deepa@college.edu", "phone": "9876543217"},
        {"name": "Mr. Karthik Raja", "email": "karthik@college.edu", "phone": "9876543218"},
        {"name": "Dr. Meena Sundaram", "email": "meena@college.edu", "phone": "9876543219"},
        {"name": "Mr. Rajesh Babu", "email": "rajesh@college.edu", "phone": "9876543220"},
        {"name": "Ms. Anjali Devi", "email": "anjali@college.edu", "phone": "9876543221"},
        {"name": "Dr. Suresh Rajan", "email": "suresh@college.edu", "phone": "9876543222"},
        {"name": "Mr. Gopal Krishnan", "email": "gopal@college.edu", "phone": "9876543223"},
    ]
    
    for faculty_data in mock_faculties:
        faculty = Faculty(
            name=faculty_data["name"],
            email=faculty_data["email"],
            password=pwd_context.hash("password123"),  # Default password
            phone=faculty_data["phone"]
        )
        db.add(faculty)
    
    db.commit()
    
    # Now add mock timetable entries
    # Get faculty and department IDs
    faculties = db.query(Faculty).all()
    departments = db.query(Department).all()
    
    # Mock timetable - distributing classes among faculties
    # Each faculty handles 1-2 departments
    mock_timetable = [
        # Faculty 1 - Dr. Ramesh Kumar handles AIDS-A
        {"faculty_id": 1, "dept_code": "AIDS-A", "day": "Tuesday", "period": 7},
        {"faculty_id": 1, "dept_code": "AIDS-A", "day": "Wednesday", "period": 5},
        {"faculty_id": 1, "dept_code": "AIDS-A", "day": "Wednesday", "period": 7},
        {"faculty_id": 1, "dept_code": "AIDS-A", "day": "Thursday", "period": 7},
        {"faculty_id": 1, "dept_code": "AIDS-A", "day": "Thursday", "period": 8},
        {"faculty_id": 1, "dept_code": "AIDS-A", "day": "Thursday", "period": 9},
        {"faculty_id": 1, "dept_code": "AIDS-A", "day": "Friday", "period": 5},
        {"faculty_id": 1, "dept_code": "AIDS-A", "day": "Saturday", "period": 7},
        
        # Faculty 2 - Ms. Priya Sharma handles AIDS-B
        {"faculty_id": 2, "dept_code": "AIDS-B", "day": "Monday", "period": 3},
        {"faculty_id": 2, "dept_code": "AIDS-B", "day": "Tuesday", "period": 5},
        {"faculty_id": 2, "dept_code": "AIDS-B", "day": "Wednesday", "period": 2},
        {"faculty_id": 2, "dept_code": "AIDS-B", "day": "Thursday", "period": 6},
        {"faculty_id": 2, "dept_code": "AIDS-B", "day": "Friday", "period": 4},
        
        # Faculty 3 - Mr. Arun Prakash handles AIML-A
        {"faculty_id": 3, "dept_code": "AIML-A", "day": "Monday", "period": 2},
        {"faculty_id": 3, "dept_code": "AIML-A", "day": "Tuesday", "period": 4},
        {"faculty_id": 3, "dept_code": "AIML-A", "day": "Wednesday", "period": 6},
        {"faculty_id": 3, "dept_code": "AIML-A", "day": "Thursday", "period": 3},
        {"faculty_id": 3, "dept_code": "AIML-A", "day": "Friday", "period": 1},
        
        # Faculty 4 - Dr. Lakshmi Narayanan handles AIML-B
        {"faculty_id": 4, "dept_code": "AIML-B", "day": "Monday", "period": 4},
        {"faculty_id": 4, "dept_code": "AIML-B", "day": "Tuesday", "period": 2},
        {"faculty_id": 4, "dept_code": "AIML-B", "day": "Wednesday", "period": 3},
        {"faculty_id": 4, "dept_code": "AIML-B", "day": "Thursday", "period": 5},
        {"faculty_id": 4, "dept_code": "AIML-B", "day": "Friday", "period": 6},
        
        # Faculty 5 - Ms. N. Backiyalakshmi handles CSBS
        {"faculty_id": 5, "dept_code": "CSBS", "day": "Monday", "period": 1},
        {"faculty_id": 5, "dept_code": "CSBS", "day": "Tuesday", "period": 3},
        {"faculty_id": 5, "dept_code": "CSBS", "day": "Wednesday", "period": 4},
        {"faculty_id": 5, "dept_code": "CSBS", "day": "Thursday", "period": 2},
        {"faculty_id": 5, "dept_code": "CSBS", "day": "Friday", "period": 7},
        
        # Faculty 6 - Mr. Senthil Kumar handles CSE-A
        {"faculty_id": 6, "dept_code": "CSE-A", "day": "Monday", "period": 5},
        {"faculty_id": 6, "dept_code": "CSE-A", "day": "Tuesday", "period": 1},
        {"faculty_id": 6, "dept_code": "CSE-A", "day": "Wednesday", "period": 7},
        {"faculty_id": 6, "dept_code": "CSE-A", "day": "Thursday", "period": 4},
        {"faculty_id": 6, "dept_code": "CSE-A", "day": "Friday", "period": 2},
        
        # Faculty 7 - Dr. Vijay Anand handles CSE-B
        {"faculty_id": 7, "dept_code": "CSE-B", "day": "Monday", "period": 6},
        {"faculty_id": 7, "dept_code": "CSE-B", "day": "Tuesday", "period": 6},
        {"faculty_id": 7, "dept_code": "CSE-B", "day": "Wednesday", "period": 1},
        {"faculty_id": 7, "dept_code": "CSE-B", "day": "Thursday", "period": 7},
        {"faculty_id": 7, "dept_code": "CSE-B", "day": "Friday", "period": 3},
        
        # Faculty 8 - Ms. Deepa Krishnan handles CYS
        {"faculty_id": 8, "dept_code": "CYS", "day": "Monday", "period": 7},
        {"faculty_id": 8, "dept_code": "CYS", "day": "Tuesday", "period": 7},
        {"faculty_id": 8, "dept_code": "CYS", "day": "Wednesday", "period": 8},
        {"faculty_id": 8, "dept_code": "CYS", "day": "Thursday", "period": 1},
        {"faculty_id": 8, "dept_code": "CYS", "day": "Friday", "period": 8},
        
        # Faculty 9 - Mr. Karthik Raja handles ECE-A
        {"faculty_id": 9, "dept_code": "ECE-A", "day": "Monday", "period": 8},
        {"faculty_id": 9, "dept_code": "ECE-A", "day": "Tuesday", "period": 8},
        {"faculty_id": 9, "dept_code": "ECE-A", "day": "Wednesday", "period": 9},
        {"faculty_id": 9, "dept_code": "ECE-A", "day": "Thursday", "period": 8},
        {"faculty_id": 9, "dept_code": "ECE-A", "day": "Friday", "period": 9},
        
        # Faculty 10 - Dr. Meena Sundaram handles ECE-B
        {"faculty_id": 10, "dept_code": "ECE-B", "day": "Monday", "period": 9},
        {"faculty_id": 10, "dept_code": "ECE-B", "day": "Tuesday", "period": 9},
        {"faculty_id": 10, "dept_code": "ECE-B", "day": "Thursday", "period": 9},
        {"faculty_id": 10, "dept_code": "ECE-B", "day": "Friday", "period": 5},
        {"faculty_id": 10, "dept_code": "ECE-B", "day": "Saturday", "period": 1},
        
        # Faculty 11 - Mr. Rajesh Babu handles IT-A
        {"faculty_id": 11, "dept_code": "IT-A", "day": "Monday", "period": 3},
        {"faculty_id": 11, "dept_code": "IT-A", "day": "Wednesday", "period": 2},
        {"faculty_id": 11, "dept_code": "IT-A", "day": "Thursday", "period": 6},
        {"faculty_id": 11, "dept_code": "IT-A", "day": "Saturday", "period": 2},
        {"faculty_id": 11, "dept_code": "IT-A", "day": "Saturday", "period": 3},
        
        # Faculty 12 - Ms. Anjali Devi handles IT-B
        {"faculty_id": 12, "dept_code": "IT-B", "day": "Monday", "period": 2},
        {"faculty_id": 12, "dept_code": "IT-B", "day": "Tuesday", "period": 4},
        {"faculty_id": 12, "dept_code": "IT-B", "day": "Wednesday", "period": 6},
        {"faculty_id": 12, "dept_code": "IT-B", "day": "Saturday", "period": 4},
        {"faculty_id": 12, "dept_code": "IT-B", "day": "Saturday", "period": 5},
        
        # Faculty 13 - Dr. Suresh Rajan handles MECH
        {"faculty_id": 13, "dept_code": "MECH", "day": "Monday", "period": 4},
        {"faculty_id": 13, "dept_code": "MECH", "day": "Tuesday", "period": 2},
        {"faculty_id": 13, "dept_code": "MECH", "day": "Wednesday", "period": 3},
        {"faculty_id": 13, "dept_code": "MECH", "day": "Saturday", "period": 6},
        {"faculty_id": 13, "dept_code": "MECH", "day": "Saturday", "period": 8},
        
        # Faculty 14 - Mr. Gopal Krishnan handles RA
        {"faculty_id": 14, "dept_code": "RA", "day": "Monday", "period": 5},
        {"faculty_id": 14, "dept_code": "RA", "day": "Tuesday", "period": 1},
        {"faculty_id": 14, "dept_code": "RA", "day": "Wednesday", "period": 4},
        {"faculty_id": 14, "dept_code": "RA", "day": "Saturday", "period": 7},
        {"faculty_id": 14, "dept_code": "RA", "day": "Saturday", "period": 9},
    ]
    
    dept_map = {d.code: d.id for d in departments}
    
    for entry in mock_timetable:
        timetable = TimetableEntry(
            faculty_id=entry["faculty_id"],
            department_id=dept_map[entry["dept_code"]],
            day=entry["day"],
            period=entry["period"],
            subject_code="24UCS271",
            subject_name="C Programming"
        )
        db.add(timetable)
    
    db.commit()
    db.close()
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()
