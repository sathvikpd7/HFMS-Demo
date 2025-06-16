from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import case
from datetime import datetime
import re

def init_timetable_routes(app, db, Timetable):
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
                
                # Basic validation
                if not all([day, meal_type, start_time, end_time, menu]):
                    raise ValueError("All fields are required")

                # Validate time format
                time_format = r'^([01]\d|2[0-3]):([0-5]\d)$'
                if not (re.match(time_format, start_time) and re.match(time_format, end_time)):
                    raise ValueError("Times must be in HH:MM format (24-hour)")

                # Compare times
                start_hour, start_minute = map(int, start_time.split(':'))
                end_hour, end_minute = map(int, end_time.split(':'))
                
                if start_hour > end_hour or (start_hour == end_hour and start_minute >= end_minute):
                    raise ValueError("End time must be later than start time")

                # Check if entry exists for this day and meal type
                existing = Timetable.query.filter_by(day=day, meal_type=meal_type).first()
                
                if existing:
                    existing.start_time = start_time
                    existing.end_time = end_time
                    existing.menu = menu
                    db.session.add(existing)
                else:
                    new_entry = Timetable(
                        day=day,
                        meal_type=meal_type,
                        start_time=start_time,
                        end_time=end_time,
                        menu=menu
                    )
                    db.session.add(new_entry)
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