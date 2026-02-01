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
    
    # Add faculties (14 faculties from DATAS.TXT)
    # Images should be stored in static/images/ folder with filenames like: faculty1.jpg, faculty2.jpg, etc.
    faculties_data = [
        {
            "name": "Sathish R",
            "email": "r.sathish@kgkite.ac.in",
            "phone": "9791406167",
            "dept": "AIDS-A",
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
            "dept": "AIDS-B",
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
            "name": "Anitha M",
            "email": "anitha.m@kgkite.ac.in",
            "phone": "9597942750",
            "dept": "AIML-A",
            "image": "faculty3.jpg",
            "linkedin": "https://www.linkedin.com/in/anitha-vimal-152295345",
            "github": "https://github.com/anithavimal666",
            "experience": "12",
            "c_exp": "2",
            "py_exp": "2",
            "research": "Big Data Analytics with Deep Learning",
            "personal_email": "manithatce@gmail.com"
        },
        {
            "name": "Aruna R",
            "email": "aruna.r@kgkite.ac.in",
            "phone": "9585458088",
            "dept": "AIML-B",
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
            password=pwd_context.hash("password123"),  # Default password
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
    
    # Mock timetable - distributing classes among faculties
    # Each faculty handles 1-2 departments
    mock_timetable = [
        # Faculty 1 - Dr. Ramesh Kumar handles AIDS-A
        {"faculty_id": 1, "dept_code": "AIDS-A", "day": "Sunday", "period": 7},
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
