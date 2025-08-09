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
    type = db.Column(db.String(10), nullable=False)  # 'lead' (received), 'user' (human sent), 'ai' (ai sent)
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
        """Convert message to dictionary for JSON serialization with safe error handling"""
        try:
            return {
                'id': self.id,
                'phone_number_id': self.phone_number_id,
                'content': self.content or '',  # Ensure content is never None
                'type': self.type,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'attachment_url': self.attachment_url or None,
                'attachment_full_url': self.attachment_full_url or None,
                'attachment_name': self.attachment_name or None,
                'attachment_type': self.attachment_type or None,
                'attachment_size': self.attachment_size or None
            }
        except Exception as e:
            # Fallback to minimal safe representation if something fails
            import logging
            logging.error(f"Error in Message.to_dict() for message {getattr(self, 'id', 'unknown')}: {e}")
            return {
                'id': getattr(self, 'id', 0),
                'phone_number_id': getattr(self, 'phone_number_id', 0),
                'content': str(getattr(self, 'content', '') or ''),
                'type': str(getattr(self, 'type', 'lead')),
                'created_at': None,
                'attachment_url': None,
                'attachment_full_url': None,
                'attachment_name': None,
                'attachment_type': None,
                'attachment_size': None
            }
    
    def has_attachment(self):
        """Check if message has any attachment"""
        return bool(self.attachment_url)
    
    def is_valid_attachment(self):
        """Check if attachment data is consistent"""
        if not self.has_attachment():
            return True  # No attachment is valid
        
        # Basic consistency checks
        has_name = bool(self.attachment_name)
        has_type = bool(self.attachment_type)
        
        # At minimum, we should have URL and type
        return has_type
    
    def get_attachment_display_name(self):
        """Get display name for attachment with fallback"""
        if not self.has_attachment():
            return None
        
        if self.attachment_name:
            return self.attachment_name
        
        # Fallback based on type
        type_names = {
            'image': 'Imagem',
            'video': 'Vídeo', 
            'audio': 'Áudio',
            'pdf': 'Documento PDF',
            'document': 'Documento',
            'file': 'Arquivo'
        }
        
        return type_names.get(self.attachment_type, 'Anexo')
    
    @staticmethod
    def validate_message_type(msg_type):
        """Validate message type"""
        valid_types = ['lead', 'user', 'ai']
        return msg_type in valid_types