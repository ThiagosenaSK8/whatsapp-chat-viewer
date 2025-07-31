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
        self._initialized = False
        self.config_file = 'config.json'
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file and environment variables"""
        try:
            # First try to load from file
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        file_config = json.load(f)
                        self._webhook_url = file_config.get('webhook_url', '').strip()
                        if self._webhook_url:
                            os.environ['WEBHOOK_URL'] = self._webhook_url
                            print(f"Configuration loaded from file: {self._webhook_url}")
                except Exception as e:
                    print(f"Error loading config file: {e}")
                    self._webhook_url = None
            
            # Fallback to environment variable if no file config
            if not self._webhook_url:
                self._webhook_url = os.getenv('WEBHOOK_URL', '').strip()
                if self._webhook_url:
                    print(f"Configuration loaded from environment: {self._webhook_url}")
            
            self._initialized = True
        except Exception as e:
            print(f"Error in _load_config: {e}")
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
        """Set webhook URL and save to file"""
        value = value.strip() if value else ''
        self._webhook_url = value
        os.environ['WEBHOOK_URL'] = value
        self._save_config()
        print(f"Webhook URL updated and saved: {value}")
    
    def reload_config(self):
        """Force reload configuration from file"""
        self._initialized = False
        self._load_config()
        return self._webhook_url
    
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

# Global configuration instance
config = Config()