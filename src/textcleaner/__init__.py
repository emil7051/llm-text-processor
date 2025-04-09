"""TextCleaner.

A versatile system for converting various file formats into clean,
structured text optimized for Large Language Models (LLMs).
"""

__version__ = "0.2.1"

# Import essential components
from textcleaner.config.config_manager import ConfigManager
from textcleaner.core.processor import TextProcessor
from textcleaner.core.models import ProcessingResult

__all__ = ["ConfigManager", "TextProcessor", "ProcessingResult"]
