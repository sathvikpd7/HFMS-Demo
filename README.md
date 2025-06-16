# Hostel Food Management System

A web-based food management system for hostels that allows users to book meals, provide feedback, and track attendance using QR codes.

## Features

- User registration and authentication
- Meal booking system (breakfast, lunch, dinner)
- QR code generation for meal bookings
- Feedback system for food quality
- Admin dashboard for managing users and viewing statistics
- QR code scanner for attendance tracking

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd hostel-food-management
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

### For Users
1. Register a new account or login if you already have one
2. Book meals for different time slots
3. Download the generated QR code for your booking
4. Provide feedback about the food quality

### For Administrators
1. Login with admin credentials
2. Access the admin dashboard
3. View user registrations, bookings, and feedback
4. Use the QR code scanner to track attendance

## Security Notes

- The application uses Flask-Login for authentication
- Passwords are hashed using Werkzeug's security utilities
- Admin access is restricted to authorized users only

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 