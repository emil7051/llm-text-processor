"""Logging configuration for TextCleaner."""

import logging
import sys
from typing import Optional
from pathlib import Path


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
    level = level_map.get(log_level.upper(), logging.INFO)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create and add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add console handler to root logger
    root_logger.addHandler(console_handler)
    
    # Add file handler if log file specified
    if log_file:
        try:
            # Create directory if it doesn't exist
            log_path = Path(log_file)
            if not log_path.parent.exists():
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
            # Create file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            
            # Add file handler to root logger
            root_logger.addHandler(file_handler)
        except Exception as e:
            logging.error(f"Failed to create log file: {e}")


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Get a logger with the specified name and level.
    
    Args:
        name: Name of the logger
        level: Logging level (if None, uses INFO level)
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    # Set default level if not provided
    if level is None:
        level = logging.INFO
        
    logger.setLevel(level)
    
    # Only add handlers if they don't exist yet
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    return logger
