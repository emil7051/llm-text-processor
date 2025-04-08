"""Logging configuration for the LLM Text Processor.

This module configures the logging system for the entire application,
ensuring consistent log formatting and behavior.
"""

import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union


def configure_logging(
    log_level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> None:
    """Configure the logging system for the application.
    
    Args:
        log_level: Desired logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to a log file. If None, logs to console only.
        log_format: Format string for log messages.
    """
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        }
    }
    
    if log_file:
        log_file_path = Path(log_file)
        log_dir = log_file_path.parent
        
        # Create the log directory if it doesn't exist
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
        
        handlers["file"] = {
            "class": "logging.FileHandler",
            "level": log_level,
            "formatter": "standard",
            "filename": str(log_file_path),
            "encoding": "utf-8",
        }
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": handlers,
        "loggers": {
            "": {  # Root logger
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": True,
            },
            "llm_text_processor": {
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
