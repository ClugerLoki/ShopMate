from app import db
from datetime import datetime
from sqlalchemy import Text

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    notification_preference = db.Column(db.String(20), default='email')  # 'email' or 'email_whatsapp'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to monitors
    monitors = db.relationship('ProductMonitor', backref='user', lazy=True, cascade='all, delete-orphan')

class ProductMonitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Product details
    product_url = db.Column(Text, nullable=False)
    product_name = db.Column(db.String(200), nullable=True)
    product_price = db.Column(db.String(50), nullable=True)
    
    # Monitoring conditions
    check_stock = db.Column(db.Boolean, default=False)
    check_size = db.Column(db.Boolean, default=False)
    desired_size = db.Column(db.String(20), nullable=True)
    check_delivery = db.Column(db.Boolean, default=False)
    check_price = db.Column(db.Boolean, default=False)
    target_price = db.Column(db.Float, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_checked = db.Column(db.DateTime, nullable=True)
    last_status = db.Column(db.String(100), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to notifications
    notifications = db.relationship('Notification', backref='monitor', lazy=True, cascade='all, delete-orphan')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monitor_id = db.Column(db.Integer, db.ForeignKey('product_monitor.id'), nullable=False)
    
    notification_type = db.Column(db.String(20), nullable=False)  # 'email', 'whatsapp'
    message = db.Column(Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='sent')  # 'sent', 'failed'
