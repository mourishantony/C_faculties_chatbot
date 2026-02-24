"""
Migration script to add swap_type column to daily_entries table
and create the swap_entries table.

Run this once after updating models.py:
    python migrate_swap.py
"""
from sqlalchemy import inspect, text
from database import engine

def _column_exists(table_name, column_name):
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate():
    # 1. Add swap_type column to daily_entries if not exists
    if not _column_exists("daily_entries", "swap_type"):
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE daily_entries ADD COLUMN swap_type VARCHAR(20)"))
            conn.commit()
        print("Added 'swap_type' column to daily_entries table")
    else:
        print("'swap_type' column already exists in daily_entries")
    
    # 2. Create swap_entries table if not exists
    inspector = inspect(engine)
    if "swap_entries" not in inspector.get_table_names():
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE swap_entries (
                    id SERIAL PRIMARY KEY,
                    faculty_id INTEGER NOT NULL,
                    swap_type VARCHAR(20) NOT NULL,
                    original_date DATE,
                    original_period INTEGER,
                    new_date DATE NOT NULL,
                    new_period INTEGER NOT NULL,
                    department_id INTEGER NOT NULL,
                    class_type VARCHAR(20) DEFAULT 'theory',
                    subject_code VARCHAR(20) DEFAULT '24UCS271',
                    subject_name VARCHAR(50) DEFAULT 'C Programming',
                    swapped_with_faculty VARCHAR(100),
                    swapped_with_department VARCHAR(100),
                    reason TEXT,
                    daily_entry_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (faculty_id) REFERENCES faculties(id),
                    FOREIGN KEY (department_id) REFERENCES departments(id),
                    FOREIGN KEY (daily_entry_id) REFERENCES daily_entries(id)
                )
            """))
            conn.commit()
        print("Created 'swap_entries' table")
    else:
        print("'swap_entries' table already exists")
    
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    migrate()
