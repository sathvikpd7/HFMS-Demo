import os
import sys
import subprocess
import traceback
from flask import Flask
from app import app, db, User, create_admin_user

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'flask',
        'flask-sqlalchemy',
        'flask-login',
        'flask-wtf',
        'werkzeug',
        'qrcode',
        'pillow',
        'python-dotenv',
        'email-validator',
        'opencv-python'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing packages:", ", ".join(missing_packages))
        print("Installing missing packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("Successfully installed missing packages")
        except subprocess.CalledProcessError as e:
            print(f"Error installing packages: {str(e)}")
            sys.exit(1)

def setup_directories():
    """Create necessary directories if they don't exist"""
    directories = ['static', 'templates', 'static/qrcodes', 'instance']
    for directory in directories:
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Created directory: {directory}")
        except Exception as e:
            print(f"Error creating directory {directory}: {str(e)}")
            sys.exit(1)

def initialize_database():
    """Initialize the database and create admin user"""
    try:
        # Ensure instance directory exists and has proper permissions
        if not os.path.exists('instance'):
            os.makedirs('instance')
            print("Created instance directory")
        
        # Run setup_database.py to create the database
        import setup_database
        setup_database.setup_database()
        
        # Now initialize the database with SQLAlchemy
        with app.app_context():
            db.create_all()
            create_admin_user()
            print("Database initialized and admin user created.")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        traceback.print_exc()  # Print the full traceback for debugging
        sys.exit(1)

if __name__ == '__main__':
    try:
        print("Setting up the application...")
        
        # Check and install dependencies
        print("Checking dependencies...")
        check_dependencies()
        
        # Setup directories
        print("Setting up directories...")
        setup_directories()
        
        # Initialize database
        print("Initializing database...")
        initialize_database()
        
        # Run the application
        print("\nStarting the application...")
        print("Access the application at: http://localhost:5000")
        print("Admin credentials: username='admin', password='admin123'")
        print("Press CTRL+C to stop the server")
        
        # Run on localhost for secure context
        app.run(
            host='localhost',
            port=5000,
            debug=True,
            use_reloader=True
        )
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        sys.exit(1)