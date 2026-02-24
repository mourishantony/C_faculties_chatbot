"""
Migration script to add extra class columns to the daily_entries table.
Run this once to add the new columns.
"""
from sqlalchemy import inspect, text
from database import engine

def _column_exists(table_name, column_name):
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate():
    # Add new columns if they don't exist
    if not _column_exists("daily_entries", "is_extra_class"):
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE daily_entries ADD COLUMN is_extra_class BOOLEAN DEFAULT FALSE"))
            conn.commit()
        print("Added column: is_extra_class")
    else:
        print("Column is_extra_class already exists")
    
    if not _column_exists("daily_entries", "extra_class_subject_code"):
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE daily_entries ADD COLUMN extra_class_subject_code VARCHAR(20)"))
            conn.commit()
        print("Added column: extra_class_subject_code")
    else:
        print("Column extra_class_subject_code already exists")
    
    if not _column_exists("daily_entries", "extra_class_subject_name"):
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE daily_entries ADD COLUMN extra_class_subject_name VARCHAR(50)"))
            conn.commit()
        print("Added column: extra_class_subject_name")
    else:
        print("Column extra_class_subject_name already exists")
    
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    migrate()
