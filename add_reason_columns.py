"""
Migration script to add absent_reason and swap_reason columns to daily_entries table.
Run this once to update the database schema.
"""

from sqlalchemy import inspect, text
from database import engine

def _column_exists(table_name, column_name):
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate():
    # Add absent_reason column if it doesn't exist
    if not _column_exists("daily_entries", "absent_reason"):
        print("Adding absent_reason column...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE daily_entries ADD COLUMN absent_reason TEXT"))
            conn.commit()
        print("✓ absent_reason column added successfully")
    else:
        print("✓ absent_reason column already exists")
    
    # Add swap_reason column if it doesn't exist
    if not _column_exists("daily_entries", "swap_reason"):
        print("Adding swap_reason column...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE daily_entries ADD COLUMN swap_reason TEXT"))
            conn.commit()
        print("✓ swap_reason column added successfully")
    else:
        print("✓ swap_reason column already exists")
    
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    migrate()
