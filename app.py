from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import qrcode
import os
from PIL import Image
import cv2
import numpy as np
import traceback  # Add this at the top of the file with other imports
from sqlalchemy import case

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hostel_food.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure the static/qrcodes directory exists
os.makedirs('static/qrcodes', exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    registration_number = db.Column(db.String(20), unique=True, nullable=False)
    room_number = db.Column(db.String(10), nullable=False)
    
    # Add relationship to MealBooking
    bookings = db.relationship('MealBooking', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def format_date_for_input(d):
    """Format a date object for HTML date input (YYYY-MM-DD)"""
    return d.strftime('%Y-%m-%d')

def parse_date_str(date_str):
    """Parse a date string (YYYY-MM-DD) into a date object"""
    return datetime.strptime(date_str, '%Y-%m-%d').date()

def get_current_date():
    """Get current date as a date object"""
    return date.today()

class MealBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)  # breakfast, lunch, dinner
    date = db.Column(db.Date, nullable=False)
    qr_code_path = db.Column(db.String(200))
    is_attended = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def formatted_date(self):
        """Return the date formatted for display"""
        return self.date.strftime('%B %d, %Y')  # e.g., April 21, 2025
        
    @property
    def date_for_input(self):
        """Return the date formatted for HTML date input"""
        return format_date_for_input(self.date)

    def __repr__(self):
        return f'<MealBooking {self.id} for {self.user_id} on {self.date} ({self.meal_type})>'

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Rating from 1-5
    comment = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add relationship to User model
    user = db.relationship('User', backref='feedbacks', lazy=True)

    def __repr__(self):
        return f'<Feedback {self.id} from User {self.user_id}>'

class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(10), nullable=False)  # Monday, Tuesday, etc.
    meal_type = db.Column(db.String(20), nullable=False)  # breakfast, lunch, dinner
    start_time = db.Column(db.String(5), nullable=False)  # Store as string "HH:MM"
    end_time = db.Column(db.String(5), nullable=False)    # Store as string "HH:MM"
    menu = db.Column(db.Text, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def start_time_obj(self):
        """Convert stored string to time object when needed"""
        return datetime.strptime(self.start_time, '%H:%M').time()
    
    @property
    def end_time_obj(self):
        """Convert stored string to time object when needed"""
        return datetime.strptime(self.end_time, '%H:%M').time()

    def __repr__(self):
        return f'<Timetable {self.day} {self.meal_type}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/qrcodes/<path:filename>')
def serve_qr_code(filename):
    """Serve QR code images from the static/qrcodes directory"""
    try:
        return send_from_directory('static/qrcodes', filename)
    except Exception as e:
        print(f"Error serving QR code: {str(e)}")
        return "QR code not found", 404

def generate_qr_code(user_id, meal_type, date_str):
    """Generate and save QR code"""
    try:
        # Create QR code data string
        qr_data = f"{user_id}|{meal_type}|{date_str}"
        
        # Create QR code instance with better error correction
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # Highest error correction
            box_size=10,
            border=4,
        )
        
        # Add the data
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create QR code image with a white background
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Create a unique filename
        filename = f"qr_{user_id}_{meal_type}_{date_str}.png"
        
        # Make sure the qrcodes directory exists
        os.makedirs('static/qrcodes', exist_ok=True)
        
        # Save the image
        filepath = os.path.join('static', 'qrcodes', filename)
        qr_image.save(filepath)
        
        # Return the URL path to the QR code
        return f'qrcodes/{filename}'
        
    except Exception as e:
        print(f"Error generating QR code: {str(e)}")
        return None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            name = request.form.get('name')
            phone_number = request.form.get('phone_number')
            registration_number = request.form.get('registration_number')
            room_number = request.form.get('room_number')
            user_type = request.form.get('user_type')
            
            if not all([username, email, password, name, phone_number, registration_number, room_number, user_type]):
                flash('All fields are required')
                return render_template('register.html')
            
            if User.query.filter_by(username=username).first():
                flash('Username already exists')
                return render_template('register.html')
            
            if User.query.filter_by(email=email).first():
                flash('Email already exists')
                return render_template('register.html')
            
            if User.query.filter_by(registration_number=registration_number).first():
                flash('Registration number already exists')
                return render_template('register.html')
            
            user = User(
                username=username,
                email=email,
                name=name,
                phone_number=phone_number,
                registration_number=registration_number,
                room_number=room_number,
                is_admin=(user_type == 'admin')
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            error_traceback = traceback.format_exc()
            flash(f'An error occurred during registration: {str(e)}')
            print(f"Registration error: {str(e)}")
            print(f"Traceback: {error_traceback}")
            db.session.rollback()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            user_type = request.form.get('user_type')
            
            if not username or not password or not user_type:
                flash('Please provide all required fields')
                return render_template('login.html')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                # Check if user type matches
                if (user_type == 'admin' and not user.is_admin) or (user_type == 'user' and user.is_admin):
                    flash('Invalid user type selected')
                    return render_template('login.html')
                
                login_user(user)
                flash(f'Welcome back, {user.name}!')
                
                if user.is_admin:
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('user_dashboard'))
            
            flash('Invalid username or password')
        except Exception as e:
            error_traceback = traceback.format_exc()
            flash(f'An error occurred during login: {str(e)}')
            print(f"Login error: {str(e)}")
            print(f"Traceback: {error_traceback}")
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    today = get_current_date()
    today_str = format_date_for_input(today)
    
    # Get user's bookings
    bookings = MealBooking.query.filter_by(user_id=current_user.id).order_by(MealBooking.date).all()
    
    # Split bookings into upcoming and past
    upcoming_bookings = []
    past_bookings = []
    for booking in bookings:
        if booking.date >= today:
            upcoming_bookings.append(booking)
        else:
            past_bookings.append(booking)
    
    return render_template('user_dashboard.html',
                         upcoming_bookings=upcoming_bookings,
                         past_bookings=past_bookings,
                         today_date=today,
                         today_str=today_str)

@app.route('/book_meal', methods=['POST'])
@login_required
def book_meal():
    if current_user.is_admin:
        flash('Admins cannot book meals')
        return redirect(url_for('admin_dashboard'))
    
    try:
        meal_type = request.form.get('meal_type')
        date_str = request.form.get('date')
        
        if not meal_type or not date_str:
            flash('Please provide all required fields')
            return redirect(url_for('user_dashboard'))
        
        booking_date = parse_date_str(date_str)
        today = get_current_date()
        
        # Validate the date is not in the past
        if booking_date < today:
            flash('Cannot book meals for past dates')
            return redirect(url_for('user_dashboard'))
        
        # Check if booking already exists
        existing_booking = MealBooking.query.filter_by(
            user_id=current_user.id,
            meal_type=meal_type,
            date=booking_date
        ).first()
        
        if existing_booking:
            flash('You have already booked this meal')
            return redirect(url_for('user_dashboard'))
        
        # Generate QR code for the booking
        qr_path = generate_qr_code(current_user.id, meal_type, date_str)
        if not qr_path:
            flash('Error generating QR code. Please try again.')
            return redirect(url_for('user_dashboard'))
        
        # Create and save the booking with QR code path
        booking = MealBooking(
            user_id=current_user.id,
            meal_type=meal_type,
            date=booking_date,
            qr_code_path=qr_path,
            created_at=datetime.utcnow()
        )
        
        db.session.add(booking)
        db.session.commit()
        
        flash('Meal booked successfully! Click "View QR Code" to see your booking QR.')
        return redirect(url_for('user_dashboard'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error booking meal: {str(e)}")
        flash(f'Error booking meal: {str(e)}')
        return redirect(url_for('user_dashboard'))

@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    try:
        rating = int(request.form['rating'])
        comment = request.form['comment']
        
        if not 1 <= rating <= 5:
            return jsonify({'success': False, 'message': 'Rating must be between 1 and 5'}), 400
            
        if not comment:
            return jsonify({'success': False, 'message': 'Comment is required'}), 400
        
        feedback = Feedback(
            user_id=current_user.id,
            rating=rating,
            comment=comment
        )
        db.session.add(feedback)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully!'
        })
        
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid rating value'
        }), 400
    except Exception as e:
        print(f"Feedback error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while submitting feedback'
        }), 500

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('user_dashboard'))
    
    # Get all users
    users = User.query.all()
    
    # Get all bookings
    bookings = MealBooking.query.order_by(MealBooking.date.desc()).all()
    
    # Get all feedbacks
    feedbacks = Feedback.query.order_by(Feedback.date.desc()).all()
    
    # Get today's date
    today = datetime.now().date()
    
    # Get timetable data
    timetable = Timetable.query.order_by(
        case(
            (Timetable.day == 'Monday', 1),
            (Timetable.day == 'Tuesday', 2),
            (Timetable.day == 'Wednesday', 3),
            (Timetable.day == 'Thursday', 4),
            (Timetable.day == 'Friday', 5),
            (Timetable.day == 'Saturday', 6),
            (Timetable.day == 'Sunday', 7)
        ),
        Timetable.meal_type
    ).all()
    
    return render_template('admin_dashboard.html',
                         users=users,
                         bookings=bookings,
                         feedbacks=feedbacks,
                         today=today,
                         timetable=timetable)

@app.route('/scan_qr', methods=['POST'])
@login_required
def scan_qr():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        qr_data = request.json.get('qr_data')
        if not qr_data:
            return jsonify({'error': 'No QR data provided'}), 400
            
        # Parse QR data (format: user_id|meal_type|date)
        parts = qr_data.split('|')
        if len(parts) != 3:
            return jsonify({'error': 'Invalid QR code format'}), 400
            
        user_id, meal_type, date = parts
        booking = MealBooking.query.filter_by(
            user_id=user_id,
            meal_type=meal_type,
            date=datetime.strptime(date, '%Y-%m-%d').date()
        ).first()
        
        if booking:
            booking.is_attended = True
            db.session.commit()
            return jsonify({'message': 'Attendance marked successfully'})
        else:
            return jsonify({'error': 'Booking not found'}), 404
            
    except Exception as e:
        print(f"QR scanning error: {str(e)}")
        return jsonify({'error': 'Error processing QR code'}), 500

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    try:
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully')
    except Exception as e:
        flash('Error deleting user')
        print(f"Delete user error: {str(e)}")
    
    return redirect(url_for('admin_dashboard'))

@app.route('/verify_booking', methods=['POST'])
@login_required
def verify_booking():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        data = request.json
        user_id = data.get('user_id')
        meal_type = data.get('meal_type')
        date_str = data.get('date')
        
        if not all([user_id, meal_type, date_str]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
        try:
            booking_date = parse_date_str(date_str)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
        
        booking = MealBooking.query.filter_by(
            user_id=user_id,
            meal_type=meal_type,
            date=booking_date
        ).first()
        
        if booking:
            if booking.is_attended:
                return jsonify({
                    'success': False,
                    'message': f'Booking already verified for {booking.formatted_date}'
                })
            
            booking.is_attended = True
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Booking verified successfully for {booking.formatted_date}'
            })
        else:
            return jsonify({'success': False, 'message': 'Booking not found'})
            
    except Exception as e:
        print(f"Booking verification error: {str(e)}")
        return jsonify({'success': False, 'message': 'Error verifying booking'}), 500

@app.route('/unverify_booking/<int:booking_id>', methods=['POST'])
@login_required
def unverify_booking(booking_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        booking = MealBooking.query.get_or_404(booking_id)
        
        if not booking.is_attended:
            return jsonify({'success': False, 'message': 'Booking is not verified'})
        
        booking.is_attended = False
        db.session.commit()
        return jsonify({'success': True, 'message': 'Booking unverified successfully'})
            
    except Exception as e:
        print(f"Booking unverification error: {str(e)}")
        return jsonify({'success': False, 'message': 'Error unverifying booking'}), 500

@app.route('/verify_multiple_bookings', methods=['POST'])
@login_required
def verify_multiple_bookings():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        data = request.json
        booking_ids = data.get('booking_ids', [])
        
        if not booking_ids:
            return jsonify({'success': False, 'message': 'No bookings selected'})
        
        bookings = MealBooking.query.filter(MealBooking.id.in_(booking_ids)).all()
        verified_count = 0
        
        for booking in bookings:
            if not booking.is_attended:
                booking.is_attended = True
                verified_count += 1
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Successfully verified {verified_count} bookings'
        })
            
    except Exception as e:
        print(f"Bulk verification error: {str(e)}")
        return jsonify({'success': False, 'message': 'Error verifying bookings'}), 500

@app.route('/unverify_multiple_bookings', methods=['POST'])
@login_required
def unverify_multiple_bookings():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        data = request.json
        booking_ids = data.get('booking_ids', [])
        
        if not booking_ids:
            return jsonify({'success': False, 'message': 'No bookings selected'})
        
        bookings = MealBooking.query.filter(MealBooking.id.in_(booking_ids)).all()
        unverified_count = 0
        
        for booking in bookings:
            if booking.is_attended:
                booking.is_attended = False
                unverified_count += 1
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Successfully unverified {unverified_count} bookings'
        })
            
    except Exception as e:
        print(f"Bulk unverification error: {str(e)}")
        return jsonify({'success': False, 'message': 'Error unverifying bookings'}), 500

@app.route('/test_admin')
@login_required
def test_admin():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('user_dashboard'))
    return "Admin access confirmed!"

@app.route('/admin/timetable', methods=['GET', 'POST'])
@login_required
def admin_timetable():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        try:
            day = request.form.get('day')
            meal_type = request.form.get('meal_type')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            menu = request.form.get('menu')
            
            # Check if entry exists for this day and meal type
            existing = Timetable.query.filter_by(day=day, meal_type=meal_type).first()
            
            if existing:
                existing.start_time = start_time
                existing.end_time = end_time
                existing.menu = menu
            else:
                new_entry = Timetable(
                    day=day,
                    meal_type=meal_type,
                    start_time=start_time,
                    end_time=end_time,
                    menu=menu
                )
                db.session.add(new_entry)
            
            db.session.commit()
            flash('Timetable updated successfully!')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating timetable: {str(e)}')
    
    # Get all timetable entries
    timetable = Timetable.query.order_by(
        case(
            (Timetable.day == 'Monday', 1),
            (Timetable.day == 'Tuesday', 2),
            (Timetable.day == 'Wednesday', 3),
            (Timetable.day == 'Thursday', 4),
            (Timetable.day == 'Friday', 5),
            (Timetable.day == 'Saturday', 6),
            (Timetable.day == 'Sunday', 7)
        ),
        Timetable.meal_type
    ).all()
    
    return render_template('admin_timetable.html', timetable=timetable)

@app.route('/user/timetable')
@login_required
def user_timetable():
    if current_user.is_admin:
        return redirect(url_for('admin_timetable'))
    
    timetable = Timetable.query.order_by(
        case(
            (Timetable.day == 'Monday', 1),
            (Timetable.day == 'Tuesday', 2),
            (Timetable.day == 'Wednesday', 3),
            (Timetable.day == 'Thursday', 4),
            (Timetable.day == 'Friday', 5),
            (Timetable.day == 'Saturday', 6),
            (Timetable.day == 'Sunday', 7)
        ),
        Timetable.meal_type
    ).all()
    
    return render_template('user_timetable.html', timetable=timetable)

@app.route('/debug')
@login_required
def debug():
    # Check if user is admin
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Database status
    try:
        users_count = User.query.count()
        admin_count = User.query.filter_by(is_admin=True).count()
        db_status = "Connected and functioning"
    except Exception as e:
        db_status = f"Error: {str(e)}"
        users_count = 0
        admin_count = 0

    # Directory checks
    static_dir = os.path.exists('static')
    templates_dir = os.path.exists('templates')
    qrcodes_dir = os.path.exists('static/qrcodes')

    # Template files check
    required_templates = {
        'base.html': False,
        'index.html': False,
        'login.html': False,
        'register.html': False,
        'user_dashboard.html': False,
        'admin_dashboard.html': False,
        'debug.html': False
    }
    
    for template in required_templates:
        required_templates[template] = os.path.exists(f'templates/{template}')

    return render_template('debug.html',
                         db_status=db_status,
                         users_count=users_count,
                         admin_count=admin_count,
                         static_dir=static_dir,
                         templates_dir=templates_dir,
                         qrcodes_dir=qrcodes_dir,
                         template_files=required_templates)

# Create admin user if not exists
def create_admin_user():
    """Create a default admin user if none exists"""
    try:
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True,
                name='Admin User',
                phone_number='1234567890',
                registration_number='ADMIN001',
                room_number='ADMIN'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created")
        return admin
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        db.session.rollback()
        return None

@app.route('/qr_scanner')
@login_required
def qr_scanner():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    return render_template('qr_scanner.html')

@app.route('/verify_qr', methods=['POST'])
@login_required
def verify_qr():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.get_json()
    qr_code = data.get('qr_code')
    
    if not qr_code:
        return jsonify({'success': False, 'message': 'No QR code provided'})
    
    try:
        # Parse QR code (format: <user_id>|<meal_type>|<date>)
        parts = qr_code.split('|')
        if len(parts) != 3:
            return jsonify({'success': False, 'message': 'Invalid QR code format. Expected format: user_id|meal_type|date'})
        
        user_id, meal_type, date = parts
        user_id = int(user_id)
        
        # Find the booking
        booking = MealBooking.query.filter_by(
            user_id=user_id,
            meal_type=meal_type,
            date=datetime.strptime(date, '%Y-%m-%d').date()
        ).first()
        
        if not booking:
            return jsonify({'success': False, 'message': 'Booking not found'})
        
        # Update booking status
        if not booking.attended:
            booking.attended = True
            booking.verified_at = datetime.now()
            db.session.commit()
            return jsonify({
                'success': True, 
                'message': f'Verified: {meal_type.capitalize()} for user {user_id} on {date}'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'This QR code has already been verified'
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    # Create required directories
    os.makedirs('static/qrcodes', exist_ok=True)
    
    # Initialize database
    with app.app_context():
        try:
            db.drop_all()  # Drop all tables
            db.create_all()  # Create all tables with new schema
            create_admin_user()  # Create admin user if not exists
            print("Database initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
    
    # Run the app on localhost
    app.run(host='localhost', port=5000, debug=True)