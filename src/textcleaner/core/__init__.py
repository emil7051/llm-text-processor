"""Core functionality for the TextCleaner."""

# Define what will be exported
__all__ = ["FileTypeRegistry", "ProcessingResult"]

# Import core components
from textcleaner.core.file_registry import FileTypeRegistry
from textcleaner.core.models import ProcessingResult
