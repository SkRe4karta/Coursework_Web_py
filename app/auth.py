from datetime import datetime
# pyrefly: ignore [missing-import]
from flask import Blueprint, render_template, redirect, url_for, flash, request
# pyrefly: ignore [missing-import]
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Booking, Notification
from app.utils import log_action, send_notification

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('booking.calendar'))
        
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not full_name or not email or not password or not confirm_password:
            flash('Пожалуйста, заполните все поля.', 'danger')
            return render_template('auth/register.html')
            
        if password != confirm_password:
            flash('Пароли не совпадают.', 'danger')
            return render_template('auth/register.html')
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Пользователь с таким email уже зарегистрирован.', 'danger')
            return render_template('auth/register.html')
            
        new_user = User(
            full_name=full_name,
            email=email,
            role='user',
            is_active=True
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Retroactively link participant records by email
            from app.models import BookingParticipant
            BookingParticipant.query.filter_by(participant_email=email, user_id=None).update({BookingParticipant.user_id: new_user.id})
            db.session.commit()
            
            # Log audit trail
            log_action(new_user.id, 'user', new_user.id, 'register', f"User registered: {email}")
            
            # Send notification
            send_notification(new_user.id, "Добро пожаловать в систему Peregovorki! Теперь вы можете бронировать переговорные комнаты.")
            
            flash('Регистрация завершена успешно. Вы можете войти в систему.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Произошла непредвиденная ошибка при регистрации. Пожалуйста, повторите попытку.', 'danger')
            
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('booking.calendar'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        if not email or not password:
            flash('Пожалуйста, заполните все обязательные поля.', 'danger')
            return render_template('auth/login.html')
            
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Неверный адрес почты или пароль.', 'danger')
            return render_template('auth/login.html')
            
        if not user.is_active:
            flash('Ваш аккаунт был деактивирован или заблокирован администратором.', 'danger')
            return render_template('auth/login.html')
            
        login_user(user, remember=remember)
        
        log_action(user.id, 'user', user.id, 'login', f"User successfully authenticated: {email}")
        flash(f'Приветствуем вас, {user.full_name}!', 'success')
        
        next_page = request.args.get('next')
        if next_page and (not next_page.startswith('/') or next_page.startswith('//')):
            next_page = None
            
        return redirect(next_page or url_for('booking.calendar'))
        
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    uid = current_user.id
    email = current_user.email
    logout_user()
    log_action(uid, 'user', uid, 'logout', f"User logged out: {email}")
    flash('Вы успешно вышли из системы.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
@login_required
def profile():
    now = datetime.utcnow()
    
    # Separate past and upcoming bookings
    future_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.start_at >= now
    ).order_by(Booking.start_at.asc()).all()
    
    past_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.start_at < now
    ).order_by(Booking.start_at.desc()).all()
    
    # Retrieve user's system notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    
    active_bookings_count = len([b for b in future_bookings if b.status in ['active', 'confirmed']])
    nearest_booking = next((b for b in future_bookings if b.status in ['active', 'confirmed']), None)
    
    return render_template(
        'bookings/profile.html',
        future_bookings=future_bookings,
        past_bookings=past_bookings,
        notifications=notifications,
        active_bookings_count=active_bookings_count,
        nearest_booking=nearest_booking
    )

@auth_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    unread = Notification.query.filter_by(user_id=current_user.id, status='unread').all()
    for n in unread:
        n.status = 'read'
    db.session.commit()
    flash('Все уведомления были отмечены как прочитанные.', 'success')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    notification.status = 'read'
    db.session.commit()
    return redirect(url_for('auth.profile'))
