import sqlite3

def verify_schema():
    conn = sqlite3.connect('hostel_food.db')
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("PRAGMA table_info(timetable)")
    columns = cursor.fetchall()
    
    print("\nTimetable table schema:")
    for col in columns:
        print(f"Column: {col[1]}, Type: {col[2]}, NotNull: {col[3]}, Default: {col[4]}")
    
    conn.close()

if __name__ == '__main__':
    verify_schema()
