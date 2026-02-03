from database import SessionLocal
from models import Faculty
from auth import get_password_hash

db = SessionLocal()

# Update all faculty passwords
new_password = "Kgisl@12345"
hashed_password = get_password_hash(new_password)

faculties = db.query(Faculty).all()

for faculty in faculties:
    faculty.password = hashed_password
    print(f"✓ Updated password for: {faculty.name} ({faculty.email})")

db.commit()
db.close()

print(f"\n All {len(faculties)} faculty passwords updated to: {new_password}")
