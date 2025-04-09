"""
Markdown file converter for the LLM Text Processor.

This converter handles markdown files (.md) and provides extraction
with preservation of markdown formatting.
"""

# import os # Removed unused import
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
# Import yaml at the top level
import yaml

from textcleaner.converters.base import BaseConverter
from textcleaner.utils.logging_config import get_logger
from textcleaner.config.config_manager import ConfigManager


class MarkdownConverter(BaseConverter):
    """Converter for markdown files.
    
    This converter reads markdown files and preserves their formatting
    while extracting metadata from frontmatter if present.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the markdown converter."""
        super().__init__(config)
        self.logger = get_logger(__name__)
        self.logger.debug("Initializing MarkdownConverter")
        
        # Set the supported file extensions
        self.supported_extensions = [".md", ".markdown"]
        
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
                original_content = f.read() # Store original content
                
            lines = original_content.splitlines() # Split into lines
            frontmatter_text = None
            body_lines = lines
            metadata = {}
            
            if lines and lines[0].strip() == '---':
                try:
                    end_marker_index = -1
                    for i, line in enumerate(lines[1:], start=1):
                        if line.strip() == '---':
                            end_marker_index = i
                            break
                            
                    if end_marker_index > 0:
                        frontmatter_lines = lines[1:end_marker_index]
                        frontmatter_text = "\n".join(frontmatter_lines)
                        body_lines = lines[end_marker_index + 1:]
                        
                        # Attempt to parse the extracted frontmatter
                        metadata = self._extract_frontmatter(frontmatter_text)
                        
                except Exception as e: # Catch potential errors during index/slice
                    self.logger.warning(f"Error processing potential frontmatter: {e}")
                    # Reset in case of error, treat as no frontmatter found
                    frontmatter_text = None
                    body_lines = lines 
                    metadata = {}
                    
            # Reconstruct body content, preserving potential trailing newline
            content = "\n".join(body_lines)
            # Check original content for trailing newline
            if original_content.endswith('\n') and not content.endswith('\n'):
                 content += "\n" 
            
            # Extract basic file metadata (outside the frontmatter try block)
            file_stats = self.get_stats(file_path) # Use BaseConverter method
            metadata.update({
                "file_name": file_path.name,
                "file_extension": file_path.suffix.lower(),
                "file_stats": {
                    "size_bytes": file_stats.get("file_size_bytes"),
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
            
    def _extract_frontmatter(self, frontmatter_text: Optional[str]) -> Dict[str, Any]:
        """Extract YAML frontmatter from markdown content if present.
        
        Args:
            frontmatter_text: The extracted text between --- markers (or None).
            
        Returns:
            Dictionary of metadata extracted from frontmatter.
        """
        metadata = {}
        if not frontmatter_text:
            return metadata # Return empty if no text was passed
            
        try:
            # Strip just in case, though splitting/joining should handle most
            frontmatter_data = yaml.safe_load(frontmatter_text.strip())
            
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
