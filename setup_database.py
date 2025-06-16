import sqlite3
import os
from werkzeug.security import generate_password_hash

def setup_database():
    # Remove existing database if it exists
    if os.path.exists('hostel_food.db'):
        os.remove('hostel_food.db')
        print("Removed existing database: hostel_food.db")

    # Create new database
    conn = sqlite3.connect('hostel_food.db')
    cursor = conn.cursor()

    # Create tables
    cursor.executescript('''
        CREATE TABLE user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT 0,
            name VARCHAR(100) NOT NULL,
            phone_number VARCHAR(15) NOT NULL,
            registration_number VARCHAR(20) UNIQUE NOT NULL,
            room_number VARCHAR(10) NOT NULL
        );

        CREATE TABLE meal_booking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            meal_type VARCHAR(20) NOT NULL,
            date DATE NOT NULL,
            qr_code_path VARCHAR(200),
            is_attended BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id)
        );

        CREATE TABLE feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            date DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user (id)
        );

        CREATE TABLE timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day VARCHAR(10) NOT NULL,
            meal_type VARCHAR(20) NOT NULL,
            start_time VARCHAR(5) NOT NULL,
            end_time VARCHAR(5) NOT NULL,
            menu TEXT NOT NULL,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # Create default admin user
    admin_password = generate_password_hash('admin123')
    cursor.execute('''
        INSERT INTO user (username, email, password_hash, is_admin, name, phone_number, registration_number, room_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('admin', 'admin@example.com', admin_password, 1, 'Admin User', '1234567890', 'ADMIN001', 'ADMIN'))

    conn.commit()
    conn.close()

    print("\nSuccessfully created database: hostel_food.db")
    print("\nCreated tables:")
    print("- user")
    print("- meal_booking")
    print("- feedback")
    print("- timetable")
    print("\nDefault admin user created:")
    print("Username: admin")
    print("Password: admin123")

if __name__ == '__main__':
    setup_database()