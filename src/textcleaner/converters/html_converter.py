"""
HTML and XML document converter

This module provides functionality to convert HTML and XML documents to clean text
while preserving the semantic structure of the document.
"""

import os
# import re # Removed unused import
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Comment, NavigableString, Tag, FeatureNotFound
from bs4.builder import ParserRejectedMarkup

from textcleaner.converters.base import BaseConverter
from textcleaner.utils.logging_config import get_logger
from textcleaner.utils import html_processing as hp_utils # Import new utility

logger = get_logger(__name__)


class HTMLConverter(BaseConverter):
    """Converter for HTML and XML documents.
    
    This converter uses BeautifulSoup to parse HTML and XML documents and
    extract meaningful content while preserving the document structure.
    It handles both local files and remote URLs.
    """

    def __init__(self, 
                 parser: str,
                 remove_comments: bool,
                 remove_scripts: bool,
                 remove_styles: bool,
                 extract_metadata: bool,
                 preserve_links: bool,
                 config=None): # Keep config for BaseConverter
        """Initialize the HTML converter.
        
        Args:
            parser: The parser to use (e.g., 'html.parser', 'lxml').
            remove_comments: Whether to remove HTML comments.
            remove_scripts: Whether to remove <script> tags.
            remove_styles: Whether to remove <style> tags.
            extract_metadata: Whether to extract metadata (title, meta tags).
            preserve_links: Whether to preserve links in Markdown format.
            config: Configuration manager instance (passed to BaseConverter).
        """
        super().__init__(config)
        
        # Define the supported file extensions
        self.supported_extensions = [".html", ".htm", ".xhtml", ".xml"]
        
        # Store specific parsing options
        self.parser = parser
        self.remove_comments = remove_comments
        self.remove_scripts = remove_scripts
        self.remove_styles = remove_styles
        self.extract_metadata = extract_metadata
        self.preserve_links = preserve_links
    
    def can_handle(self, file_path: Union[str, Path]) -> bool:
        """Check if the file can be handled by this converter.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            True if the file can be handled, False otherwise.
        """
        # Handle file paths
        path_str = str(file_path).lower()
        
        # Check if it's a URL with an HTML/XML path
        if path_str.startswith(('http://', 'https://')):
            parsed_url = urlparse(path_str)
            # URL with no path extension but probably HTML content
            if not os.path.splitext(parsed_url.path)[1]:
                return True
            # URL with HTML/XML extension
            return any(parsed_url.path.endswith(ext) for ext in self.supported_extensions)
        
        # Check if it's a local file with supported extension
        return any(path_str.endswith(ext) for ext in self.supported_extensions)
    
    def convert(self, file_path: Union[str, Path]) -> Tuple[str, Dict[str, Any]]:
        """Convert an HTML/XML document to clean text.
        
        Args:
            file_path: Path to the HTML/XML file or a URL.
            
        Returns:
            A tuple containing the extracted text and metadata.
        """
        path_str = str(file_path)
        
        # Handle URLs or local files
        if path_str.startswith(('http://', 'https://')):
            # For URLs, we'll need to fetch the content
            try:
                import requests
                response = requests.get(path_str, timeout=30)
                response.raise_for_status()  # Raise an exception for HTTP errors
                content = response.text
                filename = os.path.basename(urlparse(path_str).path) or "index.html"
            except requests.RequestException as e:
                logger.error(f"Failed to fetch URL {path_str}: {e}")
                raise RuntimeError(f"Failed to fetch URL: {str(e)}") from e
        else:
            # For local files, read the content
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                filename = os.path.basename(path_str)
            except IOError as e:
                logger.error(f"Failed to read file {file_path}: {e}")
                raise RuntimeError(f"Failed to read file: {str(e)}") from e
        
        # Parse the HTML/XML content
        try:
            # Select appropriate parser based on file extension
            if isinstance(file_path, Path) and file_path.suffix.lower() == '.xml':
                # Use XML parser for XML files
                from bs4 import XMLParsedAsHTMLWarning
                import warnings
                
                # Filter out the warning for XML parsed as HTML
                warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
                
                # Try to use lxml's XML parser if available, otherwise fall back to html.parser
                try:
                    soup = BeautifulSoup(content, features="xml")
                except ParserRejectedMarkup:
                    # Fall back to default parser if XML parsing fails
                    logger.warning(f"XML parsing failed for {filename}, falling back to {self.parser}")
                    soup = BeautifulSoup(content, self.parser)
                # Catch potential FeatureNotFound errors if 'xml' feature isn't available
                except FeatureNotFound as e:
                     logger.error(f"BeautifulSoup XML feature not found: {e}. Ensure lxml is installed.")
                     raise RuntimeError(f"Required XML parsing feature not available.") from e
            else:
                # Use configured HTML parser for HTML files
                soup = BeautifulSoup(content, self.parser)
        except Exception as e:
            # Log the specific exception type and message
            logger.exception(f"Failed to parse content for {filename} with parser {self.parser}. Original error: {type(e).__name__}: {e}")
            raise RuntimeError(f"Failed to parse document content: {str(e)}") from e
        
        # Extract metadata
        doc_metadata = {}
        if self.extract_metadata:
            doc_metadata = hp_utils.extract_html_metadata(soup)
        
        # Add file stats (always)
        metadata = {
            "file_name": filename,
            "file_type": "html",
            **doc_metadata # Merge extracted metadata
        }
        
        if isinstance(file_path, Path): # Only get stats for local files
            metadata["file_stats"] = self.get_stats(file_path)
        
        # Clean the document
        hp_utils.clean_soup(soup, 
                            self.remove_comments, 
                            self.remove_scripts, 
                            self.remove_styles)
        
        # Extract and format the text
        text = hp_utils.extract_formatted_text(soup, self.preserve_links)
        
        return text, metadata
