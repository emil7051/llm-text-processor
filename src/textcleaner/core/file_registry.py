"""File type and extension registry for the LLM Text Processor."""

from pathlib import Path
from typing import Dict, List, Optional, Set

from textcleaner.utils.logging_config import get_logger


class FileTypeRegistry:
    """Registry for managing file types, extensions, and format mappings."""

    def __init__(self):
        """Initialize the file type registry."""
        self.logger = get_logger(__name__)
        
        # Map of format names to their default extensions
        self._format_to_extension: Dict[str, str] = {
            "markdown": "md",
            "plain_text": "txt",
            "json": "json",
            "csv": "csv",
            "html": "html",
            "xml": "xml",
        }
        
        # Map of file extensions to supported conversion formats
        self._extension_to_formats: Dict[str, List[str]] = {
            # PDF
            ".pdf": ["markdown", "plain_text", "json"],
            # Word (add .doc, .odt)
            ".docx": ["markdown", "plain_text", "json"],
            ".doc": ["markdown", "plain_text", "json"],
            ".odt": ["markdown", "plain_text", "json"],
            # Excel (add .xls, .ods)
            ".xlsx": ["markdown", "plain_text", "json", "csv"],
            ".xls": ["markdown", "plain_text", "json", "csv"],
            ".ods": ["markdown", "plain_text", "json", "csv"],
            # PowerPoint (add .ppt, .odp)
            ".pptx": ["markdown", "plain_text", "json"],
            ".ppt": ["markdown", "plain_text", "json"],
            ".odp": ["markdown", "plain_text", "json"],
            # Text & Markdown (add .markdown)
            ".txt": ["markdown", "plain_text", "json"],
            ".md": ["plain_text", "json"],
            ".markdown": ["plain_text", "json"],
            # HTML/XML (add .xhtml)
            ".html": ["markdown", "plain_text", "json"],
            ".htm": ["markdown", "plain_text", "json"],
            ".xhtml": ["markdown", "plain_text", "json"],
            ".xml": ["markdown", "plain_text", "json"],
            # Data formats (Treat as text for now)
            ".json": ["markdown", "plain_text"],
            ".csv": ["markdown", "plain_text", "json"],
        }
        
        # Set of supported extensions (for quick lookup)
        self._supported_extensions: Set[str] = set(self._extension_to_formats.keys())

    def get_default_extension(self, format_name: str) -> str:
        """Get the default file extension for a format.
        
        Args:
            format_name: Name of the format (e.g., 'markdown', 'plain_text')
            
        Returns:
            The default extension for the format (without leading dot)
        """
        return self._format_to_extension.get(format_name.lower(), "txt")
    
    def get_supported_formats(self, file_path: Path) -> List[str]:
        """Get supported conversion formats for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of supported formats for the file
        """
        ext = file_path.suffix.lower()
        return self._extension_to_formats.get(ext, [])
    
    def is_supported_extension(self, file_path: Path) -> bool:
        """Check if a file extension is supported.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file extension is supported, False otherwise
        """
        return file_path.suffix.lower() in self._supported_extensions
    
    def should_process_file(self, 
                           file_path: Path, 
                           file_extensions: Optional[List[str]] = None) -> bool:
        """Determine if a file should be processed.
        
        Args:
            file_path: Path to the file
            file_extensions: Optional list of file extensions to process
            
        Returns:
            True if the file should be processed, False otherwise
        """
        # Get file extension (with the dot)
        ext = file_path.suffix.lower()
        
        # If specific extensions were provided, check against those
        if file_extensions:
            return ext in file_extensions
            
        # Otherwise, check if we have support for this file type
        return ext in self._supported_extensions
    
    def get_all_supported_extensions(self) -> List[str]:
        """Get a list of all supported file extensions.
        
        Returns:
            List of supported file extensions (with leading dot)
        """
        return list(self._supported_extensions)
    
    def register_extension(self, 
                          extension: str, 
                          supported_formats: List[str]) -> None:
        """Register a new file extension with supported formats.
        
        Args:
            extension: File extension to register (with leading dot)
            supported_formats: List of formats the extension supports
        """
        # Ensure extension has leading dot
        if not extension.startswith('.'):
            extension = f".{extension}"
            
        extension = extension.lower()
        
        self._extension_to_formats[extension] = supported_formats
        self._supported_extensions.add(extension)
        
        self.logger.info(f"Registered extension '{extension}' with formats: {supported_formats}")
    
    def register_format(self, 
                       format_name: str, 
                       default_extension: str) -> None:
        """Register a new output format with its default extension.
        
        Args:
            format_name: Name of the format to register
            default_extension: Default extension for the format (without leading dot)
        """
        format_name = format_name.lower()
        
        # Remove leading dot if present
        if default_extension.startswith('.'):
            default_extension = default_extension[1:]
            
        self._format_to_extension[format_name] = default_extension
        
        self.logger.info(f"Registered format '{format_name}' with default extension: {default_extension}")
