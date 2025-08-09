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
    def get_phone_by_id(phone_id: int) -> Optional[PhoneNumber]:
        """Get phone by ID"""
        try:
            return PhoneNumber.query.get(phone_id)
        except Exception as e:
            logging.error(f"Error getting phone by ID {phone_id}: {e}")
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
    
    @staticmethod
    def delete_phone(phone_id: int) -> bool:
        """Delete a phone number and all its messages (cascade)"""
        try:
            phone = PhoneNumber.query.get(phone_id)
            if phone:
                db.session.delete(phone)
                db.session.commit()
                logging.info(f"Phone deleted: {phone.number} (ID: {phone_id})")
                return True
            return False
        except Exception as e:
            logging.error(f"Error deleting phone {phone_id}: {e}")
            db.session.rollback()
            return False

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
        """
        Create new message with enhanced validation and consistency
        
        Args:
            phone_number: Phone number (will be created if doesn't exist)
            content: Message text content (can be empty if attachment provided)
            message_type: 'lead' (received), 'user' (human sent), 'ai' (ai sent)
            attachment_url: Local or external URL to attachment
            attachment_full_url: Full URL with domain (optional)
            attachment_name: Display name for attachment
            attachment_type: Type of attachment ('image', 'video', 'audio', 'pdf', 'document', 'file')
            attachment_size: Size in bytes (optional)
        
        Returns:
            Message object if successful, None if failed
        """
        try:
            # Validate message type
            if not Message.validate_message_type(message_type):
                logging.error(f"Invalid message type: {message_type}")
                return None
            
            # Ensure we have either content or attachment
            if not content and not attachment_url:
                logging.error("Message must have either content or attachment")
                return None
            
            # Get or create phone number
            phone = PhoneOperations.get_phone_by_number(phone_number)
            if not phone:
                logging.info(f"Creating new phone number: {phone_number}")
                phone = PhoneOperations.create_phone_number(phone_number)
                if not phone:
                    logging.error(f"Failed to create phone number: {phone_number}")
                    return None
            
            # Clean and validate attachment data
            clean_attachment_data = MessageOperations._clean_attachment_data(
                attachment_url, attachment_full_url, attachment_name, 
                attachment_type, attachment_size
            )
            
            # Create message with validated data
            message = Message(
                phone_number_id=phone.id,
                content=content or '',  # Ensure content is never None
                type=message_type,
                **clean_attachment_data
            )
            
            db.session.add(message)
            db.session.commit()
            
            logging.info(f"Message created: ID={message.id}, Type={message_type}, Phone={phone_number}")
            if attachment_url:
                logging.info(f"  Attachment: {attachment_name} ({attachment_type})")
            
            return message
            
        except Exception as e:
            logging.error(f"Error creating message for {phone_number}: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def _clean_attachment_data(attachment_url, attachment_full_url, attachment_name, 
                              attachment_type, attachment_size):
        """
        Clean and validate attachment data for consistency
        
        Returns:
            Dictionary with clean attachment data
        """
        cleaned = {
            'attachment_url': None,
            'attachment_full_url': None, 
            'attachment_name': None,
            'attachment_type': None,
            'attachment_size': None
        }
        
        # If no attachment URL, return empty data
        if not attachment_url:
            return cleaned
        
        # Clean URL
        cleaned['attachment_url'] = attachment_url.strip()
        
        # Set full URL (fallback to attachment_url if not provided)
        cleaned['attachment_full_url'] = attachment_full_url or attachment_url
        
        # Clean name (provide fallback based on type)
        if attachment_name:
            cleaned['attachment_name'] = attachment_name.strip()
        else:
            # Generate fallback name based on type
            type_names = {
                'image': 'image',
                'video': 'video',
                'audio': 'audio', 
                'pdf': 'document.pdf',
                'document': 'document',
                'file': 'file'
            }
            fallback_name = type_names.get(attachment_type, 'attachment')
            cleaned['attachment_name'] = fallback_name
            logging.info(f"Generated fallback attachment name: {fallback_name}")
        
        # Clean type (ensure it's valid)
        valid_types = ['image', 'video', 'audio', 'pdf', 'document', 'file']
        if attachment_type and attachment_type in valid_types:
            cleaned['attachment_type'] = attachment_type
        else:
            cleaned['attachment_type'] = 'file'  # Safe fallback
            if attachment_type:
                logging.warning(f"Invalid attachment type '{attachment_type}', using 'file'")
        
        # Clean size (ensure it's positive integer or None)
        if attachment_size is not None:
            try:
                size = int(attachment_size)
                cleaned['attachment_size'] = size if size > 0 else None
            except (ValueError, TypeError):
                cleaned['attachment_size'] = None
                logging.warning(f"Invalid attachment size '{attachment_size}', setting to None")
        
        return cleaned

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