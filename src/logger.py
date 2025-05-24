"""
Centralized logging configuration following DRY principles.
"""
import logging
import sys
from typing import Optional

class PaymentTrackerLogger:
    """Centralized logger for the payment tracker application."""
    
    _instance: Optional['PaymentTrackerLogger'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            PaymentTrackerLogger._initialized = True
    
    def _setup_logging(self):
        """Setup logging configuration."""
        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)
        
        # Suppress noisy third-party loggers
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('google').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger instance with the specified name."""
        PaymentTrackerLogger()  # Ensure initialization
        return logging.getLogger(name)

# Convenience function for getting loggers
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return PaymentTrackerLogger.get_logger(name)