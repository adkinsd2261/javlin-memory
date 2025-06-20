
"""
Bulletproof Logging System for MemoryOS
Ensures logging never fails and always captures critical information
"""

import os
import logging
import traceback
from datetime import datetime, timezone
from pathlib import Path

class BulletproofLogger:
    """A logging system that never fails and always captures errors"""
    
    def __init__(self, name="MemoryOS", logs_dir="logs"):
        self.name = name
        self.logs_dir = Path(logs_dir)
        
        # Ensure logs directory exists
        try:
            self.logs_dir.mkdir(exist_ok=True)
        except Exception as e:
            print(f"⚠️ Could not create logs directory: {e}")
            self.logs_dir = Path(".")  # Fallback to current directory
        
        self.setup_logging()
    
    def setup_logging(self):
        """Setup bulletproof logging configuration"""
        try:
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Setup file handlers with fallbacks
            self.file_handlers = []
            
            # Main log file
            try:
                main_handler = logging.FileHandler(self.logs_dir / 'memoryos.log')
                main_handler.setFormatter(formatter)
                main_handler.setLevel(logging.INFO)
                self.file_handlers.append(main_handler)
            except Exception as e:
                print(f"⚠️ Could not setup main log file: {e}")
            
            # Error-specific log file
            try:
                error_handler = logging.FileHandler(self.logs_dir / 'errors.log')
                error_handler.setFormatter(formatter)
                error_handler.setLevel(logging.ERROR)
                self.file_handlers.append(error_handler)
            except Exception as e:
                print(f"⚠️ Could not setup error log file: {e}")
            
            # Console handler (always works)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)
            
            # Configure root logger
            self.logger = logging.getLogger(self.name)
            self.logger.setLevel(logging.INFO)
            
            # Add all handlers
            for handler in self.file_handlers:
                self.logger.addHandler(handler)
            self.logger.addHandler(console_handler)
            
        except Exception as e:
            print(f"🔥 Critical logging setup failure: {e}")
            # Create minimal fallback logger
            self.logger = logging.getLogger(self.name)
            console_handler = logging.StreamHandler()
            self.logger.addHandler(console_handler)
    
    def log_error(self, message, error=None, include_traceback=True):
        """Log an error with full context - NEVER fails"""
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Build error message
            if error:
                error_msg = f"{message}: {str(error)}"
            else:
                error_msg = message
            
            # Log to configured logger
            self.logger.error(error_msg)
            
            # Add traceback if requested and available
            if include_traceback and error:
                tb = traceback.format_exc()
                self.logger.error(f"TRACEBACK: {tb}")
            
            # Fallback: Always print to console
            print(f"🚨 ERROR [{timestamp}]: {error_msg}")
            
            # Fallback: Write to simple error file
            try:
                with open('emergency_errors.log', 'a') as f:
                    f.write(f"[{timestamp}] {error_msg}\n")
                    if include_traceback and error:
                        f.write(f"TRACEBACK: {traceback.format_exc()}\n")
                    f.write("-" * 50 + "\n")
            except Exception:
                pass  # Even this fallback can fail, but we don't crash
                
        except Exception as meta_error:
            # If logging itself fails, use print as ultimate fallback
            print(f"🔥 LOGGING SYSTEM FAILURE: {meta_error}")
            print(f"🔥 ORIGINAL ERROR: {message}")
    
    def log_info(self, message):
        """Log info message with fallback"""
        try:
            self.logger.info(message)
        except Exception:
            print(f"ℹ️ {message}")
    
    def log_warning(self, message):
        """Log warning message with fallback"""
        try:
            self.logger.warning(message)
        except Exception:
            print(f"⚠️ {message}")

# Global bulletproof logger instance
bulletproof_logger = BulletproofLogger()
