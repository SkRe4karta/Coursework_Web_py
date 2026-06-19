from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import db, Booking, Room, User
from app.utils import admin_required

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/')
@login_required
@admin_required('can_view_analytics')
def dashboard():
    total_bookings = Booking.query.count()
    active_bookings = Booking.query.filter_by(status='active').count()
    
    # Busiest room calculation
    busiest_query = db.session.query(
        Room.name, func.count(Booking.id).label('booking_count')
    ).join(Booking).filter(Booking.status.in_(['active', 'completed'])).group_by(Room.name).order_by(db.desc('booking_count')).first()
    
    busiest_room = busiest_query[0] if busiest_query else "Нет данных"
    busiest_count = busiest_query[1] if busiest_query else 0
    
    return render_template(
        'admin/analytics.html',
        total_bookings=total_bookings,
        active_bookings=active_bookings,
        busiest_room=busiest_room,
        busiest_count=busiest_count
    )

@analytics_bp.route('/data')
@login_required
@admin_required('can_view_analytics')
def get_data():
    # 1. Occupancy totals per room
    room_data = db.session.query(
        Room.name, func.count(Booking.id).label('count')
    ).outerjoin(Booking, (Booking.room_id == Room.id) & (Booking.status.in_(['active', 'completed']))).group_by(Room.name).order_by(Room.name.asc()).all()
    
    rooms_labels = [r[0] for r in room_data]
    rooms_values = [r[1] for r in room_data]
    
    # 2. Bookings distributed by employees (Top 10)
    employee_data = db.session.query(
        User.full_name, func.count(Booking.id).label('count')
    ).join(Booking).filter(Booking.status.in_(['active', 'completed'])).group_by(User.full_name).order_by(db.desc('count')).limit(10).all()
    
    employees_labels = [e[0] for e in employee_data]
    employees_values = [e[1] for e in employee_data]
    
    # 3. Bookings timeline over the last 7 calendar days
    today = datetime.utcnow().date()
    days_labels = []
    days_values = []
    
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        
        count = Booking.query.filter(
            Booking.status.in_(['active', 'completed']),
            Booking.start_at >= day_start,
            Booking.start_at <= day_end
        ).count()
        
        days_labels.append(day.strftime('%d.%m'))
        days_values.append(count)
        
    return jsonify({
        'rooms': {
            'labels': rooms_labels,
            'values': rooms_values
        },
        'employees': {
            'labels': employees_labels,
            'values': employees_values
        },
        'days': {
            'labels': days_labels,
            'values': days_values
        }
    })
