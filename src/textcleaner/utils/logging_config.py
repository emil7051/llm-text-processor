"""Logging configuration for the text processor."""

import os
import logging
import logging.config
from pathlib import Path
from typing import Optional, Union, Dict, Any

# Constants for logging
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def configure_logging(
    log_level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    log_format: str = DEFAULT_LOG_FORMAT
) -> None:
    """Configure logging for the application.
    
    Args:
        log_level: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to log file. If None, logs only to console.
        log_format: Format string for log messages.
    """
    # Normalize log level
    log_level = log_level.upper()
    if log_level not in LOG_LEVELS:
        log_level = "INFO"
    
    # Set up handlers
    handlers: Dict[str, Dict[str, Any]] = {
        "console": {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        }
    }
    
    # Add file handler if log_file is specified
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        handlers["file"] = {
            "class": "logging.FileHandler",
            "level": log_level,
            "formatter": "standard",
            "filename": log_file,
            "mode": "a",
            "encoding": "utf-8",
        }
    
    # Configure logging
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": log_format,
            },
        },
        "handlers": handlers,
        "loggers": {
            "": {  # Root logger
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": True,
            },
            "textcleaner": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": False,
            },
        },
    }
    
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: Name for the logger, typically the module name.
        
    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)
