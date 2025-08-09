# -*- coding: utf-8 -*-
import os
import logging
import time
from flask import Flask
from db.models import db, User, PhoneNumber, Message
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

def init_database(app: Flask):
    """Initialize database connection and create tables"""
    
    # Database configuration
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres123@localhost:5432/whatsapp_chat')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Basic connection pool settings
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 3600
    }
    
    # Initialize SQLAlchemy with app
    db.init_app(app)
    
    # Retry connection logic
    max_retries = 30
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            with app.app_context():
                # Create all tables
                db.create_all()
                logging.info("Database tables created successfully")
                break
        except OperationalError as e:
            if attempt == max_retries - 1:
                logging.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                raise
            logging.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    with app.app_context():
        
        # Create default user if doesn't exist
        default_user = User.query.filter_by(email='admin@admin.com').first()
        if not default_user:
            default_user = User(email='admin@admin.com')
            default_user.set_password('admin123')
            db.session.add(default_user)
            db.session.commit()
            logging.info("Default user created: admin@admin.com / admin123")
        
        # Create some sample phone numbers if they don't exist
        sample_numbers = ['+5511999999999', '+5511888888888', '+5511777777777']
        for number in sample_numbers:
            existing_phone = PhoneNumber.query.filter_by(number=number).first()
            if not existing_phone:
                phone = PhoneNumber(number=number, ai_active=False)
                db.session.add(phone)
        
        db.session.commit()
        logging.info("Sample phone numbers created")

def get_db():
    """Get database instance"""
    return db

def close_db_connections():
    """Close all database connections"""
    try:
        if db.engine:
            db.engine.dispose()
            logging.info("Database connections closed successfully")
    except Exception as e:
        logging.error(f"Error closing database connections: {e}")

def check_db_connection():
    """Check if database connection is healthy"""
    try:
        db.session.execute(text('SELECT 1'))
        return True
    except Exception as e:
        logging.error(f"Database connection check failed: {e}")
        return False