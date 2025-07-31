# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Check if password matches hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def __repr__(self):
        return f'<User {self.email}>'

class PhoneNumber(db.Model):
    __tablename__ = 'phone_numbers'
    
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), unique=True, nullable=False)
    ai_active = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    messages = db.relationship('Message', backref='phone', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PhoneNumber {self.number}>'

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    phone_number_id = db.Column(db.Integer, db.ForeignKey('phone_numbers.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)  # Made nullable since attachments might not have text
    type = db.Column(db.String(10), nullable=False)  # 'user' ou 'ai'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Attachment fields
    attachment_url = db.Column(db.String(500), nullable=True)
    attachment_full_url = db.Column(db.String(500), nullable=True)  # URL with full domain
    attachment_name = db.Column(db.String(255), nullable=True)
    attachment_type = db.Column(db.String(50), nullable=True)  # image, video, audio, pdf, document, file
    attachment_size = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<Message {self.id} - {self.type}>'
    
    def to_dict(self):
        """Convert message to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'phone_number_id': self.phone_number_id,
            'content': self.content,
            'type': self.type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'attachment_url': self.attachment_url,
            'attachment_full_url': self.attachment_full_url,
            'attachment_name': self.attachment_name,
            'attachment_type': self.attachment_type,
            'attachment_size': self.attachment_size
        }