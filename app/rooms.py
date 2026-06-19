from datetime import datetime
# pyrefly: ignore [missing-import]
from flask import Blueprint, render_template, redirect, url_for, flash, request
# pyrefly: ignore [missing-import]
from flask_login import login_required, current_user
from app.models import db, Room, Booking
from app.utils import admin_required, log_action, send_notification

rooms_bp = Blueprint('rooms', __name__)

@rooms_bp.route('/')
@login_required
def list_rooms():
    # Filter criteria
    capacity = request.args.get('capacity', type=int)
    location = request.args.get('location')
    equipment = request.args.get('equipment')
    
    query = Room.query
    
    # Regular users only see active rooms
    if current_user.role not in ['root', 'admin']:
        query = query.filter_by(is_active=True)
        
    if capacity:
        query = query.filter(Room.capacity >= capacity)
    if location:
        query = query.filter(Room.location.ilike(f"%{location}%"))
    if equipment:
        query = query.filter(Room.equipment.ilike(f"%{equipment}%"))
        
    rooms = query.order_by(Room.name.asc()).all()
    
    return render_template(
        'rooms/list.html',
        rooms=rooms,
        capacity=capacity,
        location=location,
        equipment=equipment
    )

@rooms_bp.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required('can_manage_rooms')
def create_room():
    if request.method == 'POST':
        name = request.form.get('name')
        capacity = request.form.get('capacity', type=int)
        location = request.form.get('location')
        equipment = request.form.get('equipment')
        description = request.form.get('description')
        status = request.form.get('status', 'active')
        is_active = True if request.form.get('is_active') else False
        
        if not name or not capacity or not location:
            flash('Пожалуйста, укажите название переговорной, вместимость и этаж/расположение.', 'danger')
            return render_template('rooms/form.html', action="create")
            
        existing = Room.query.filter_by(name=name).first()
        if existing:
            flash('Переговорная комната с таким названием уже существует.', 'danger')
            return render_template('rooms/form.html', action="create")
            
        room = Room(
            name=name,
            capacity=capacity,
            location=location,
            equipment=equipment,
            description=description,
            status=status,
            is_active=is_active
        )
        try:
            db.session.add(room)
            db.session.commit()
            
            log_action(current_user.id, 'room', room.id, 'create_room', f"Created meeting room: {name}")
            flash('Переговорная комната успешно добавлена.', 'success')
            return redirect(url_for('rooms.list_rooms'))
        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка базы данных при сохранении переговорной.', 'danger')
            
    return render_template('rooms/form.html', action="create")

@rooms_bp.route('/<int:room_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required('can_manage_rooms')
def edit_room(room_id):
    room = Room.query.get_or_404(room_id)
    if request.method == 'POST':
        name = request.form.get('name')
        capacity = request.form.get('capacity', type=int)
        location = request.form.get('location')
        equipment = request.form.get('equipment')
        description = request.form.get('description')
        status = request.form.get('status')
        is_active = True if request.form.get('is_active') else False
        
        if not name or not capacity or not location:
            flash('Пожалуйста, заполните название, вместимость и расположение.', 'danger')
            return render_template('rooms/form.html', room=room, action="edit")
            
        existing = Room.query.filter(Room.name == name, Room.id != room_id).first()
        if existing:
            flash('Другая переговорная комната уже использует это название.', 'danger')
            return render_template('rooms/form.html', room=room, action="edit")
            
        old_status = room.status
        old_active = room.is_active
        
        room.name = name
        room.capacity = capacity
        room.location = location
        room.equipment = equipment
        room.description = description
        room.status = status
        room.is_active = is_active
        
        try:
            db.session.commit()
            
            details = f"Updated room attributes. Active: {old_active}->{is_active}, Status: {old_status}->{status}"
            log_action(current_user.id, 'room', room.id, 'edit_room', details)
            flash('Параметры переговорной успешно изменены.', 'success')
            return redirect(url_for('rooms.list_rooms'))
        except Exception as e:
            db.session.rollback()
            flash('Не удалось сохранить изменения переговорной в базе данных.', 'danger')
            
    return render_template('rooms/form.html', room=room, action="edit")

@rooms_bp.route('/<int:room_id>/deactivate', methods=['POST'])
@login_required
@admin_required('can_manage_rooms')
def deactivate_room(room_id):
    room = Room.query.get_or_404(room_id)
    name = room.name
    try:
        room.is_active = False
        room.status = 'unavailable'
        
        now = datetime.utcnow()
        future_bookings = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.status.in_(['active', 'confirmed']),
            Booking.start_at >= now
        ).all()
        
        for b in future_bookings:
            send_notification(
                b.user_id,
                f"Внимание: комната '{name}', которую вы забронировали на {b.start_at.strftime('%d.%m.%Y %H:%M')}, была деактивирована администратором. Пожалуйста, измените бронирование.",
                booking_id=b.id
            )
            
        db.session.commit()
        log_action(current_user.id, 'room', room_id, 'deactivate_room', f"Deactivated meeting room: {name}")
        flash(f'Комната {name} переведена в статус "недоступна". Затронуто будущих бронирований: {len(future_bookings)}.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash('Произошла ошибка при деактивации комнаты.', 'danger')
    return redirect(url_for('rooms.list_rooms'))
