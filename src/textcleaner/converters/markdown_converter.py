"""
Markdown file converter for the LLM Text Processor.

This converter handles markdown files (.md) and provides extraction
with preservation of markdown formatting.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from textcleaner.converters.base import BaseConverter
from textcleaner.utils.logging_config import get_logger


class MarkdownConverter(BaseConverter):
    """Converter for markdown files.
    
    This converter reads markdown files and preserves their formatting
    while extracting metadata from frontmatter if present.
    """
    
    def __init__(self):
        """Initialize the markdown converter."""
        super().__init__()
        self.logger = get_logger(__name__)
        self.logger.debug("Initializing MarkdownConverter")
        
        # Set the supported file extensions
        self.supported_extensions = [".md", ".markdown"]
        
    def get_supported_extensions(self) -> Set[str]:
        """Get the set of file extensions supported by this converter.
        
        Returns:
            Set of supported file extensions.
        """
        return {".md", ".markdown"}
        
    def convert(self, file_path: Union[str, Path]) -> Tuple[str, Dict[str, Any]]:
        """Convert a markdown file to raw text.
        
        Args:
            file_path: Path to the markdown file to convert.
            
        Returns:
            Tuple of (text content, metadata dictionary).
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is not a valid markdown file.
        """
        # Ensure file_path is a Path object
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        self.logger.info(f"Converting markdown file: {file_path}")
        
        # Check if the file exists
        if not file_path.exists():
            error_msg = f"File not found: {file_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        # Read the file content
        try:
            self.logger.debug(f"Reading markdown file content from {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Extract metadata from frontmatter if present
            metadata = self._extract_frontmatter(content)
            
            # If frontmatter was found, remove it from the content
            if "frontmatter" in metadata:
                content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
            
            # Extract basic file metadata
            file_stats = file_path.stat()
            metadata.update({
                "file_name": file_path.name,
                "file_extension": file_path.suffix.lower(),
                "file_stats": {
                    "size_bytes": file_stats.st_size,
                    "created_at": file_stats.st_ctime,
                    "modified_at": file_stats.st_mtime,
                }
            })
            
            # Extract headings for additional metadata
            headings = self._extract_headings(content)
            if headings:
                metadata["headings"] = headings
                
            self.logger.info(f"Successfully converted markdown file: {file_path}")
            self.logger.debug(f"Extracted {len(content)} characters of text")
            
            return content, metadata
            
        except UnicodeDecodeError:
            error_msg = f"File is not a valid markdown file or has an unsupported encoding: {file_path}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error reading markdown file {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise
            
    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract YAML frontmatter from markdown content if present.
        
        Args:
            content: Markdown content to extract frontmatter from.
            
        Returns:
            Dictionary of metadata extracted from frontmatter.
        """
        metadata = {}
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        
        if frontmatter_match:
            try:
                import yaml
                frontmatter_text = frontmatter_match.group(1)
                frontmatter_data = yaml.safe_load(frontmatter_text)
                
                if isinstance(frontmatter_data, dict):
                    metadata["frontmatter"] = frontmatter_data
                    
                    # Extract common metadata fields
                    for key in ["title", "author", "date", "description", "tags", "categories"]:
                        if key in frontmatter_data:
                            metadata[key] = frontmatter_data[key]
            except Exception as e:
                self.logger.warning(f"Error parsing frontmatter: {str(e)}")
                
        return metadata
        
    def _extract_headings(self, content: str) -> List[Dict[str, Any]]:
        """Extract headings from markdown content for TOC generation.
        
        Args:
            content: Markdown content to extract headings from.
            
        Returns:
            List of heading dictionaries with level and text.
        """
        # Match ATX-style headings (# Heading)
        heading_pattern = r'^(#{1,6})\s+(.+?)(?:\s+#{1,6})?$'
        headings = []
        
        for line in content.split('\n'):
            match = re.match(heading_pattern, line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append({
                    "level": level,
                    "text": text
                })
                
        return headings
