"""Configuration module for TextCleaner.

This module provides configuration management for the TextCleaner application.
"""

# Import essential components to make them available at the textcleaner.config level
from textcleaner.config.config_manager import ConfigManager
from textcleaner.config.config_factory import ConfigFactory

__all__ = ["ConfigManager", "ConfigFactory"] 