from functools import wraps
# pyrefly: ignore [missing-import]
from flask import abort, flash, redirect, url_for, current_app
# pyrefly: ignore [missing-import]
from flask_login import current_user
from app.models import db, AuditLog, Notification

def admin_required(permission_name=None):
    """
    Decorator to check if user has admin/root role.
    If permission_name is specified, checks if the admin has that specific permission.
    Root user always has all permissions.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Root has access to everything
            if current_user.role == 'root':
                return f(*args, **kwargs)
                
            # Admins check specific permissions
            if current_user.role == 'admin':
                if permission_name is None:
                    return f(*args, **kwargs)
                elif getattr(current_user, permission_name, False):
                    return f(*args, **kwargs)
                else:
                    flash('У вас нет прав для совершения этого действия.', 'danger')
                    return redirect(url_for('booking.calendar'))
            
            # Non-admins get rejected
            flash('Доступ запрещен. Требуются права администратора.', 'danger')
            return redirect(url_for('booking.calendar'))
        return decorated_function
    return decorator

def root_required(f):
    """
    Decorator to restrict access to the root administrator only.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role != 'root':
            flash('Доступ запрещен. Требуются права главного администратора (root).', 'danger')
            return redirect(url_for('booking.calendar'))
        return f(*args, **kwargs)
    return decorated_function

def log_action(user_id, entity_type, entity_id, action, details=None):
    """
    Creates a entry in the audit_logs database table.
    """
    try:
        log = AuditLog(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            details=details
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to save audit log: {str(e)}")

def send_notification(user_id, message, booking_id=None, channel='web'):
    """
    Saves a user notification to the database.
    Can be expanded in the future for actual SMTP email sending.
    """
    try:
        notification = Notification(
            user_id=user_id,
            booking_id=booking_id,
            channel=channel,
            message=message,
            status='unread'
        )
        db.session.add(notification)
        db.session.commit()
        
        # Placeholder for SMTP integration
        # if channel == 'email':
        #     send_smtp_email(user_id, message)
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to send notification: {str(e)}")

def allowed_file(filename):
    """
    Checks if a filename has an allowed extension defined in the config.
    """
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']
