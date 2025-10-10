"""
ComfyBros Logging System
Provides centralized logging for all ComfyBros components.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path


class ComfyBrosLogger:
    """Centralized logger for ComfyBros extension"""
    
    _instance: Optional['ComfyBrosLogger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is not None:
            return
            
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup the logging configuration"""
        self._logger = logging.getLogger('ComfyBros')
        self._logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self._logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - ComfyBros - %(levelname)s - %(message)s'
        )
        
        # Console handler (always enabled)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self._logger.addHandler(console_handler)
        
        # File handler (if possible)
        try:
            log_file = self._get_log_file_path()
            if log_file:
                file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(detailed_formatter)
                self._logger.addHandler(file_handler)
                self._logger.info(f"ComfyBros logging to file: {log_file}")
        except Exception as e:
            self._logger.warning(f"Could not setup file logging: {e}")
        
        # Prevent propagation to root logger
        self._logger.propagate = False
        
        self._logger.info("ComfyBros logger initialized")
    
    def _get_log_file_path(self) -> Optional[str]:
        """Get the path for the log file"""
        try:
            # Try to use ComfyUI's user directory first
            try:
                import folder_paths
                user_dir = folder_paths.get_user_directory()
                log_dir = os.path.join(user_dir, 'logs')
            except (ImportError, AttributeError):
                # Fallback to extension directory
                ext_dir = os.path.dirname(os.path.abspath(__file__))
                log_dir = os.path.join(ext_dir, 'logs')
            
            # Create logs directory if it doesn't exist
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            
            # Create log file with date
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(log_dir, f'comfybros_{today}.log')
            
            return log_file
            
        except Exception:
            return None
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Get a logger instance"""
        if name:
            return logging.getLogger(f'ComfyBros.{name}')
        return self._logger
    
    def debug(self, message: str, component: str = ""):
        """Log debug message"""
        logger = self.get_logger(component) if component else self._logger
        logger.debug(message)
    
    def info(self, message: str, component: str = ""):
        """Log info message"""
        logger = self.get_logger(component) if component else self._logger
        logger.info(message)
    
    def warning(self, message: str, component: str = ""):
        """Log warning message"""
        logger = self.get_logger(component) if component else self._logger
        logger.warning(message)
    
    def error(self, message: str, component: str = ""):
        """Log error message"""
        logger = self.get_logger(component) if component else self._logger
        logger.error(message)
    
    def critical(self, message: str, component: str = ""):
        """Log critical message"""
        logger = self.get_logger(component) if component else self._logger
        logger.critical(message)
    
    def exception(self, message: str, component: str = ""):
        """Log exception with traceback"""
        logger = self.get_logger(component) if component else self._logger
        logger.exception(message)


# Global logger instance
comfy_logger = ComfyBrosLogger()


def get_logger(component: str = "") -> logging.Logger:
    """Get a logger for a specific component"""
    return comfy_logger.get_logger(component)


def log_debug(message: str, component: str = ""):
    """Log debug message"""
    comfy_logger.debug(message, component)


def log_info(message: str, component: str = ""):
    """Log info message"""
    comfy_logger.info(message, component)


def log_warning(message: str, component: str = ""):
    """Log warning message"""
    comfy_logger.warning(message, component)


def log_error(message: str, component: str = ""):
    """Log error message"""
    comfy_logger.error(message, component)


def log_critical(message: str, component: str = ""):
    """Log critical message"""
    comfy_logger.critical(message, component)


def log_exception(message: str, component: str = ""):
    """Log exception with traceback"""
    comfy_logger.exception(message, component)