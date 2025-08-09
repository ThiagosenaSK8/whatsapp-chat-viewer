# -*- coding: utf-8 -*-
"""
Migration script to update message types from old system to new system:

Old system:
- 'user': All outgoing messages
- 'ai': All incoming messages (from webhook)

New system:
- 'lead': Messages received from external (via webhook) - incoming
- 'user': Messages sent by human when AI is inactive - outgoing
- 'ai': Messages sent by AI when AI is active - outgoing

This script will:
1. Update all current 'ai' type messages to 'lead' (received messages)
2. Keep 'user' type messages as they are (sent by users)
3. Show statistics of the migration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from db.connection import init_database
from db.models import db, Message
import logging

def create_migration_app():
    """Create Flask app for migration"""
    app = Flask(__name__)
    
    # Use the same database configuration as main app
    database_url = os.getenv('DATABASE_URL', '')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("Make sure your .env file contains DATABASE_URL")
        sys.exit(1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    init_database(app)
    
    return app

def migrate_message_types():
    """Migrate message types from old system to new system"""
    
    print("🚀 Starting message type migration...")
    print("=" * 60)
    
    try:
        # Get statistics before migration
        total_messages = Message.query.count()
        old_ai_messages = Message.query.filter_by(type='ai').count()
        old_user_messages = Message.query.filter_by(type='user').count()
        
        print(f"📊 BEFORE MIGRATION:")
        print(f"   Total messages: {total_messages}")
        print(f"   'ai' type messages: {old_ai_messages}")
        print(f"   'user' type messages: {old_user_messages}")
        print()
        
        if old_ai_messages == 0:
            print("✅ No 'ai' type messages found to migrate")
            print("Migration not needed or already completed")
            return
        
        # Confirm migration
        response = input(f"🔄 Migrate {old_ai_messages} 'ai' messages to 'lead'? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("❌ Migration cancelled by user")
            return
        
        print("\n🔄 Performing migration...")
        
        # Update all 'ai' type messages to 'lead'
        # These were previously messages received from webhook
        updated_count = db.session.query(Message).filter_by(type='ai').update(
            {Message.type: 'lead'},
            synchronize_session=False
        )
        
        # Commit the changes
        db.session.commit()
        
        print(f"✅ Successfully updated {updated_count} messages from 'ai' to 'lead'")
        
        # Get statistics after migration
        new_total_messages = Message.query.count()
        new_lead_messages = Message.query.filter_by(type='lead').count()
        new_user_messages = Message.query.filter_by(type='user').count()
        new_ai_messages = Message.query.filter_by(type='ai').count()
        
        print(f"\n📊 AFTER MIGRATION:")
        print(f"   Total messages: {new_total_messages}")
        print(f"   'lead' type messages: {new_lead_messages}")
        print(f"   'user' type messages: {new_user_messages}")
        print(f"   'ai' type messages: {new_ai_messages}")
        print()
        
        # Validation
        if updated_count == old_ai_messages and new_lead_messages == old_ai_messages:
            print("✅ Migration completed successfully!")
            print("🎯 New message type logic:")
            print("   - 'lead': Messages received from external sources")
            print("   - 'user': Messages sent by humans (when AI is inactive)")
            print("   - 'ai': Messages sent by AI (when AI is active)")
        else:
            print("⚠️ Migration validation warning:")
            print(f"   Expected: {old_ai_messages} messages migrated")
            print(f"   Actual: {updated_count} messages migrated")
            print(f"   'lead' messages now: {new_lead_messages}")
        
    except Exception as e:
        print(f"❌ Migration failed with error: {e}")
        print("Rolling back changes...")
        db.session.rollback()
        return
    
    print("\n" + "=" * 60)
    print("🎉 Message type migration completed!")

def rollback_migration():
    """Rollback migration (convert 'lead' back to 'ai')"""
    
    print("🔄 Starting migration rollback...")
    print("=" * 60)
    
    try:
        # Get current statistics
        lead_messages = Message.query.filter_by(type='lead').count()
        
        print(f"📊 CURRENT STATE:")
        print(f"   'lead' type messages: {lead_messages}")
        
        if lead_messages == 0:
            print("✅ No 'lead' type messages found to rollback")
            return
        
        # Confirm rollback
        response = input(f"🔄 Rollback {lead_messages} 'lead' messages to 'ai'? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("❌ Rollback cancelled by user")
            return
        
        print("\n🔄 Performing rollback...")
        
        # Update all 'lead' type messages back to 'ai'
        updated_count = db.session.query(Message).filter_by(type='lead').update(
            {Message.type: 'ai'},
            synchronize_session=False
        )
        
        # Commit the changes
        db.session.commit()
        
        print(f"✅ Successfully rolled back {updated_count} messages from 'lead' to 'ai'")
        
    except Exception as e:
        print(f"❌ Rollback failed with error: {e}")
        print("Rolling back changes...")
        db.session.rollback()
        return
    
    print("🎉 Migration rollback completed!")

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.WARNING)  # Reduce database logging noise
    
    # Create Flask app context
    app = create_migration_app()
    
    with app.app_context():
        print("WhatsApp Chat Viewer - Message Type Migration")
        print("=" * 60)
        
        if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
            rollback_migration()
        else:
            migrate_message_types()
