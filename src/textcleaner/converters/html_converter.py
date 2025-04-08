"""
HTML and XML document converter

This module provides functionality to convert HTML and XML documents to clean text
while preserving the semantic structure of the document.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from textcleaner.converters.base import BaseConverter


class HTMLConverter(BaseConverter):
    """Converter for HTML and XML documents.
    
    This converter uses BeautifulSoup to parse HTML and XML documents and
    extract meaningful content while preserving the document structure.
    It handles both local files and remote URLs.
    """

    def __init__(self, config=None):
        """Initialize the HTML converter.
        
        Args:
            config: Optional configuration for the converter.
        """
        super().__init__(config)
        
        # Define the supported file extensions
        self.supported_extensions = [".html", ".htm", ".xhtml", ".xml"]
        
        # Configure parsing options from config
        self.parser = self.config.get("converters.html.parser", "html.parser")
        self.remove_comments = self.config.get("converters.html.remove_comments", True)
        self.remove_scripts = self.config.get("converters.html.remove_scripts", True)
        self.remove_styles = self.config.get("converters.html.remove_styles", True)
        self.extract_metadata = self.config.get("converters.html.extract_metadata", True)
        self.preserve_links = self.config.get("converters.html.preserve_links", True)
        
        # Elements that should be treated as block-level (surrounded by newlines)
        self.block_elements = {
            'address', 'article', 'aside', 'blockquote', 'canvas', 'dd', 'div',
            'dl', 'dt', 'fieldset', 'figcaption', 'figure', 'footer', 'form',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hr', 'li', 'main',
            'nav', 'noscript', 'ol', 'p', 'pre', 'section', 'table', 'tfoot',
            'ul', 'video'
        }
    
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
            import requests
            response = requests.get(path_str, timeout=30)
            response.raise_for_status()  # Raise an exception for HTTP errors
            content = response.text
            filename = os.path.basename(urlparse(path_str).path) or "index.html"
        else:
            # For local files, read the content
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            filename = os.path.basename(path_str)
        
        # Parse the HTML/XML content
        # Select appropriate parser based on file extension
        if file_path.suffix.lower() == '.xml':
            # Use XML parser for XML files
            from bs4 import XMLParsedAsHTMLWarning
            import warnings
            
            # Filter out the warning for XML parsed as HTML
            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
            
            # Try to use lxml's XML parser if available, otherwise fall back to html.parser
            try:
                soup = BeautifulSoup(content, features="xml")
            except Exception:
                # Fall back to default parser
                soup = BeautifulSoup(content, self.parser)
        else:
            # Use configured HTML parser for HTML files
            soup = BeautifulSoup(content, self.parser)
        
        # Extract metadata
        metadata = self._extract_metadata(soup, filename)
        
        # Clean the document
        self._clean_document(soup)
        
        # Extract and format the text
        text = self._extract_text(soup)
        
        return text, metadata
    
    def _extract_metadata(self, soup: BeautifulSoup, filename: str) -> Dict[str, Any]:
        """Extract metadata from the HTML/XML document.
        
        Args:
            soup: BeautifulSoup object representing the document.
            filename: Name of the file.
            
        Returns:
            Dictionary containing the extracted metadata.
        """
        metadata = {
            "file_name": filename,
            "file_type": "html",
            "title": None,
            "description": None,
            "keywords": None,
            "author": None,
            "date": None,
        }
        
        if not self.extract_metadata:
            return metadata
        
        # Try to extract the title
        title_tag = soup.find('title')
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)
        
        # Try to extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            property_attr = meta.get('property', '').lower()
            content = meta.get('content', '')
            
            if name == 'description' or property_attr == 'og:description':
                metadata["description"] = content
            elif name == 'keywords':
                metadata["keywords"] = content
            elif name == 'author':
                metadata["author"] = content
            elif name in ['date', 'published_time'] or property_attr == 'article:published_time':
                metadata["date"] = content
        
        return metadata
    
    def _clean_document(self, soup: BeautifulSoup) -> None:
        """Clean the HTML/XML document by removing unwanted elements.
        
        Args:
            soup: BeautifulSoup object representing the document.
        """
        # Remove comments if configured to do so
        if self.remove_comments:
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
        
        # Remove script tags if configured to do so
        if self.remove_scripts:
            for script in soup.find_all('script'):
                script.extract()
        
        # Remove style tags if configured to do so
        if self.remove_styles:
            for style in soup.find_all('style'):
                style.extract()
        
        # Remove other unnecessary elements
        for element in soup.find_all(['nav', 'footer', 'aside']):
            if self._is_likely_navigation_or_footer(element):
                element.extract()
    
    def _is_likely_navigation_or_footer(self, element: Tag) -> bool:
        """Determine if an element is likely navigation or footer content.
        
        Args:
            element: HTML element to check.
            
        Returns:
            True if the element is likely navigation or footer, False otherwise.
        """
        # Check for common class and ID patterns
        element_str = str(element).lower()
        common_patterns = ['nav', 'menu', 'footer', 'bottom', 'copyright', 'sidebar']
        
        # Check if any of the common patterns appear in the class or ID
        if any(pattern in element.get('class', [''])[0].lower() 
               if element.get('class') else False for pattern in common_patterns):
            return True
        
        if element.get('id') and any(pattern in element.get('id').lower() 
                                    for pattern in common_patterns):
            return True
        
        # Check if it contains mostly links
        links = element.find_all('a')
        total_text_length = len(element.get_text(strip=True))
        
        if total_text_length > 0:
            link_text_length = sum(len(link.get_text(strip=True)) for link in links)
            link_ratio = link_text_length / total_text_length
            
            # If more than 70% of the text is in links, it's likely navigation
            if link_ratio > 0.7 and len(links) > 3:
                return True
        
        return False
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract and format text from the HTML/XML document.
        
        Args:
            soup: BeautifulSoup object representing the document.
            
        Returns:
            Extracted and formatted text.
        """
        # Extract the main content area if possible
        main_content = soup.find('main') or soup.find('article') or soup.find('div', {'id': 'content'})
        if not main_content:
            main_content = soup.body or soup
        
        # Build the text content with proper formatting
        lines = []
        self._process_element(main_content, lines, 0)
        
        # Join the lines and normalize whitespace
        text = '\n'.join(lines)
        
        # Clean up excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def _process_element(self, element: Union[Tag, NavigableString], lines: List[str], 
                         heading_level: int) -> None:
        """Process an HTML element recursively and extract its text.
        
        Args:
            element: BeautifulSoup element to process.
            lines: List of text lines to append to.
            heading_level: Current heading level for proper Markdown formatting.
        """
        if isinstance(element, NavigableString):
            text = element.strip()
            if text:
                lines.append(text)
            return
        
        tag_name = element.name
        
        # Process headings
        if tag_name and tag_name.startswith('h') and len(tag_name) == 2:
            try:
                level = int(tag_name[1])
                if 1 <= level <= 6:
                    text = element.get_text(strip=True)
                    if text:
                        lines.append('')
                        lines.append('#' * level + ' ' + text)
                        lines.append('')
                    return
            except ValueError:
                pass
        
        # Process lists
        if tag_name == 'ul' or tag_name == 'ol':
            lines.append('')
            
            for i, li in enumerate(element.find_all('li', recursive=False)):
                prefix = '* ' if tag_name == 'ul' else f"{i+1}. "
                li_text = li.get_text(strip=True)
                if li_text:
                    lines.append(prefix + li_text)
            
            lines.append('')
            return
        
        # Process links
        if tag_name == 'a' and self.preserve_links:
            text = element.get_text(strip=True)
            href = element.get('href')
            if text and href:
                lines.append(f"[{text}]({href})")
                return
        
        # Process tables
        if tag_name == 'table':
            self._process_table(element, lines)
            return
        
        # Process other elements
        if tag_name in self.block_elements:
            # Add a new line before block elements
            if lines and lines[-1]:
                lines.append('')
        
        # Recursively process child elements
        for child in element.children:
            self._process_element(child, lines, heading_level)
        
        if tag_name in self.block_elements:
            # Add a new line after block elements
            if lines and lines[-1]:
                lines.append('')
    
    def _process_table(self, table: Tag, lines: List[str]) -> None:
        """Process an HTML table and convert it to Markdown format.
        
        Args:
            table: BeautifulSoup table element.
            lines: List of text lines to append to.
        """
        rows = table.find_all('tr')
        if not rows:
            return
        
        lines.append('')
        
        # Process header row
        header_cells = rows[0].find_all(['th', 'td'])
        if header_cells:
            header_line = '| ' + ' | '.join(cell.get_text(strip=True) for cell in header_cells) + ' |'
            lines.append(header_line)
            
            # Add the separator row
            separator_line = '| ' + ' | '.join(['---'] * len(header_cells)) + ' |'
            lines.append(separator_line)
        
        # Process data rows
        for row in rows[1:] if header_cells else rows:
            cells = row.find_all('td')
            if cells:
                data_line = '| ' + ' | '.join(cell.get_text(strip=True) for cell in cells) + ' |'
                lines.append(data_line)
        
        lines.append('')
