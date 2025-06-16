import sqlite3
from datetime import datetime

def test_timetable():
    conn = sqlite3.connect('hostel_food.db')
    cursor = conn.cursor()
    
    # Test insert
    try:
        cursor.execute('''
            INSERT INTO timetable (day, meal_type, start_time, end_time, menu)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Monday', 'breakfast', '07:30', '09:30', 'Idli, Sambar, Chutney'))
        conn.commit()
        print("Successfully inserted test data")
        
        # Test query
        cursor.execute('SELECT * FROM timetable')
        row = cursor.fetchone()
        print("\nQueried data:")
        print(f"Day: {row[1]}")
        print(f"Meal: {row[2]}")
        print(f"Time: {row[3]} - {row[4]}")
        print(f"Menu: {row[5]}")
        print(f"Last updated: {row[6]}")
        
    except sqlite3.Error as e:
        print(f"Error: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    test_timetable()
