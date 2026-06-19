import os
# pyrefly: ignore [missing-import]
from flask import Flask, render_template
# pyrefly: ignore [missing-import]
from flask_login import LoginManager
from app.models import db, User, Notification
from config import Config

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Для доступа к этой странице необходимо авторизоваться.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user and user.is_active:
        return user
    return None

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize SQLAlchemy & LoginManager
    db.init_app(app)
    login_manager.init_app(app)
    
    # Import Blueprints
    from app.auth import auth_bp
    from app.rooms import rooms_bp
    from app.booking import booking_bp
    from app.admin import admin_bp
    from app.root import root_bp
    from app.analytics import analytics_bp
    from app.reports import reports_bp
    
    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(rooms_bp, url_prefix='/rooms')
    app.register_blueprint(booking_bp, url_prefix='/bookings')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(root_bp, url_prefix='/root')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    # Index landing route
    @app.route('/')
    def index():
        return render_template('index.html')

    # Global variables injected into Jinja2 context
    @app.context_processor
    def inject_global_data():
        import datetime
        unread_notifications_count = 0
        # pyrefly: ignore [missing-import]
        from flask_login import current_user
        if current_user.is_authenticated:
            try:
                unread_notifications_count = Notification.query.filter_by(
                    user_id=current_user.id, 
                    status='unread'
                ).count()
            except Exception:
                pass  # Database might not be initialized yet
        return dict(unread_notifications_count=unread_notifications_count, datetime=datetime)
    # Error handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
        
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
        
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
        
    return app
