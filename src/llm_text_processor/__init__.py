"""LLM Text Preprocessing Tool.

A versatile system for converting various file formats into clean,
structured text optimized for Large Language Models (LLMs).
"""

__version__ = "0.1.0"

from llm_text_processor.config.config_manager import ConfigManager
from llm_text_processor.text_processor import TextProcessor

__all__ = ["TextProcessor", "ConfigManager"]
