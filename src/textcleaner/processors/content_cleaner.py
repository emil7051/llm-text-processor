"""Processor for cleaning content."""

# import re # Removed unused import
# import unicodedata # Removed unused import
from typing import Any, Dict, Optional

from .base import BaseProcessor
from textcleaner.utils import content_cleaning as cc_utils

class ContentCleaner(BaseProcessor):
    """Processor for cleaning content.
    
    Removes extraneous content like headers, footers, page numbers,
    and cleans whitespace, unicode, duplicates, and boilerplate.
    """
    
    def __init__(self,
                 remove_headers_footers: bool,
                 remove_page_numbers: bool, # Keep param for config compatibility
                 remove_watermarks: bool, # Keep param for config compatibility
                 clean_whitespace: bool,
                 normalize_unicode: bool,
                 remove_boilerplate: bool,
                 remove_duplicate_content: bool,
                 remove_irrelevant_metadata: bool, # Keep param for config compatibility
                 merge_short_paragraphs: bool):
        """Initialize the content cleaner."""
        self.remove_headers_footers = remove_headers_footers
        self.remove_page_numbers = remove_page_numbers # Unused member (logic handled by remove_headers_footers)
        # self.remove_watermarks = remove_watermarks # Unused member
        self.clean_whitespace = clean_whitespace
        self.normalize_unicode = normalize_unicode
        self.remove_boilerplate = remove_boilerplate
        self.remove_duplicate_content = remove_duplicate_content
        # self.remove_irrelevant_metadata = remove_irrelevant_metadata # Unused member
        self.merge_short_paragraphs = merge_short_paragraphs
        
    def process(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Apply all configured cleaning steps to the content."""
        if not content:
            return content
            
        processed_content = content
        
        # Apply header/footer removal (also handles page numbers)
        if self.remove_headers_footers:
            processed_content = cc_utils.remove_headers_footers(processed_content)
        
        # Removed confusing conditional block for remove_page_numbers as it's handled above
        # if self.remove_page_numbers and not self.remove_headers_footers:
        #     pass 

        if self.remove_duplicate_content:
            processed_content = cc_utils.remove_duplicates(processed_content)
        
        if self.remove_boilerplate:
            processed_content = cc_utils.remove_boilerplate_text(processed_content)
        
        if self.clean_whitespace:
            processed_content = cc_utils.clean_whitespace(processed_content)
        
        if self.merge_short_paragraphs:
            processed_content = cc_utils.merge_short_paragraphs(processed_content)
        
        if self.normalize_unicode:
            processed_content = cc_utils.normalize_unicode(processed_content)
        
        # Placeholder comments for watermark/metadata removal logic removed

        return processed_content.strip() # Return stripped content 