# -*- coding: utf-8 -*-
import os
import json
import logging
from typing import Optional
from datetime import datetime

class Config:
    """Centralized configuration management with persistence"""
    
    def __init__(self):
        self._webhook_url = None
        self._webhook_timeout = 5  # Default timeout
        self._initialized = False
        self.config_file = 'config.json'
        self._load_config()
    
    def _load_config(self):
        """Load configuration with production-friendly priority order"""
        try:
            # Priority 1: Saved configuration file (from interface) - PRIMARY for production
            file_webhook_url = ''
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        file_config = json.load(f)
                        file_webhook_url = file_config.get('webhook_url', '').strip()
                except Exception as e:
                    print(f"Error loading config file: {e}")
                    file_webhook_url = ''
            
            # Priority 2: Environment variable (from .env) - OVERRIDE only if explicitly set
            env_webhook_url = os.getenv('WEBHOOK_URL', '').strip()
            
            # Priority Logic: Interface First, Environment Override if needed
            if file_webhook_url:
                self._webhook_url = file_webhook_url
                print(f"✅ Webhook URL loaded from interface config: {file_webhook_url}")
                # Warn if environment would override
                if env_webhook_url and env_webhook_url != file_webhook_url:
                    print(f"⚠️  Note: Environment variable WEBHOOK_URL would override interface config")
                    print(f"   Interface: {file_webhook_url}")
                    print(f"   Environment: {env_webhook_url}")
                    print(f"   Using interface config (recommended for production)")
            elif env_webhook_url:
                self._webhook_url = env_webhook_url
                print(f"✅ Webhook URL loaded from environment (.env): {env_webhook_url}")
            else:
                self._webhook_url = ''
                print("ℹ️  No webhook URL configured - set via Settings page")
            
            # Load webhook timeout from environment (always from .env)
            try:
                self._webhook_timeout = int(os.getenv('WEBHOOK_TIMEOUT', '5'))
                print(f"✅ Webhook timeout: {self._webhook_timeout}s (from .env)")
            except (ValueError, TypeError):
                self._webhook_timeout = 5
                print("⚠️  Using default webhook timeout: 5s")
            
            self._initialized = True
            
        except Exception as e:
            print(f"❌ Error in _load_config: {e}")
            self._webhook_url = ''
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            config_data = {
                'webhook_url': self._webhook_url or '',
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    @property
    def webhook_url(self) -> str:
        """Get current webhook URL"""
        if not self._initialized:
            self._load_config()
        return self._webhook_url or ''
    
    @webhook_url.setter
    def webhook_url(self, value: str):
        """Set webhook URL with production-friendly logic"""
        value = value.strip() if value else ''
        
        # Always save to interface config (production-friendly)
        self._webhook_url = value
        
        if value:
            self._save_config()
            print(f"✅ Webhook URL saved to interface config: {value}")
            
            # Check if environment variable exists and warn if different
            env_webhook_url = os.getenv('WEBHOOK_URL', '').strip()
            if env_webhook_url and env_webhook_url != value:
                print(f"ℹ️  Note: Environment variable WEBHOOK_URL exists with different value")
                print(f"   Environment: {env_webhook_url}")
                print(f"   Interface: {value}")
                print(f"   Currently using interface config (production-friendly)")
        else:
            # Clear config - remove file
            if os.path.exists(self.config_file):
                try:
                    os.remove(self.config_file)
                    print("🗑️  Cleared webhook config")
                except Exception as e:
                    print(f"Warning: Could not remove config file: {e}")
            else:
                print("ℹ️  Webhook URL cleared")
    
    def reload_config(self):
        """Force reload configuration from file"""
        self._initialized = False
        self._load_config()
        return self._webhook_url
    
    @property
    def webhook_timeout(self) -> int:
        """Get webhook timeout in seconds"""
        return self._webhook_timeout
    
    @property
    def database_url(self) -> str:
        """Get database URL"""
        return os.getenv('DATABASE_URL', '')
    
    @property
    def secret_key(self) -> str:
        """Get secret key"""
        return os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    @property
    def flask_debug(self) -> bool:
        """Get Flask debug mode"""
        return os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    @property
    def port(self) -> int:
        """Get application port"""
        return int(os.getenv('PORT', 5000))
    
    def get_config_status(self) -> dict:
        """Get detailed configuration status for debugging"""
        env_webhook_url = os.getenv('WEBHOOK_URL', '').strip()
        file_webhook_url = ''
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    file_webhook_url = file_config.get('webhook_url', '').strip()
            except Exception:
                file_webhook_url = 'ERROR_READING_FILE'
        
        # Check if there's a potential override situation
        has_env_override = bool(env_webhook_url and file_webhook_url and env_webhook_url != file_webhook_url)
        
        # Determine active source (interface-first approach)
        if file_webhook_url:
            active_source = 'interface'
        elif env_webhook_url:
            active_source = 'env'
        else:
            active_source = 'none'
        
        return {
            'current_url': self._webhook_url,
            'env_url': env_webhook_url,
            'file_url': file_webhook_url,
            'file_exists': os.path.exists(self.config_file),
            'has_conflict': has_env_override,
            'source': active_source,
            'timeout': self._webhook_timeout,
            'recommendation': self._get_config_recommendation(env_webhook_url, file_webhook_url, has_env_override)
        }
    
    def _get_config_recommendation(self, env_url, file_url, has_override):
        """Get recommendation for configuration management"""
        if has_override:
            return "INFO: Environment variable exists but interface config is being used (production-friendly)"
        elif file_url and not env_url:
            return "GOOD: Using interface configuration (perfect for production deployment)"
        elif env_url and not file_url:
            return "OK: Using environment variable (local development setup)"
        elif not env_url and not file_url:
            return "No webhook configured - set via Settings page"
        else:
            return "GOOD: Interface and environment configurations match"

# Global configuration instance
config = Config()