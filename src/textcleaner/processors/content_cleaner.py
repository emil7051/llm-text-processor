"""Processor for cleaning content."""

import re
import unicodedata
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
                 remove_page_numbers: bool,
                 remove_watermarks: bool, # Note: Watermark removal not implemented
                 clean_whitespace: bool,
                 normalize_unicode: bool,
                 remove_boilerplate: bool,
                 remove_duplicate_content: bool,
                 remove_irrelevant_metadata: bool, # Note: Metadata removal not implemented
                 merge_short_paragraphs: bool):
        """Initialize the content cleaner."""
        self.remove_headers_footers = remove_headers_footers
        self.remove_page_numbers = remove_page_numbers
        self.remove_watermarks = remove_watermarks
        self.clean_whitespace = clean_whitespace
        self.normalize_unicode = normalize_unicode
        self.remove_boilerplate = remove_boilerplate
        self.remove_duplicate_content = remove_duplicate_content
        self.remove_irrelevant_metadata = remove_irrelevant_metadata
        self.merge_short_paragraphs = merge_short_paragraphs
        
    def process(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Apply all configured cleaning steps to the content."""
        if not content:
            return content
            
        processed_content = content
        
        # Apply header/footer removal ONLY if configured
        if self.remove_headers_footers:
            processed_content = cc_utils.remove_headers_footers(processed_content)
        
        # Apply page number removal ONLY if configured (can overlap with above)
        # Note: Current remove_headers_footers might already remove simple page numbers
        if self.remove_page_numbers and not self.remove_headers_footers:
             # If header/footer removal wasn't run, specifically target page numbers
             # Add a specific page number removal function if needed, or rely on 
             # remove_headers_footers patterns being sufficient even when called selectively.
             # For now, assume remove_headers_footers covers page# patterns
             # If remove_headers_footers is True, page numbers are handled there.
             # If remove_headers_footers is False, but remove_page_numbers is True,
             # we might need a separate call here. Let's refine remove_headers_footers later if needed.
             pass # Placeholder - current remove_headers_footers handles page# patterns

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
        
        # Placeholder for watermark/metadata removal logic
        # if self.remove_watermarks:
        #     processed_content = self._remove_watermarks(processed_content)
        # if self.remove_irrelevant_metadata:
        #     processed_content = self._remove_metadata_lines(processed_content, metadata)

        return processed_content.strip() # Return stripped content 