"""Base converter classes for handling different file formats."""

# import os # Removed - Unused import
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from textcleaner.config.config_manager import ConfigManager

# Import specific converter implementations here
# Removed direct imports to avoid circular dependency
# Imports are now done inside methods where needed or at the bottom


class BaseConverter(ABC):
    """Base class for all file format converters.
    
    This abstract class defines the interface that all converters must implement.
    Each converter is responsible for handling specific file formats and extracting
    content and metadata.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the converter.
        
        Args:
            config: Configuration manager instance. If None, default settings are used.
        """
        self.config = config or ConfigManager()
        # List of file extensions this converter can handle
        self.supported_extensions: List[str] = []
        
    def can_handle(self, file_path: Union[str, Path]) -> bool:
        """Check if this converter can handle the given file.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            True if this converter can handle the file, False otherwise.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        return file_path.suffix.lower() in self.supported_extensions
        
    @abstractmethod
    def convert(self, file_path: Union[str, Path]) -> Tuple[str, Dict[str, Any]]:
        """Convert file to raw content and extract metadata.
        
        This method should extract the text content from the file and
        return it along with any relevant metadata.
        
        Args:
            file_path: Path to the file to convert.
            
        Returns:
            Tuple of (raw_content, metadata_dict).
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file format is unsupported.
            RuntimeError: If conversion fails.
        """
        pass
    
    def get_stats(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get statistics about the file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Dictionary with file statistics (size, etc.).
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        return {
            "file_name": file_path.name,
            "file_extension": file_path.suffix,
            "file_size_bytes": file_path.stat().st_size,
            "file_size_kb": round(file_path.stat().st_size / 1024, 2),
            "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
        }


class ConverterRegistry:
    """Registry for file format converters.
    
    This class maintains a registry of converter classes and provides methods
    to register new converters and find appropriate converters for files.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the converter registry.
        
        Args:
            config: Configuration manager instance to pass to converters.
        """
        self.config = config or ConfigManager()
        self.converters: List['BaseConverter'] = [] # Use forward reference string
    
    def populate_registry(self) -> None:
        """Register all standard converters with the registry using the current config."""
        # Import here to avoid circular dependency at module level
        from textcleaner.converters.pdf_converter import PDFConverter
        from textcleaner.converters.office_converter import OfficeConverter
        from textcleaner.converters.html_converter import HTMLConverter
        from textcleaner.converters.text_converter import TextConverter
        from textcleaner.converters.markdown_converter import MarkdownConverter
        from textcleaner.converters.csv_converter import CSVConverter

        if not self.config:
            raise RuntimeError("Registry must have a config set before populating.")

        config = self.config

        # Clear existing converters before repopulating
        self.converters = []

        # Register the PDF converter
        self.register(PDFConverter(config=config))

        # Register the Office document converter with specific config values
        self.register(OfficeConverter(
            extract_comments=config.get("formats.office.extract_comments", False),
            extract_tracked_changes=config.get("formats.office.extract_tracked_changes", False),
            extract_hidden_content=config.get("formats.office.extract_hidden_content", False),
            max_excel_rows=config.get("formats.office.max_excel_rows", 1000),
            max_excel_cols=config.get("formats.office.max_excel_cols", 20),
            config=config
        ))

        # Register the HTML/XML converter with specific config values
        self.register(HTMLConverter(
            parser=config.get("converters.html.parser", "html.parser"),
            remove_comments=config.get("converters.html.remove_comments", True),
            remove_scripts=config.get("converters.html.remove_scripts", True),
            remove_styles=config.get("converters.html.remove_styles", True),
            extract_metadata=config.get("converters.html.extract_metadata", True),
            preserve_links=config.get("converters.html.preserve_links", True),
            config=config
        ))

        # Register the plain text converter
        self.register(TextConverter(config=config))

        # Register the markdown converter
        self.register(MarkdownConverter(config=config))

        # Register the CSV converter
        self.register(CSVConverter(config=config))

    def register(self, converter: 'BaseConverter') -> None: # Use forward reference string
        """Register an instantiated converter.
        
        Args:
            converter: Converter instance to register. Must be an instance of BaseConverter.
            
        Raises:
            TypeError: If converter is not an instance of BaseConverter.
        """
        if not isinstance(converter, BaseConverter):
            raise TypeError("Converter must be an instance of BaseConverter")
            
        # Add to registry
        self.converters.append(converter)
        
        # Set config if available
        if self.config:
            converter.config = self.config
        
    def set_config(self, config: ConfigManager) -> None:
        """Set the configuration for all registered converters.
        
        Args:
            config: Configuration manager instance to use.
        """
        self.config = config
        
        # Update the config for all existing converters
        for converter in self.converters:
            converter.config = config
        
    def find_converter(self, file_path: Union[str, Path]) -> Optional['BaseConverter']: # Use forward reference string
        """Find a converter that can handle the given file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            A converter instance that can handle the file, or None if no converter is found.
        """
        for converter in self.converters:
            if converter.can_handle(file_path):
                return converter
                
        return None
