"""
Migration script to add absent_reason and swap_reason columns to daily_entries table.
Run this once to update the database schema.
"""

import sqlite3

def migrate():
    conn = sqlite3.connect('c_faculties.db')
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(daily_entries)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Add absent_reason column if it doesn't exist
    if 'absent_reason' not in columns:
        print("Adding absent_reason column...")
        cursor.execute("ALTER TABLE daily_entries ADD COLUMN absent_reason TEXT")
        print("✓ absent_reason column added successfully")
    else:
        print("✓ absent_reason column already exists")
    
    # Add swap_reason column if it doesn't exist
    if 'swap_reason' not in columns:
        print("Adding swap_reason column...")
        cursor.execute("ALTER TABLE daily_entries ADD COLUMN swap_reason TEXT")
        print("✓ swap_reason column added successfully")
    else:
        print("✓ swap_reason column already exists")
    
    conn.commit()
    conn.close()
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    migrate()
