"""Logging configuration for TextCleaner."""

import logging
import sys
from typing import Optional


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
