# -*- coding: utf-8 -*-
import logging
import os
import time
import json
from datetime import datetime
from typing import List, Dict
from threading import Lock

class LogManager:
    """Centralized log management system with persistence"""
    
    def __init__(self):
        self.logs = []
        self.max_logs = 2000
        self.log_file = 'app_logs.json'
        self._lock = Lock()
        self._handler_added = False
        self._load_logs()
        self.setup_logging()
    
    def _load_logs(self):
        """Load existing logs from file"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    loaded_logs = json.load(f)
                    self.logs = loaded_logs if isinstance(loaded_logs, list) else []
                print(f"Loaded {len(self.logs)} logs from file")
            except Exception as e:
                print(f"Error loading logs file: {e}")
                self.logs = []
        else:
            # Create initial log entry
            self.logs = [{
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': 'Log system initialized',
                'module': 'logs'
            }]
    
    def _save_logs(self):
        """Save logs to file"""
        try:
            with self._lock:
                # Keep only the last max_logs entries before saving
                if len(self.logs) > self.max_logs:
                    self.logs = self.logs[-self.max_logs:]
                
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    json.dump(self.logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving logs file: {e}")
    
    def setup_logging(self):
        """Setup custom logging handler to capture logs"""
        if self._handler_added:
            return
            
        try:
            # Create custom handler
            handler = LogCapturingHandler(self)
            handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            
            # Add handler to root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(handler)
            
            self._handler_added = True
            print("Log handler setup completed")
        except Exception as e:
            print(f"Error setting up log handler: {e}")
    
    def add_log(self, level: str, message: str, module: str = 'app'):
        """Add log entry to memory storage"""
        try:
            with self._lock:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'level': level,
                    'message': message,
                    'module': module
                }
                
                self.logs.append(log_entry)
                
                # Keep only last max_logs entries in memory
                if len(self.logs) > self.max_logs:
                    self.logs = self.logs[-self.max_logs:]
                
                # Save to file every 5 new logs or on ERROR/WARNING
                if len(self.logs) % 5 == 0 or level in ['ERROR', 'WARNING']:
                    self._save_logs()
        except Exception as e:
            print(f"Error adding log: {e}")
    
    def get_logs(self, level: str = 'all', lines: int = 100) -> List[Dict]:
        """Get filtered logs"""
        try:
            with self._lock:
                filtered_logs = self.logs.copy()
                
                # Filter by level
                if level.upper() != 'ALL':
                    filtered_logs = [log for log in filtered_logs if log['level'] == level.upper()]
                
                # Return last N lines
                return filtered_logs[-lines:] if filtered_logs else []
        except Exception as e:
            print(f"Error getting logs: {e}")
            return []
    
    def clear_logs(self):
        """Clear all logs"""
        try:
            with self._lock:
                self.logs.clear()
                # Also clear the file
                if os.path.exists(self.log_file):
                    os.remove(self.log_file)
                
                # Add a cleared log entry
                self.logs.append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'message': 'Logs cleared by admin',
                    'module': 'logs'
                })
                
                self._save_logs()
        except Exception as e:
            print(f"Error clearing logs: {e}")

class LogCapturingHandler(logging.Handler):
    """Custom logging handler to capture logs in memory"""
    
    def __init__(self, log_manager):
        super().__init__()
        self.log_manager = log_manager
    
    def emit(self, record):
        """Emit log record to memory storage"""
        try:
            # Extract module name from logger name
            module = record.name.split('.')[-1] if '.' in record.name else record.name
            
            # Add to log manager
            self.log_manager.add_log(
                level=record.levelname,
                message=record.getMessage(),
                module=module
            )
        except Exception:
            # Prevent infinite recursion if logging fails
            pass

# Global log manager instance
log_manager = LogManager()