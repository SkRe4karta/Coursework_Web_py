from datetime import datetime
# pyrefly: ignore [missing-import]
from flask_sqlalchemy import SQLAlchemy
# pyrefly: ignore [missing-import]
from flask_login import UserMixin
# pyrefly: ignore [missing-import]
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'root', 'admin', 'user'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Granular administrative permissions
    can_manage_rooms = db.Column(db.Boolean, default=False, nullable=False)
    can_manage_bookings = db.Column(db.Boolean, default=False, nullable=False)
    can_manage_users = db.Column(db.Boolean, default=False, nullable=False)
    can_view_analytics = db.Column(db.Boolean, default=False, nullable=False)
    can_export_reports = db.Column(db.Boolean, default=False, nullable=False)
    can_view_audit_logs = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    bookings = db.relationship('Booking', backref='organizer', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def has_permission(self, permission_name):
        if self.role == 'root':
            return True
        if self.role == 'admin':
            return getattr(self, permission_name, False)
        return False

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Room(db.Model):
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    capacity = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    equipment = db.Column(db.String(255), nullable=True)  # Comma-separated list or text
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active', 'repair', 'unavailable'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    bookings = db.relationship('Booking', backref='room', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Room {self.name} (Cap: {self.capacity})>"


class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    participants_count = db.Column(db.Integer, default=1, nullable=False)
    start_at = db.Column(db.DateTime, nullable=False, index=True)
    end_at = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active', 'cancelled', 'completed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    participants = db.relationship('BookingParticipant', backref='booking', lazy=True, cascade='all, delete-orphan')
    attachments = db.relationship('Attachment', backref='booking', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='booking', lazy=True)

    def __repr__(self):
        return f"<Booking {self.title} (Room: {self.room_id}, User: {self.user_id})>"


class BookingParticipant(db.Model):
    __tablename__ = 'booking_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    participant_email = db.Column(db.String(120), nullable=False)
    response_status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'accepted', 'declined'
    notified_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)

    # Relationships
    user = db.relationship('User', backref=db.backref('participations', lazy=True))

    def __repr__(self):
        return f"<Participant {self.participant_email} (Status: {self.response_status})>"


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True)
    channel = db.Column(db.String(20), default='web', nullable=False)  # 'web', 'email'
    template = db.Column(db.String(50), nullable=True)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='unread', nullable=False)  # 'unread', 'read'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Notification {self.id} User: {self.user_id} Status: {self.status}>"


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    entity_type = db.Column(db.String(50), nullable=False)  # 'user', 'room', 'booking', 'privilege', 'report'
    entity_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(100), nullable=False)  # 'register', 'login', 'create', 'edit', 'delete', 'grant_rights', etc.
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.entity_type}:{self.entity_id}>"


class Attachment(db.Model):
    __tablename__ = 'attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Attachment {self.original_filename} (Booking: {self.booking_id})>"
