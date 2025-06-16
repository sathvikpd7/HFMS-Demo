from app import db
import sqlite3
from datetime import datetime

def add_created_at_column():
    try:
        # Connect to the database
        conn = sqlite3.connect('hostel_food.db')
        cursor = conn.cursor()
        
        # Add the created_at column with a default value
        cursor.execute('''
            ALTER TABLE meal_booking 
            ADD COLUMN created_at TIMESTAMP 
            DEFAULT CURRENT_TIMESTAMP
        ''')
        
        # Commit the changes
        conn.commit()
        print("Successfully added created_at column to meal_booking table")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column created_at already exists")
        else:
            print(f"Error adding column: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_created_at_column()
