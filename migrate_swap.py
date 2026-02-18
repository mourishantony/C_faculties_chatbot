"""
Migration script to add swap_type column to daily_entries table
and create the swap_entries table.

Run this once after updating models.py:
    python migrate_swap.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "c_faculties.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Add swap_type column to daily_entries if not exists
    try:
        cursor.execute("ALTER TABLE daily_entries ADD COLUMN swap_type VARCHAR(20)")
        print("Added 'swap_type' column to daily_entries table")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("'swap_type' column already exists in daily_entries")
        else:
            raise
    
    # 2. Create swap_entries table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS swap_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (faculty_id) REFERENCES faculties(id),
            FOREIGN KEY (department_id) REFERENCES departments(id),
            FOREIGN KEY (daily_entry_id) REFERENCES daily_entries(id)
        )
    """)
    print("Created 'swap_entries' table (if not existed)")
    
    conn.commit()
    conn.close()
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    migrate()
