import sqlite3
from datetime import datetime, timedelta
import random

def test_database():
    # Connect to database
    conn = sqlite3.connect('hostel_food.db')
    cursor = conn.cursor()
    
    try:
        # 1. Add test users
        test_users = [
            ('student1', 'student1@example.com', 'password123', False),
            ('student2', 'student2@example.com', 'password123', False),
            ('student3', 'student3@example.com', 'password123', False)
        ]
        
        cursor.executemany('''
            INSERT INTO user (username, email, password_hash, is_admin)
            VALUES (?, ?, ?, ?)
        ''', test_users)
        
        # 2. Add test meal bookings
        # Get user IDs
        cursor.execute('SELECT id FROM user WHERE username != "admin"')
        user_ids = [row[0] for row in cursor.fetchall()]
        
        # Generate bookings for the next 7 days
        meal_types = ['breakfast', 'lunch', 'dinner']
        bookings = []
        
        for user_id in user_ids:
            for i in range(7):
                date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
                for meal_type in meal_types:
                    is_attended = random.choice([True, False])
                    bookings.append((user_id, meal_type, date, f'/static/qrcodes/qr_{user_id}_{meal_type}_{date}.png', is_attended))
        
        cursor.executemany('''
            INSERT INTO meal_booking (user_id, meal_type, date, qr_code_path, is_attended)
            VALUES (?, ?, ?, ?, ?)
        ''', bookings)
        
        # 3. Add test feedback
        feedback_data = []
        for user_id in user_ids:
            for _ in range(3):  # 3 feedback entries per user
                rating = random.randint(1, 5)
                comment = f"Test feedback comment with rating {rating}"
                feedback_data.append((user_id, rating, comment))
        
        cursor.executemany('''
            INSERT INTO feedback (user_id, rating, comment)
            VALUES (?, ?, ?)
        ''', feedback_data)
        
        # Commit changes
        conn.commit()
        
        # 4. View data
        print("\n=== Users ===")
        cursor.execute('''
            SELECT id, username, email, is_admin 
            FROM user
        ''')
        for row in cursor.fetchall():
            print(f"ID: {row[0]}, Username: {row[1]}, Email: {row[2]}, Admin: {row[3]}")
        
        print("\n=== Today's Meal Bookings ===")
        cursor.execute('''
            SELECT mb.id, u.username, mb.meal_type, mb.date, mb.is_attended
            FROM meal_booking mb
            JOIN user u ON mb.user_id = u.id
            WHERE mb.date = DATE('now')
        ''')
        for row in cursor.fetchall():
            print(f"ID: {row[0]}, User: {row[1]}, Meal: {row[2]}, Date: {row[3]}, Attended: {row[4]}")
        
        print("\n=== Recent Feedback ===")
        cursor.execute('''
            SELECT f.id, u.username, f.rating, f.comment, f.date
            FROM feedback f
            JOIN user u ON f.user_id = u.id
            ORDER BY f.date DESC
            LIMIT 5
        ''')
        for row in cursor.fetchall():
            print(f"ID: {row[0]}, User: {row[1]}, Rating: {row[2]}, Comment: {row[3]}, Date: {row[4]}")
        
        print("\n=== User Statistics ===")
        cursor.execute('SELECT * FROM user_statistics')
        for row in cursor.fetchall():
            print(f"User: {row[1]}, Total Bookings: {row[2]}, Attended: {row[3]}, Feedback Count: {row[4]}, Avg Rating: {row[5]}")
        
        print("\n=== Daily Meal Statistics ===")
        cursor.execute('''
            SELECT * FROM daily_meal_statistics 
            WHERE date = DATE('now')
        ''')
        for row in cursor.fetchall():
            print(f"Date: {row[0]}, Meal: {row[1]}, Total: {row[2]}, Attended: {row[3]}, Attendance %: {row[4]}")
        
        print("\n=== Feedback Statistics ===")
        cursor.execute('SELECT * FROM feedback_statistics')
        for row in cursor.fetchall():
            print(f"Rating: {row[0]}, Count: {row[1]}, Percentage: {row[2]}%")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    test_database() 