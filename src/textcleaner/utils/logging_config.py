"""Logging configuration for TextCleaner."""

import logging
import sys
from typing import Optional
from pathlib import Path


# Custom filter to suppress DEBUG messages from specific libraries
class SuppressDebugFilter(logging.Filter):
    def __init__(self, names_to_suppress):
        super().__init__()
        self.names_to_suppress = names_to_suppress

    def filter(self, record):
        # Suppress if the level is DEBUG and the name starts with one of the suppressed names
        if record.levelno == logging.DEBUG:
            for name in self.names_to_suppress:
                if record.name.startswith(name):
                    return False  # Suppress the message
        return True  # Allow other messages


def configure_logging(log_level: str = 'INFO', log_file: Optional[str] = None):
    """Configure global logging for the application.
    
    Args:
        log_level: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
    """
    # Convert string level to logging level
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    level = level_map.get(log_level.upper(), logging.WARNING)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Set specific (higher) log levels for noisy libraries
    logging.getLogger("pdfminer").setLevel(logging.WARNING)
    logging.getLogger("textcleaner.utils.content_cleaning").setLevel(logging.WARNING)
    logging.getLogger("textcleaner.processors").setLevel(logging.WARNING)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create the filter instance
    suppress_filter = SuppressDebugFilter(names_to_suppress=[
        'pdfminer', 
        'textcleaner.utils.content_cleaning',
        'textcleaner.processors'
    ])

    # Create and add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create simplified formatter
    formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(formatter)
    
    # Add the filter to the console handler
    console_handler.addFilter(suppress_filter)
    
    # Add console handler to root logger
    root_logger.addHandler(console_handler)
    
    # Add file handler if log file specified
    if log_file:
        try:
            # Create directory if it doesn't exist
            log_path = Path(log_file)
            if not log_path.parent.exists():
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
            # Create file handler with detailed format for the log file
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            detailed_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(detailed_formatter)
            
            # Add the filter to the file handler
            file_handler.addFilter(suppress_filter)
            
            # Add file handler to root logger
            root_logger.addHandler(file_handler)
        except Exception as e:
            logging.error(f"Failed to create log file: {e}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)
