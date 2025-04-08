"""Base converter classes for handling different file formats."""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from textcleaner.config.config_manager import ConfigManager


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
        self.converters: List[BaseConverter] = []
    
    def register(self, converter: BaseConverter) -> None:
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
        
    def register_converter(self, converter_class: type) -> None:
        """Register a converter class.
        
        Args:
            converter_class: Converter class to register. Must be a subclass of BaseConverter.
            
        Raises:
            TypeError: If converter_class is not a subclass of BaseConverter.
        """
        if not issubclass(converter_class, BaseConverter):
            raise TypeError("Converter must be a subclass of BaseConverter")
            
        # Create instance and add to registry
        converter = converter_class(self.config)
        self.converters.append(converter)
    
    def set_config(self, config: ConfigManager) -> None:
        """Set the configuration for all registered converters.
        
        Args:
            config: Configuration manager instance to use.
        """
        self.config = config
        
        # Update the config for all existing converters
        for converter in self.converters:
            converter.config = config
        
    def find_converter(self, file_path: Union[str, Path]) -> Optional[BaseConverter]:
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
        
    def convert_file(self, file_path: Union[str, Path]) -> Tuple[str, Dict[str, Any]]:
        """Convert a file using the appropriate converter.
        
        Args:
            file_path: Path to the file to convert.
            
        Returns:
            Tuple of (raw_content, metadata_dict).
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If no converter is found for the file format.
            RuntimeError: If conversion fails.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        converter = self.find_converter(file_path)
        if not converter:
            raise ValueError(f"No converter found for file: {file_path}")
            
        return converter.convert(file_path)
