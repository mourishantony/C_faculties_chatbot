"""
Migration script to add extra class columns to the daily_entries table.
Run this once to add the new columns.
"""
import sqlite3

def migrate():
    conn = sqlite3.connect('c_faculties.db')
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(daily_entries)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Add new columns if they don't exist
    if 'is_extra_class' not in columns:
        cursor.execute("ALTER TABLE daily_entries ADD COLUMN is_extra_class BOOLEAN DEFAULT 0")
        print("Added column: is_extra_class")
    else:
        print("Column is_extra_class already exists")
    
    if 'extra_class_subject_code' not in columns:
        cursor.execute("ALTER TABLE daily_entries ADD COLUMN extra_class_subject_code VARCHAR(20)")
        print("Added column: extra_class_subject_code")
    else:
        print("Column extra_class_subject_code already exists")
    
    if 'extra_class_subject_name' not in columns:
        cursor.execute("ALTER TABLE daily_entries ADD COLUMN extra_class_subject_name VARCHAR(50)")
        print("Added column: extra_class_subject_name")
    else:
        print("Column extra_class_subject_name already exists")
    
    conn.commit()
    conn.close()
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    migrate()
