"""
Script to add room_number column to existing departments table
and populate room numbers for all departments.
"""
from sqlalchemy import text
from database import engine, SessionLocal
from models import Department

# Room number mapping
ROOM_NUMBERS = {
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

def update_room_numbers():
    """Add room_number column if not exists and update all departments"""
    db = SessionLocal()
    
    try:
        # Check if room_number column exists using SQLAlchemy inspect (works for both SQLite and PostgreSQL)
        from sqlalchemy import inspect as sa_inspect
        inspector = sa_inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("departments")]
        
        if 'room_number' not in columns:
            print("Adding room_number column to departments table...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE departments ADD COLUMN room_number VARCHAR(20)"))
                conn.commit()
            print("✓ Column added successfully")
        else:
            print("✓ room_number column already exists")
        
        # Update room numbers for all departments
        print("\nUpdating room numbers...")
        departments = db.query(Department).all()
        
        for dept in departments:
            if dept.code in ROOM_NUMBERS:
                dept.room_number = ROOM_NUMBERS[dept.code]
                print(f"  ✓ {dept.code}: Room {ROOM_NUMBERS[dept.code]}")
            else:
                print(f"  ⚠ {dept.code}: No room number mapped")
        
        db.commit()
        print("\n✓ All room numbers updated successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_room_numbers()
