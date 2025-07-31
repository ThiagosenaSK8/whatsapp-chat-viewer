# -*- coding: utf-8 -*-
import logging
from typing import List, Optional
from db.models import db, User, PhoneNumber, Message
from datetime import datetime, date

class UserOperations:
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email"""
        try:
            return User.query.filter_by(email=email).first()
        except Exception as e:
            logging.error(f"Error getting user by email {email}: {e}")
            return None
    
    @staticmethod
    def create_user(email: str, password: str) -> Optional[User]:
        """Create new user"""
        try:
            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            logging.info(f"User created: {email}")
            return user
        except Exception as e:
            logging.error(f"Error creating user {email}: {e}")
            db.session.rollback()
            return None

class PhoneOperations:
    @staticmethod
    def get_all_phone_numbers() -> List[PhoneNumber]:
        """Get all phone numbers"""
        try:
            return PhoneNumber.query.order_by(PhoneNumber.created_at.desc()).all()
        except Exception as e:
            logging.error(f"Error getting all phone numbers: {e}")
            return []
    
    @staticmethod
    def get_phone_by_number(number: str) -> Optional[PhoneNumber]:
        """Get phone by number"""
        try:
            return PhoneNumber.query.filter_by(number=number).first()
        except Exception as e:
            logging.error(f"Error getting phone by number {number}: {e}")
            return None
    
    @staticmethod
    def toggle_ai_status(phone_id: int) -> bool:
        """Toggle AI status for a phone number"""
        try:
            phone = PhoneNumber.query.get(phone_id)
            if phone:
                phone.ai_active = not phone.ai_active
                db.session.commit()
                logging.info(f"AI status toggled for phone {phone.number}: {phone.ai_active}")
                return True
            return False
        except Exception as e:
            logging.error(f"Error toggling AI status for phone {phone_id}: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def create_phone_number(number: str) -> Optional[PhoneNumber]:
        """Create new phone number"""
        try:
            existing_phone = PhoneOperations.get_phone_by_number(number)
            if existing_phone:
                return existing_phone
            
            phone = PhoneNumber(number=number, ai_active=False)
            db.session.add(phone)
            db.session.commit()
            logging.info(f"Phone number created: {number}")
            return phone
        except Exception as e:
            logging.error(f"Error creating phone number {number}: {e}")
            db.session.rollback()
            return None

class MessageOperations:
    @staticmethod
    def get_messages_by_phone(phone_number: str, limit: int = 100) -> List[Message]:
        """Get messages for a specific phone number"""
        try:
            phone = PhoneOperations.get_phone_by_number(phone_number)
            if not phone:
                return []
            
            return Message.query.filter_by(phone_number_id=phone.id)\
                                .order_by(Message.created_at.asc())\
                                .limit(limit).all()
        except Exception as e:
            logging.error(f"Error getting messages for phone {phone_number}: {e}")
            return []
    
    @staticmethod
    def create_message(phone_number: str, content: str, message_type: str, 
                      attachment_url: str = None, attachment_full_url: str = None,
                      attachment_name: str = None, attachment_type: str = None, 
                      attachment_size: int = None) -> Optional[Message]:
        """Create new message"""
        try:
            phone = PhoneOperations.get_phone_by_number(phone_number)
            if not phone:
                phone = PhoneOperations.create_phone_number(phone_number)
                if not phone:
                    return None
            
            message = Message(
                phone_number_id=phone.id,
                content=content,
                type=message_type,
                attachment_url=attachment_url,
                attachment_full_url=attachment_full_url,
                attachment_name=attachment_name,
                attachment_type=attachment_type,
                attachment_size=attachment_size
            )
            db.session.add(message)
            db.session.commit()
            logging.info(f"Message created for phone {phone_number}: {message_type}")
            return message
        except Exception as e:
            logging.error(f"Error creating message for phone {phone_number}: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_daily_stats(target_date: date = None) -> dict:
        """Get daily statistics"""
        try:
            if not target_date:
                target_date = date.today()
            
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            total_messages = Message.query.filter(
                Message.created_at.between(start_datetime, end_datetime)
            ).count()
            
            ai_messages = Message.query.filter(
                Message.created_at.between(start_datetime, end_datetime),
                Message.type == 'ai'
            ).count()
            
            cost = ai_messages * 0.10
            
            return {
                'total_messages': total_messages,
                'ai_messages': ai_messages,
                'cost': cost,
                'date': target_date.isoformat()
            }
        except Exception as e:
            logging.error(f"Error getting daily stats: {e}")
            return {
                'total_messages': 0,
                'ai_messages': 0,
                'cost': 0.0,
                'date': target_date.isoformat() if target_date else date.today().isoformat()
            }