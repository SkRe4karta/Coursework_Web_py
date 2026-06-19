from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import db, Booking, Room, User, AuditLog
from app.utils import admin_required, log_action

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required()
def dashboard():
    rooms_count = Room.query.count()
    bookings_count = Booking.query.count()
    users_count = User.query.count()
    active_bookings_count = Booking.query.filter_by(status='active').count()
    
    from sqlalchemy import func
    busiest_query = db.session.query(
        Room.name, func.count(Booking.id).label('cnt')
    ).join(Booking).filter(Booking.status.in_(['active', 'confirmed'])).group_by(Room.name).order_by(db.desc('cnt')).first()
    
    busiest_room_name = busiest_query[0] if busiest_query else "Нет данных"
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        rooms_count=rooms_count,
        bookings_count=bookings_count,
        users_count=users_count,
        active_bookings_count=active_bookings_count,
        busiest_room_name=busiest_room_name,
        recent_logs=recent_logs
    )

@admin_bp.route('/bookings')
@login_required
@admin_required('can_manage_bookings')
def list_bookings():
    bookings = Booking.query.order_by(Booking.start_at.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings)

@admin_bp.route('/users')
@login_required
@admin_required('can_manage_users')
def list_users():
    users = User.query.order_by(User.email.asc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required('can_manage_users')
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'root':
        flash('Невозможно заблокировать главного администратора.', 'danger')
        return redirect(url_for('admin.list_users'))
        
    if user.id == current_user.id:
        flash('Вы не можете заблокировать самого себя.', 'danger')
        return redirect(url_for('admin.list_users'))
        
    user.is_active = not user.is_active
    db.session.commit()
    
    status_str = "blocked" if not user.is_active else "activated"
    log_action(current_user.id, 'user', user.id, 'toggle_active', f"User {user.email} status set to: {status_str}")
    flash(f"Пользователь {user.email} успешно {'разблокирован' if user.is_active else 'заблокирован'}.", 'success')
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/audit-logs')
@login_required
@admin_required('can_view_audit_logs')
def list_audit_logs():
    action = request.args.get('action')
    entity_type = request.args.get('entity_type')
    
    query = AuditLog.query
    if action:
        query = query.filter_by(action=action)
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
        
    logs = query.order_by(AuditLog.created_at.desc()).all()
    
    # Get distinct values for filter dropdowns
    actions = [r[0] for r in db.session.query(AuditLog.action).distinct().all()]
    entity_types = [r[0] for r in db.session.query(AuditLog.entity_type).distinct().all()]
    
    return render_template(
        'admin/audit_logs.html', 
        logs=logs,
        actions=actions,
        entity_types=entity_types,
        selected_action=action,
        selected_entity_type=entity_type
    )
