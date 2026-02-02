# C Programming Faculty Management System

A web application for managing C Programming faculty schedules, daily entries, and an AI-powered chatbot for quick information.

## Features

- 👨‍🏫 **Faculty Portal**: Register, login, and fill daily class schedules
- 🔐 **Admin Dashboard**: View reports, manage faculties, track attendance
- 🤖 **AI Chatbot**: Ask questions about today's classes, topics, and schedules
- 📅 **Timetable Management**: Pre-loaded timetable for easy verification
- 📚 **Syllabus Tracking**: Track which topics are being taught

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: JWT Tokens
- **AI/ML**: Sentence Transformers, FAISS (Semantic Search)

## Installation

### Option 1: Docker (Recommended)

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - Home: http://localhost:8000
   - Chatbot: http://localhost:8000/chatbot
   - Faculty Login: http://localhost:8000/faculty/login
   - Admin Login: http://localhost:8000/admin/login

3. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Option 2: Manual Setup

**Requirements:** Python 3.10 or 3.11 (Python 3.13+ not yet supported)

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database with mock data:**
   ```bash
   python init_data.py
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```
   
   Or using uvicorn:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Open in browser:**
   - Home: http://localhost:8000
   - Chatbot: http://localhost:8000/chatbot
   - Faculty Login: http://localhost:8000/faculty/login
   - Admin Login: http://localhost:8000/admin/login

## Default Credentials

### Admin
- Username: `admin`
- Password: `admin123`

### Mock Faculties (14 faculties pre-loaded)
- Email: `ramesh@college.edu` (and others)
- Password: `password123` (same for all mock faculties)

## Mock Faculty List

| # | Name | Email |
|---|------|-------|
| 1 | Dr. Ramesh Kumar | ramesh@college.edu |
| 2 | Ms. Priya Sharma | priya@college.edu |
| 3 | Mr. Arun Prakash | arun@college.edu |
| 4 | Dr. Lakshmi Narayanan | lakshmi@college.edu |
| 5 | Ms. N. Backiyalakshmi | backiya@college.edu |
| 6 | Mr. Senthil Kumar | senthil@college.edu |
| 7 | Dr. Vijay Anand | vijay@college.edu |
| 8 | Ms. Deepa Krishnan | deepa@college.edu |
| 9 | Mr. Karthik Raja | karthik@college.edu |
| 10 | Dr. Meena Sundaram | meena@college.edu |
| 11 | Mr. Rajesh Babu | rajesh@college.edu |
| 12 | Ms. Anjali Devi | anjali@college.edu |
| 13 | Dr. Suresh Rajan | suresh@college.edu |
| 14 | Mr. Gopal Krishnan | gopal@college.edu |

## Departments (14)

- B.Tech AI&DS - A
- B.Tech AI&DS - B
- B.Tech AI&ML - A
- B.Tech AI&ML - B
- B.Tech CSBS
- B.Tech CSE - A
- B.Tech CSE - B
- B.Tech CYS
- B.Tech ECE - A
- B.Tech ECE - B
- B.Tech IT - A
- B.Tech IT - B
- B.Tech MECH
- B.Tech RA

## Period Timings

| Period | Time |
|--------|------|
| 1 | 08:00 AM - 08:45 AM |
| 2 | 08:45 AM - 09:30 AM |
| Break | 09:30 AM - 09:45 AM |
| 3 | 09:45 AM - 10:30 AM |
| 4 | 10:30 AM - 11:15 AM |
| 5 | 11:15 AM - 12:00 PM |
| Lunch | 12:00 PM - 01:00 PM |
| 6 | 01:00 PM - 01:45 PM |
| 7 | 01:45 PM - 02:30 PM |
| 8 | 02:30 PM - 03:15 PM |
| Break | 03:15 PM - 03:30 PM |
| 9 | 03:30 PM - 04:15 PM |

## Chatbot Examples

Try these queries:
- "Hi, what are the C programming classes today?"
- "What topic is Dr. Ramesh Kumar going to teach?"
- "What class is in the 4th period?"
- "Who teaches CSE-A?"
- "List all faculties"
- "Help"

## How to Modify Data

### Adding/Modifying Timetable
Edit the `mock_timetable` list in `init_data.py` and re-run:
```python
{"faculty_id": 1, "dept_code": "AIDS-A", "day": "Monday", "period": 3},
```

### Adding Syllabus Topics
Edit the `syllabus_topics` list in `init_data.py`.

### Adding Departments
Edit the `departments` list in `init_data.py`.

### Reset Database
Delete `c_faculties.db` and run `python init_data.py` again.

## Project Structure

```
C_faculties_chatbot/
├── main.py              # FastAPI application
├── database.py          # Database configuration
├── models.py            # SQLAlchemy models
├── auth.py              # Authentication utilities
├── chatbot.py           # Chatbot logic
├── init_data.py         # Initialize mock data
├── requirements.txt     # Python dependencies
├── c_faculties.db       # SQLite database (auto-created)
├── static/
│   ├── css/
│   │   └── style.css    # Styles
│   └── js/
│       └── app.js       # JavaScript utilities
└── templates/
    ├── index.html           # Home page
    ├── faculty_login.html   # Faculty login
    ├── faculty_register.html # Faculty registration
    ├── faculty_dashboard.html # Faculty dashboard
    ├── admin_login.html     # Admin login
    ├── admin_dashboard.html # Admin dashboard
    └── chatbot.html         # Chatbot interface
```

## License

MIT License - Feel free to use and modify!
