# pyrefly: ignore [missing-import]
from flask import Blueprint, render_template, redirect, url_for, flash, request
# pyrefly: ignore [missing-import]
from flask_login import login_required, current_user
from app.models import db, User, Room, Booking, AuditLog
from app.utils import root_required, log_action

root_bp = Blueprint('root', __name__)

@root_bp.route('/')
@root_bp.route('/dashboard')
@login_required
@root_required
def dashboard():
    # Retrieve administrative and employee registers
    admins = User.query.filter(User.role == 'admin').order_by(User.email.asc()).all()
    users = User.query.filter(User.role == 'user').order_by(User.email.asc()).all()
    
    rooms_count = Room.query.count()
    bookings_count = Booking.query.count()
    users_count = User.query.count()
    active_bookings_count = Booking.query.filter_by(status='active').count()
    
    # pyrefly: ignore [missing-import]
    from sqlalchemy import func
    busiest_query = db.session.query(
        Room.name, func.count(Booking.id).label('cnt')
    ).join(Booking).filter(Booking.status.in_(['active', 'confirmed'])).group_by(Room.name).order_by(db.desc('cnt')).first()
    
    busiest_room_name = busiest_query[0] if busiest_query else "Нет данных"
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(5).all()
    
    return render_template(
        'root/dashboard.html', 
        admins=admins, 
        users=users,
        rooms_count=rooms_count,
        bookings_count=bookings_count,
        users_count=users_count,
        active_bookings_count=active_bookings_count,
        busiest_room_name=busiest_room_name,
        recent_logs=recent_logs
    )

@root_bp.route('/create-admin', methods=['GET', 'POST'])
@login_required
@root_required
def create_admin():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not full_name or not email or not password or not confirm_password:
            flash('Пожалуйста, заполните все обязательные поля формы.', 'danger')
            return render_template('root/create_admin.html')
            
        if password != confirm_password:
            flash('Пароли не совпадают.', 'danger')
            return render_template('root/create_admin.html')
            
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Данный email адрес уже зарегистрирован в системе.', 'danger')
            return render_template('root/create_admin.html')
            
        admin = User(
            full_name=full_name,
            email=email,
            role='admin',
            is_active=True,
            can_manage_rooms=True if request.form.get('can_manage_rooms') else False,
            can_manage_bookings=True if request.form.get('can_manage_bookings') else False,
            can_manage_users=True if request.form.get('can_manage_users') else False,
            can_view_analytics=True if request.form.get('can_view_analytics') else False,
            can_export_reports=True if request.form.get('can_export_reports') else False,
            can_view_audit_logs=True if request.form.get('can_view_audit_logs') else False
        )
        admin.set_password(password)
        
        try:
            db.session.add(admin)
            db.session.commit()
            
            log_action(current_user.id, 'user', admin.id, 'create_admin', f"Created admin: {email}")
            flash(f"Учетная запись администратора {email} создана успешно.", 'success')
            return redirect(url_for('root.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Ошибка при записи нового администратора в базу данных.', 'danger')
            
    return render_template('root/create_admin.html')

@root_bp.route('/users/<int:user_id>/permissions', methods=['GET', 'POST'])
@login_required
@root_required
def manage_permissions(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'root':
        flash('Невозможно изменить уровень доступа владельца системы (root).', 'danger')
        return redirect(url_for('root.dashboard'))
        
    if request.method == 'POST':
        new_role = request.form.get('role')
        if new_role in ['admin', 'user']:
            user.role = new_role
            
        # Checkboxes parsing
        user.can_manage_rooms = True if request.form.get('can_manage_rooms') else False
        user.can_manage_bookings = True if request.form.get('can_manage_bookings') else False
        user.can_manage_users = True if request.form.get('can_manage_users') else False
        user.can_view_analytics = True if request.form.get('can_view_analytics') else False
        user.can_export_reports = True if request.form.get('can_export_reports') else False
        user.can_view_audit_logs = True if request.form.get('can_view_audit_logs') else False
        
        try:
            db.session.commit()
            log_action(current_user.id, 'user', user.id, 'modify_permissions', f"Updated role/permissions for {user.email}")
            flash(f"Права доступа для пользователя {user.email} успешно обновлены.", 'success')
            return redirect(url_for('root.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Не удалось зафиксировать права в базе данных.', 'danger')
            
    return render_template('root/permissions.html', user=user)
