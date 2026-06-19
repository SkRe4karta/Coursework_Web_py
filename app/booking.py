import os
import uuid
from datetime import datetime, timedelta
# pyrefly: ignore [missing-import]
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
# pyrefly: ignore [missing-import]
from flask_login import login_required, current_user
# pyrefly: ignore [missing-import]
from werkzeug.utils import secure_filename
from app.models import db, Booking, Room, BookingParticipant, Attachment, User
from app.utils import log_action, send_notification, allowed_file
# pyrefly: ignore [missing-import]
from sqlalchemy import func

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/calendar')
@login_required
def calendar():
    import calendar as py_calendar

    date_str = request.args.get('date')
    room_id = request.args.get('room_id', type=int)
    capacity = request.args.get('capacity', type=int)
    equipment = request.args.get('equipment')
    
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = datetime.utcnow().date()
    else:
        selected_date = datetime.utcnow().date()
        
    cal = py_calendar.Calendar(firstweekday=0)
    month_dates = cal.monthdatescalendar(selected_date.year, selected_date.month)
    
    start_of_calendar = month_dates[0][0]
    end_of_calendar = month_dates[-1][-1]
    
    if selected_date.month == 1:
        prev_month_date = selected_date.replace(year=selected_date.year - 1, month=12, day=1)
    else:
        prev_month_date = selected_date.replace(month=selected_date.month - 1, day=1)
        
    if selected_date.month == 12:
        next_month_date = selected_date.replace(year=selected_date.year + 1, month=1, day=1)
    else:
        next_month_date = selected_date.replace(month=selected_date.month + 1, day=1)
    
    room_query = Room.query
    if capacity:
        room_query = room_query.filter(Room.capacity >= capacity)
    if equipment:
        room_query = room_query.filter(Room.equipment.ilike(f"%{equipment}%"))
    rooms = room_query.all()
    room_ids = [r.id for r in rooms]
    
    # Query bookings for this calendar view
    booking_query = Booking.query.filter(
        Booking.status.in_(['active', 'confirmed']),
        Booking.start_at >= datetime.combine(start_of_calendar, datetime.min.time()),
        Booking.end_at <= datetime.combine(end_of_calendar, datetime.max.time())
    )
    
    if room_id:
        booking_query = booking_query.filter(Booking.room_id == room_id)
    else:
        booking_query = booking_query.filter(Booking.room_id.in_(room_ids))
        
    bookings = booking_query.all()
    
    # Group bookings by week and day for the monthly grid
    weeks_data = []
    for week in month_dates:
        week_data = []
        for day_date in week:
            day_bookings = [b for b in bookings if b.start_at.date() == day_date]
            week_data.append({
                'date': day_date,
                'bookings': sorted(day_bookings, key=lambda x: x.start_at),
                'is_today': day_date == datetime.utcnow().date(),
                'is_current_month': day_date.month == selected_date.month
            })
        weeks_data.append(week_data)
        
    all_rooms = Room.query.filter_by(is_active=True).all()
    
    return render_template(
        'bookings/calendar.html',
        prev_month_date=prev_month_date,
        next_month_date=next_month_date,
        selected_date=selected_date,
        weeks_data=weeks_data,
        rooms=rooms,
        all_rooms=all_rooms,
        selected_room_id=room_id,
        capacity=capacity,
        equipment=equipment
    )

@booking_bp.route('/calendar/day/<date_str>')
@login_required
def calendar_day(date_str):
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Неверный формат даты.', 'danger')
        return redirect(url_for('booking.calendar'))
        
    room_id = request.args.get('room_id', type=int)
    
    booking_query = Booking.query.filter(
        Booking.status.in_(['active', 'confirmed']),
        Booking.start_at >= datetime.combine(selected_date, datetime.min.time()),
        Booking.end_at <= datetime.combine(selected_date, datetime.max.time())
    )
    
    if room_id:
        booking_query = booking_query.filter(Booking.room_id == room_id)
        
    bookings = booking_query.order_by(Booking.start_at).all()
    
    return render_template(
        'bookings/calendar_day.html',
        selected_date=selected_date,
        bookings=bookings,
        room_id=room_id
    )

@booking_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_booking():
    room_id = request.args.get('room_id', type=int)
    rooms = Room.query.filter_by(is_active=True, status='active').all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        selected_room_id = request.form.get('room_id', type=int)
        start_str = request.form.get('start_at')
        end_str = request.form.get('end_at')
        participants_count = request.form.get('participants_count', type=int, default=1)
        participants_str = request.form.get('participants', '')
        comment = request.form.get('comment')
        
        if not title or not selected_room_id or not start_str or not end_str:
            flash('Название встречи, переговорная комната и время начала/окончания обязательны.', 'danger')
            return render_template('bookings/form.html', rooms=rooms, action='create', selected_room_id=room_id)
            
        try:
            start_at = datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
            end_at = datetime.strptime(end_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Неверный формат ввода даты/времени.', 'danger')
            return render_template('bookings/form.html', rooms=rooms, action='create', selected_room_id=room_id)
            
        now = datetime.utcnow()
        if start_at >= end_at:
            flash('Время окончания встречи не может быть раньше или равно времени начала.', 'danger')
            return render_template('bookings/form.html', rooms=rooms, action='create', selected_room_id=room_id)
            
        # 5 minutes leeway for time synchronization
        if start_at < now - timedelta(minutes=5):
            flash('Невозможно забронировать переговорную в прошлом.', 'danger')
            return render_template('bookings/form.html', rooms=rooms, action='create', selected_room_id=room_id)
            
        room = Room.query.get(selected_room_id)
        if not room or not room.is_active or room.status != 'active':
            flash('Выбранная комната в данный момент неактивна или находится на ремонте.', 'danger')
            return render_template('bookings/form.html', rooms=rooms, action='create', selected_room_id=room_id)
            
        # Overlap booking check: new_start < existing_end AND new_end > existing_start
        conflicting = Booking.query.filter(
            Booking.room_id == selected_room_id,
            Booking.status.in_(['active', 'confirmed']),
            Booking.start_at < end_at,
            Booking.end_at > start_at
        ).first()
        
        if conflicting:
            alternatives = Room.query.filter(
                Room.is_active == True,
                Room.status == 'active',
                ~Room.id.in_(
                    db.session.query(Booking.room_id).filter(
                        Booking.status.in_(['active', 'confirmed']),
                        Booking.start_at < end_at,
                        Booking.end_at > start_at
                    )
                )
            ).order_by(Room.capacity.asc()).limit(3).all()
            
            flash(f'Данный слот времени занят встречей: "{conflicting.title}" ({conflicting.start_at.strftime("%H:%M")} - {conflicting.end_at.strftime("%H:%M")}).', 'danger')
            return render_template('bookings/form.html', rooms=rooms, action='create', selected_room_id=room_id, alternatives=alternatives)
            
        booking = Booking(
            user_id=current_user.id,
            room_id=selected_room_id,
            title=title,
            description=description or comment,
            participants_count=participants_count,
            start_at=start_at,
            end_at=end_at,
            status='active'
        )
        
        file = request.files.get('attachment')
        attachment_obj = None
        if file and file.filename != '':
            if allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{original_filename}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                
                try:
                    file.save(file_path)
                    attachment_obj = Attachment(
                        original_filename=original_filename,
                        stored_filename=unique_filename,
                        file_path=file_path
                    )
                except Exception as e:
                    flash(f'Ошибка записи прикрепленного файла: {str(e)}', 'danger')
                    return render_template('bookings/form.html', rooms=rooms, action='create', selected_room_id=room_id)
            else:
                flash('Указанный формат файла не поддерживается (разрешены: pdf, doc/docx, xls/xlsx, csv, txt, png, jpg, zip).', 'danger')
                return render_template('bookings/form.html', rooms=rooms, action='create', selected_room_id=room_id)
                
        try:
            db.session.add(booking)
            db.session.flush()
            
            if attachment_obj:
                attachment_obj.booking_id = booking.id
                db.session.add(attachment_obj)
                
            emails = [e.strip() for e in participants_str.split(',') if e.strip()]
            for email in emails:
                registered_user = User.query.filter_by(email=email).first()
                participant = BookingParticipant(
                    booking_id=booking.id,
                    participant_email=email,
                    response_status='pending',
                    user_id=registered_user.id if registered_user else None
                )
                db.session.add(participant)
                
                if registered_user:
                    send_notification(
                        registered_user.id,
                        f"Сотрудник {current_user.full_name} пригласил вас на встречу '{title}' в '{room.name}' ({start_at.strftime('%d.%m %H:%M')}-{end_at.strftime('%H:%M')}).",
                        booking_id=booking.id
                    )
                    
            db.session.commit()
            
            log_action(current_user.id, 'booking', booking.id, 'create_booking', f"Booked room {room.name} for: {title}")
            send_notification(
                current_user.id,
                f"Успешное бронирование комнаты '{room.name}' на {start_at.strftime('%d.%m.%Y с %H:%M по ')} {end_at.strftime('%H:%M')}.",
                booking_id=booking.id
            )
            
            flash('Бронирование успешно создано.', 'success')
            return redirect(url_for('booking.calendar', room_id=selected_room_id, date=start_at.strftime('%Y-%m-%d')))
        except Exception as e:
            db.session.rollback()
            if attachment_obj and os.path.exists(attachment_obj.file_path):
                os.remove(attachment_obj.file_path)
            flash(f'Ошибка при записи бронирования: {str(e)}', 'danger')
            
    return render_template('bookings/form.html', rooms=rooms, action='create', selected_room_id=room_id)

@booking_bp.route('/<int:booking_id>')
@login_required
def detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template('bookings/detail.html', booking=booking)

@booking_bp.route('/<int:booking_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    is_owner = booking.user_id == current_user.id
    is_admin = current_user.role == 'admin' and current_user.can_manage_bookings
    is_root = current_user.role == 'root'
    
    if not (is_owner or is_admin or is_root):
        flash('Доступ запрещен. Вы не являетесь организатором встречи.', 'danger')
        return redirect(url_for('booking.calendar'))
        
    rooms = Room.query.filter_by(is_active=True, status='active').all()
    if booking.room not in rooms:
        rooms.append(booking.room)
        
    participant_emails = ", ".join([p.participant_email for p in booking.participants])
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        selected_room_id = request.form.get('room_id', type=int)
        start_str = request.form.get('start_at')
        end_str = request.form.get('end_at')
        participants_count = request.form.get('participants_count', type=int, default=1)
        participants_str = request.form.get('participants', '')
        comment = request.form.get('comment')
        
        if not title or not selected_room_id or not start_str or not end_str:
            flash('Название встречи, комната и даты проведения обязательны.', 'danger')
            return render_template('bookings/form.html', booking=booking, rooms=rooms, participant_emails=participant_emails, action='edit')
            
        try:
            start_at = datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
            end_at = datetime.strptime(end_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Неверный формат ввода даты.', 'danger')
            return render_template('bookings/form.html', booking=booking, rooms=rooms, participant_emails=participant_emails, action='edit')
            
        if start_at >= end_at:
            flash('Время окончания встречи не может быть раньше времени начала.', 'danger')
            return render_template('bookings/form.html', booking=booking, rooms=rooms, participant_emails=participant_emails, action='edit')
            
        # Overlap booking check (excluding self)
        conflicting = Booking.query.filter(
            Booking.room_id == selected_room_id,
            Booking.status.in_(['active', 'confirmed']),
            Booking.id != booking_id,
            Booking.start_at < end_at,
            Booking.end_at > start_at
        ).first()
        
        if conflicting:
            alternatives = Room.query.filter(
                Room.is_active == True,
                Room.status == 'active',
                ~Room.id.in_(
                    db.session.query(Booking.room_id).filter(
                        Booking.status.in_(['active', 'confirmed']),
                        Booking.start_at < end_at,
                        Booking.end_at > start_at
                    )
                )
            ).order_by(Room.capacity.asc()).limit(3).all()
            
            flash(f'Выбранное время пересекается с существующим бронированием: "{conflicting.title}".', 'danger')
            return render_template('bookings/form.html', booking=booking, rooms=rooms, participant_emails=participant_emails, action='edit', alternatives=alternatives)
            
        room = Room.query.get(selected_room_id)
        if not room or not room.is_active or room.status != 'active':
            flash('Выбранная комната не существует, неактивна или находится на ремонте.', 'danger')
            return render_template('bookings/form.html', booking=booking, rooms=rooms, participant_emails=participant_emails, action='edit')
        
        file = request.files.get('attachment')
        attachment_obj = None
        if file and file.filename != '':
            if allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{original_filename}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                
                try:
                    file.save(file_path)
                    for old_att in booking.attachments:
                        if os.path.exists(old_att.file_path):
                            os.remove(old_att.file_path)
                        db.session.delete(old_att)
                    
                    attachment_obj = Attachment(
                        booking_id=booking.id,
                        original_filename=original_filename,
                        stored_filename=unique_filename,
                        file_path=file_path
                    )
                except Exception as e:
                    flash(f'Ошибка сохранения нового вложения: {str(e)}', 'danger')
                    return render_template('bookings/form.html', booking=booking, rooms=rooms, participant_emails=participant_emails, action='edit')
            else:
                flash('Формат файла не поддерживается.', 'danger')
                return render_template('bookings/form.html', booking=booking, rooms=rooms, participant_emails=participant_emails, action='edit')
                
        old_room_name = booking.room.name
        booking.title = title
        booking.description = description or comment
        booking.participants_count = participants_count
        booking.room_id = selected_room_id
        booking.start_at = start_at
        booking.end_at = end_at
        
        try:
            if attachment_obj:
                db.session.add(attachment_obj)
                
            BookingParticipant.query.filter_by(booking_id=booking.id).delete()
            emails = [e.strip() for e in participants_str.split(',') if e.strip()]
            for email in emails:
                registered_user = User.query.filter_by(email=email).first()
                participant = BookingParticipant(
                    booking_id=booking.id,
                    participant_email=email,
                    response_status='pending',
                    user_id=registered_user.id if registered_user else None
                )
                db.session.add(participant)
                
                if registered_user:
                    send_notification(
                        registered_user.id,
                        f"Бронирование '{title}' в '{room.name}' (ранее '{old_room_name}') было изменено. Новое время: {start_at.strftime('%d.%m %H:%M')}-{end_at.strftime('%H:%M')}.",
                        booking_id=booking.id
                    )
                    
            db.session.commit()
            
            log_action(current_user.id, 'booking', booking.id, 'edit_booking', f"Modified booking: {title}")
            send_notification(
                booking.user_id,
                f"Ваша встреча '{title}' была отредактирована. Время проведения: {start_at.strftime('%d.%m.%Y с %H:%M по ')} {end_at.strftime('%H:%M')}.",
                booking_id=booking.id
            )
            
            flash('Бронирование изменено успешно.', 'success')
            return redirect(url_for('booking.detail', booking_id=booking.id))
        except Exception as e:
            db.session.rollback()
            if attachment_obj and os.path.exists(attachment_obj.file_path):
                os.remove(attachment_obj.file_path)
            flash(f'Ошибка базы данных при обновлении: {str(e)}', 'danger')
            
    return render_template('bookings/form.html', booking=booking, rooms=rooms, participant_emails=participant_emails, action='edit')

@booking_bp.route('/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    is_owner = booking.user_id == current_user.id
    is_admin = current_user.role == 'admin' and current_user.can_manage_bookings
    is_root = current_user.role == 'root'
    
    if not (is_owner or is_admin or is_root):
        flash('У вас нет прав для отмены этого бронирования.', 'danger')
        return redirect(url_for('booking.calendar'))
        
    try:
        booking.status = 'cancelled'
        db.session.commit()
        
        log_action(current_user.id, 'booking', booking_id, 'cancel_booking', f"Cancelled meeting slot: {booking.title}")
        
        if current_user.id != booking.user_id:
            send_notification(
                booking.user_id,
                f"Ваша бронь '{booking.title}' в комнату '{booking.room.name}' была отменена администратором.",
                booking_id=booking.id
            )
            
        for p in booking.participants:
            registered_user = User.query.filter_by(email=p.participant_email).first()
            if registered_user:
                send_notification(
                    registered_user.id,
                    f"Встреча '{booking.title}' в '{booking.room.name}' на {booking.start_at.strftime('%d.%m.%Y %H:%M')} отменена.",
                    booking_id=booking.id
                )
                
        flash('Бронирование успешно отменено.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при отмене встречи: {str(e)}', 'danger')
        
    return redirect(request.referrer or url_for('booking.calendar'))

@booking_bp.route('/match', methods=['GET', 'POST'])
@login_required
def match_room():
    if request.method == 'POST':
        start_str = request.form.get('start_at')
        end_str = request.form.get('end_at')
        participants = request.form.get('participants', type=int, default=1)
        equipment = request.form.get('equipment', '')
        location = request.form.get('location', '')
        
        if not start_str or not end_str:
            flash('Пожалуйста, укажите дату и время начала и окончания.', 'warning')
            return render_template('bookings/match.html')
            
        try:
            start_at = datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
            end_at = datetime.strptime(end_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Неверный формат ввода даты/времени.', 'danger')
            return render_template('bookings/match.html')
            
        if start_at >= end_at:
            flash('Время окончания встречи не может быть раньше времени начала.', 'danger')
            return render_template('bookings/match.html', start_val=start_str, end_val=end_str, participants=participants)
            
        # 1. Start query for active and available rooms
        query = Room.query.filter_by(is_active=True, status='active')
        
        # 2. Filter by capacity
        query = query.filter(Room.capacity >= participants)
        
        # 3. Filter by equipment if provided
        if equipment:
            query = query.filter(Room.equipment.ilike(f"%{equipment}%"))
            
        # 4. Filter by location if provided
        if location:
            query = query.filter(Room.location.ilike(f"%{location}%"))
            
        # 5. Find rooms that are NOT booked in the given time slot
        occupied_room_ids_query = db.session.query(Booking.room_id).filter(
            Booking.status.in_(['active', 'confirmed']),
            Booking.start_at < end_at,
            Booking.end_at > start_at
        )
        
        query = query.filter(~Room.id.in_(occupied_room_ids_query))
        
        available_rooms = query.all()
        
        if not available_rooms:
            flash('К сожалению, по заданным критериям не найдено ни одной свободной комнаты. Попробуйте изменить параметры.', 'warning')
            return render_template('bookings/match.html', start_val=start_str, end_val=end_str, participants=participants, equipment=equipment, location=location)
            
        # Calculate load for each available room for the current week to recommend the least loaded one
        start_of_week = datetime.utcnow().date() - timedelta(days=datetime.utcnow().weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        load_query = dict(db.session.query(
            Booking.room_id, func.count(Booking.id)
        ).filter(
            Booking.room_id.in_([r.id for r in available_rooms]),
            Booking.status.in_(['active', 'confirmed']),
            Booking.start_at >= datetime.combine(start_of_week, datetime.min.time()),
            Booking.start_at <= datetime.combine(end_of_week, datetime.max.time())
        ).group_by(Booking.room_id).all())
        
        # Sort by: 1) Capacity ascending (closest fit) 2) Load ascending (least loaded) 3) Name
        available_rooms.sort(key=lambda r: (r.capacity, load_query.get(r.id, 0), r.name))
        
        recommended_room = available_rooms[0]
        alternatives = available_rooms[1:]
        
        return render_template('bookings/match_result.html', 
            recommended=recommended_room, 
            alternatives=alternatives,
            start_str=start_str, 
            end_str=end_str,
            participants=participants,
            start_date=start_at,
            end_date=end_at
        )
        
    return render_template('bookings/match.html')

@booking_bp.route('/uploads/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
