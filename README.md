# C Programming Faculty Management System

A comprehensive web application for managing C Programming faculty schedules, tracking daily class entries, and providing an FAQ-based chatbot for quick information.

## 🌟 Features

### 👨‍🏫 Faculty Portal
- Secure login for 14 faculty members
- Fill daily class schedules (Theory, Lab, Mini Project)
- Track syllabus progress
- View personal timetable

### 📊 Admin Dashboard (Public View)
- View all faculty information
- See today's schedule at a glance
- AI chatbot for quick queries
- No login required (secret URL access)

### 👑 Super Admin Dashboard
- Full CRUD operations for all database tables
- Manage Faculties, Timetable, Syllabus, Lab Programs
- Manage FAQs for chatbot
- View system statistics

### 🤖 FAQ-Based Chatbot
- Answer questions using FAQs stored in database
- Query today's schedule
- Get faculty information
- Access lab programs and session materials

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: JWT Tokens with bcrypt password hashing
- **Chatbot**: FAQ-based keyword matching

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd C_faculties_chatbot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python init_data.py
   ```

5. **Run the application**
   ```bash
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

### Docker (Alternative)

```bash
docker-compose up --build
```

## 🔐 Access URLs

> ⚠️ **Important**: All URLs are secret. Do not share with unauthorized users.

| Page | URL | Access |
|------|-----|--------|
| Admin Dashboard | `/cprog_admin_view_x7k9` | Public (no login) |
| Login Page | `/cprog_portal_m2p8` | Faculty & Super Admin |
| Faculty Dashboard | `/cprog_faculty_dash_q4w1` | After login |
| Super Admin Dashboard | `/cprog_super_dash_z9y3` | After login |

**Common URLs return 404:** `/`, `/login`, `/admin`, `/faculty/dashboard`

## 🔑 Login Credentials

### Super Admin
- **Email**: `super_admin@gmail.com`
- **Password**: `superadmin123`

### Faculty (14 members)
- **Password for all**: `password123`
- **Emails**: Use faculty email from database

| # | Name | Department | Email |
|---|------|------------|-------|
| 1 | Sathish R | AIDS-A | r.sathish@kgkite.ac.in |
| 2 | Sikkandhar Batcha J | AIDS-B | sikkandharbatcha.j@kgkite.ac.in |
| 3 | Thilak S | AIML-A | thilak.s@kgkite.ac.in |
| 4 | Sivakumar T | AIML-B | sivakumar.t@kgkite.ac.in |
| 5 | Logeshwari S | CSBS | logeshwari.s@kgkite.ac.in |
| 6 | Priyanka G | CSE-A | priyanka.g@kgkite.ac.in |
| 7 | Swetha M | CSE-B | swetha.m@kgkite.ac.in |
| 8 | Jayaraj | CYS | jayaraj@kgkite.ac.in |
| 9 | Sivakami | ECE-A | sivakami@kgkite.ac.in |
| 10 | Sathiyanathan P | ECE-B | sathiyanathan.p@kgkite.ac.in |
| 11 | Priya R | IT-A | priya.r@kgkite.ac.in |
| 12 | Jasmine Shamila G | IT-B | jasmineshamila.g@kgkite.ac.in |
| 13 | Pradeep G | MECH | pradeep.g@kgkite.ac.in |
| 14 | Madhan S | RA | madhan.s@kgkite.ac.in |

## 📁 Project Structure

```
C_faculties_chatbot/
├── main.py              # FastAPI application & routes
├── models.py            # SQLAlchemy database models
├── database.py          # Database connection
├── auth.py              # Authentication helpers
├── chatbot.py           # FAQ-based chatbot logic
├── init_data.py         # Database initialization
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose config
├── static/
│   ├── css/style.css    # Stylesheets
│   ├── js/app.js        # JavaScript utilities
│   └── images/          # Faculty images
└── templates/
    ├── login.html                  # Login page
    ├── faculty_dashboard.html      # Faculty portal
    ├── admin_dashboard.html        # Admin view (public)
    └── super_admin_dashboard.html  # Super admin CRUD
```

## 🗄️ Database Schema

| Table | Description |
|-------|-------------|
| `faculties` | Faculty member information |
| `departments` | 14 B.Tech departments |
| `timetable_entries` | Weekly class schedule |
| `daily_entries` | Daily class records |
| `syllabus` | Session-wise syllabus |
| `lab_programs` | Weekly lab programs |
| `period_timings` | Period time slots |
| `super_admins` | Super admin accounts |
| `faqs` | Chatbot FAQ data |
| `admins` | Legacy admin table |

## 🤖 Chatbot Commands

The chatbot responds to natural language queries:

**Schedule:**
- "Who has class today?"
- "Today's schedule"
- "Show classes"

**Faculty:**
- "List all faculty"
- "Who teaches AIDS-A?"
- "Sathish schedule"

**Lab Programs:**
- "Week 3 lab"
- "Lab program week 5"

**Sessions:**
- "Session 3 PPT"
- "Deck 5"

**General:**
- "help" - Show all commands
- Any FAQ question from database

## 🔧 API Endpoints

### Public APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | Unified login |
| GET | `/api/departments` | List departments |
| GET | `/api/syllabus` | Get syllabus |
| GET | `/api/lab-programs` | Get lab programs |
| GET | `/api/faqs` | Get active FAQs |
| POST | `/api/chatbot` | Chatbot query |
| POST | `/api/admin/chatbot` | Admin chatbot |

### Faculty APIs (Auth Required)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/faculty/me` | Get current faculty |
| GET | `/api/faculty/today-schedule` | Today's schedule |
| POST | `/api/faculty/daily-entry` | Submit daily entry |

### Super Admin APIs (Auth Required)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/super-admin/faculties` | Manage faculties |
| GET/POST | `/api/super-admin/timetable` | Manage timetable |
| GET/POST | `/api/super-admin/syllabus` | Manage syllabus |
| GET/POST | `/api/super-admin/lab-programs` | Manage lab programs |
| GET/POST | `/api/super-admin/faqs` | Manage FAQs |
| GET/POST | `/api/super-admin/departments` | Manage departments |
| GET | `/api/super-admin/stats` | System statistics |

## 📝 License

This project is for educational purposes.

## 👨‍💻 Author

C Programming Faculty Management System - KG College of Arts and Science

---

**Note**: Remember to keep the secret URLs confidential and share only with authorized personnel.
