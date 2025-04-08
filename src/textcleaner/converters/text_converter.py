"""
Plain text file converter for the LLM Text Processor.

This converter handles plain text files (.txt) and provides simple
text extraction without special formatting or metadata handling.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from textcleaner.converters.base import BaseConverter
from textcleaner.utils.logging_config import get_logger


class TextConverter(BaseConverter):
    """Converter for plain text files.
    
    This converter simply reads text files and returns their content with minimal
    processing.
    """
    
    def __init__(self):
        """Initialize the text converter."""
        super().__init__()
        self.logger = get_logger(__name__)
        self.logger.debug("Initializing TextConverter")
        
        # Set the supported file extensions
        self.supported_extensions = [".txt"]  # This is how BaseConverter.can_handle checks compatibility
        
    def get_supported_extensions(self) -> Set[str]:
        """Get the set of file extensions supported by this converter.
        
        Returns:
            Set of supported file extensions.
        """
        return {".txt"}
        
    def convert(self, file_path: Union[str, Path]) -> Tuple[str, Dict[str, Any]]:
        """Convert a text file to raw text.
        
        Args:
            file_path: Path to the text file to convert.
            
        Returns:
            Tuple of (text content, metadata dictionary).
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is not a valid text file.
        """
        # Ensure file_path is a Path object
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        self.logger.info(f"Converting text file: {file_path}")
        
        # Check if the file exists
        if not file_path.exists():
            error_msg = f"File not found: {file_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        # Read the file content
        try:
            self.logger.debug(f"Reading text file content from {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Extract basic file metadata
            file_stats = file_path.stat()
            metadata = {
                "file_name": file_path.name,
                "file_extension": file_path.suffix.lower(),
                "file_stats": {
                    "size_bytes": file_stats.st_size,
                    "created_at": file_stats.st_ctime,
                    "modified_at": file_stats.st_mtime,
                }
            }
            
            self.logger.info(f"Successfully converted text file: {file_path}")
            self.logger.debug(f"Extracted {len(content)} characters of text")
            
            return content, metadata
            
        except UnicodeDecodeError:
            error_msg = f"File is not a valid text file or has an unsupported encoding: {file_path}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error reading text file {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise
