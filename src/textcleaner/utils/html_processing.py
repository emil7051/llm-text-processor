"""Utilities for processing parsed HTML/XML content using BeautifulSoup."""

from typing import Any, Dict, Optional, Union, List, Tuple
import re
import logging

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from textcleaner.utils.logging_config import get_logger

logger = get_logger(__name__)

# Elements that should be treated as block-level (surrounded by newlines)
# Moved here as it relates to processing logic.
BLOCK_ELEMENTS = {
    'address', 'article', 'aside', 'blockquote', 'canvas', 'dd', 'div',
    'dl', 'dt', 'fieldset', 'figcaption', 'figure', 'footer', 'form',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hr', 'li', 'main',
    'nav', 'noscript', 'ol', 'p', 'pre', 'section', 'table', 'tfoot',
    'ul', 'video'
}

def extract_html_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extracts metadata (title, meta tags) from a BeautifulSoup object.

    Args:
        soup: BeautifulSoup object representing the document.

    Returns:
        Dictionary containing the extracted metadata.
    """
    metadata = {
        "title": None,
        "description": None,
        "keywords": None,
        "author": None,
        "date": None,
    }

    # Try to extract the title
    title_tag = soup.find('title')
    if title_tag:
        metadata["title"] = title_tag.get_text(strip=True)

    # Try to extract meta tags
    for meta in soup.find_all('meta'):
        name = meta.get('name', '').lower()
        property_attr = meta.get('property', '').lower()
        content = meta.get('content', '')

        if not content:
            continue

        if name == 'description' or property_attr == 'og:description':
            if not metadata["description"]: # Prefer name over property
                metadata["description"] = content
        elif name == 'keywords':
             if not metadata["keywords"]:
                 metadata["keywords"] = content
        elif name == 'author':
             if not metadata["author"]:
                 metadata["author"] = content
        elif name in ['date', 'published_time'] or property_attr == 'article:published_time':
             if not metadata["date"]:
                 metadata["date"] = content

    return metadata

def clean_soup(soup: BeautifulSoup, 
               remove_comments: bool, 
               remove_scripts: bool, 
               remove_styles: bool) -> None:
    """Cleans the BeautifulSoup object by removing unwanted elements in place.

    Args:
        soup: BeautifulSoup object representing the document.
        remove_comments: Whether to remove HTML comments.
        remove_scripts: Whether to remove <script> tags.
        remove_styles: Whether to remove <style> tags.
    """
    # Remove comments if configured
    if remove_comments:
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
    
    # Remove script tags if configured
    if remove_scripts:
        for script in soup.find_all('script'):
            script.extract()
    
    # Remove style tags if configured
    if remove_styles:
        for style in soup.find_all('style'):
            style.extract()
    
    # Remove common non-content sections (nav, footer, aside)
    # Note: This is a simple approach; more complex heuristics might be needed
    for tag_name in ['nav', 'footer', 'aside']:
        for element in soup.find_all(tag_name):
            element.extract()


# --- Text Extraction and Formatting --- #

def _process_table_to_markdown(table: Tag, lines: List[str]) -> None:
    """Processes an HTML table Tag into Markdown format, appending to lines."""
    rows = table.find_all('tr')
    if not rows:
        return

    lines.append('')
    header_cells = rows[0].find_all(['th', 'td'])
    num_cols = len(header_cells)
    if num_cols == 0:
        return
        
    # Process header
    header_line = '| ' + ' | '.join(cell.get_text(strip=True).replace('|', '\|') for cell in header_cells) + ' |'
    lines.append(header_line)
    separator_line = '| ' + ' | '.join(['---'] * num_cols) + ' |'
    lines.append(separator_line)

    # Process data rows
    for row in rows[1:]:
        cells = row.find_all('td')
        # Ensure the number of cells matches the header
        data_values = [(cell.get_text(strip=True).replace('|', '\|') or ' ') 
                       for cell in cells[:num_cols]]
        # Pad if necessary
        data_values.extend([' '] * (num_cols - len(data_values)))
        data_line = '| ' + ' | '.join(data_values) + ' |'
        lines.append(data_line)

    lines.append('')

def _process_element_recursive(element: Union[Tag, NavigableString], 
                               lines: List[str], 
                               preserve_links: bool) -> None:
    """Recursively processes a BeautifulSoup element to extract formatted text."""
    if isinstance(element, NavigableString):
        text = element.strip()
        # Preserve whitespace within certain tags like <pre>
        if element.parent.name == 'pre':
            text = str(element) # Keep original whitespace
            
        if text: # Append non-empty text
             # Append to the last line if it exists and is not just whitespace
            if lines and lines[-1].strip():
                lines[-1] += text
            else: # Otherwise, start a new line
                lines.append(text)
        return

    tag_name = element.name
    
    # Handle block elements by adding newlines before/after processing children
    is_block = tag_name in BLOCK_ELEMENTS
    if is_block and lines and lines[-1]:
        lines.append('') # Add newline before block element
        
    # --- Specific Tag Handling ---
    if tag_name and tag_name.startswith('h') and len(tag_name) == 2:
        try:
            level = int(tag_name[1])
            if 1 <= level <= 6:
                text = element.get_text(strip=True)
                if text:
                    lines.append('') # Ensure blank line before heading
                    lines.append('#' * level + ' ' + text)
                    # Skip children processing for headings
                    if lines and lines[-1]: # Ensure blank line after heading
                        lines.append('') 
                return # Stop processing this branch
        except ValueError:
            pass # Fall through if not a valid h1-h6 tag

    elif tag_name in ('ul', 'ol'):
        lines.append('') # Blank line before list
        list_items = element.find_all('li', recursive=False)
        for i, li in enumerate(list_items):
            prefix = '* ' if tag_name == 'ul' else f"{i+1}. "
            
            # Process li content into temporary lines
            li_lines = []
            for child in li.children:
                _process_element_recursive(child, li_lines, preserve_links)
            
            # Clean up leading/trailing empty lines from li content
            while li_lines and not li_lines[0].strip():
                li_lines.pop(0)
            while li_lines and not li_lines[-1].strip():
                li_lines.pop()
                
            # Prepend prefix to the first line and add to main lines
            if li_lines:
                li_lines[0] = prefix + li_lines[0].lstrip() # Remove leading space if any
                lines.extend(li_lines)
                
        lines.append('') # Blank line after list
        return # Stop processing this branch

    elif tag_name == 'a' and preserve_links:
        text = element.get_text(strip=True)
        href = element.get('href')
        if text and href:
            # Append link inline
            if lines and lines[-1].strip():
                lines[-1] += f"[{text}]({href})"
            else:
                 lines.append(f"[{text}]({href})")
            # Don't process children of link if we preserved it
            return

    elif tag_name == 'table':
        _process_table_to_markdown(element, lines)
        return # Stop processing this branch
        
    elif tag_name == 'br':
        lines.append('') # Treat <br> as a newline
        return
        
    elif tag_name == 'hr':
        lines.append('\n---\n') # Add markdown horizontal rule
        return
        
    elif tag_name == 'pre':
         lines.append('\n```') # Start code block
         # Process children normally to get text content
         for child in element.children:
            _process_element_recursive(child, lines, preserve_links=False) # Don't format links in code
         lines.append('```\n') # End code block
         return # Stop processing this branch

    # --- General Recursion --- 
    # Recursively process child elements for unhandled tags
    for child in element.children:
        _process_element_recursive(child, lines, preserve_links)

    # Add newline after block element if content was added
    if is_block and lines and lines[-1]:
        lines.append('')

def extract_formatted_text(soup: BeautifulSoup, preserve_links: bool) -> str:
    """Extracts and formats text content from a cleaned BeautifulSoup object.
    
    Args:
        soup: BeautifulSoup object, presumably already cleaned.
        preserve_links: Whether to format links in Markdown.
        
    Returns:
        Formatted text content as a single string.
    """
    # Attempt to find the main content area
    main_content = soup.find('main') or soup.find('article') or soup.find('div', {'id': 'content', 'class': 'content'})
    target_element = main_content if main_content else (soup.body or soup)
    
    lines = []
    _process_element_recursive(target_element, lines, preserve_links)
    
    # Final cleanup of whitespace
    text = '\n'.join(lines)
    text = re.sub(r'\n{3,}', '\n\n', text) # Collapse excessive blank lines
    text = re.sub(r'^\s+|\s+$', '', text) # Trim leading/trailing whitespace
    
    return text 