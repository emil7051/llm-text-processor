"""Processor for preserving document structure."""

import re
from typing import Any, Dict, Optional

from .base import BaseProcessor
from textcleaner.utils import structure_operations as so_utils

class StructureProcessor(BaseProcessor):
    """Processor for preserving document structure.
    
    This processor ensures that structural elements like headings,
    lists, tables, etc. are properly preserved.
    """
    
    def __init__(self, 
                 preserve_headings: bool,
                 preserve_lists: bool,
                 preserve_tables: bool,
                 preserve_links: bool):
        """Initialize the structure processor.
        
        Args:
            preserve_headings: Whether to preserve headings.
            preserve_lists: Whether to preserve lists.
            preserve_tables: Whether to preserve tables.
            preserve_links: Whether to preserve links.
        """
        self.preserve_headings = preserve_headings
        self.preserve_lists = preserve_lists
        self.preserve_tables = preserve_tables # Note: Not used in process() currently
        self.preserve_links = preserve_links # Note: Not used in process() currently
        
    def process(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Process the content to preserve structure.
        
        Ensures that document structure is maintained in a clean,
        standardized format.
        
        Args:
            content: The content to process.
            metadata: Optional metadata about the content.
            
        Returns:
            Content with preserved structure.
        """
        if not content:
            return content
            
        processed_content = content
        
        # Only standardize if preserve_lists is NOT set to True explicitly
        # This maintains original list markers if preservation is desired.
        if not self.preserve_lists:
            processed_content = so_utils.standardize_lists(processed_content)

        if self.preserve_headings:
            processed_content = so_utils.format_headings(processed_content)

        # Placeholder for future table/link preservation logic
        # if self.preserve_tables:
        #     processed_content = self._preserve_tables(processed_content)
        # if self.preserve_links:
        #     processed_content = self._preserve_links(processed_content, metadata)

        return processed_content

    # def _standardize_lists(self, content: str) -> str:
    #     """Standardize list item markers (e.g., bullets, dashes) to use Markdown asterisks."""
    #     # Pattern for various bullet point symbols
    #     bullet_pattern = r'^\s*[•·⦿⦾⦿⁃⁌⁍◦▪▫◘◙◦➢➣➤●○◼◻►▻▷▹➔→⇒⟹⟾⟶⇝⇢⤷⟼⟿⤳⤻⤔⟴]+ *'
    #     content = re.sub(bullet_pattern, '* ', content, flags=re.MULTILINE)
    #     # Pattern for dash/hyphen bullet points
    #     dash_pattern = r'^\s*[-–—] *'
    #     content = re.sub(dash_pattern, '* ', content, flags=re.MULTILINE)
    #     return content

    # def _format_headings(self, content: str) -> str:
    #     """Identify potential headings and format them using Markdown."""
    #     lines = content.split('\n')
    #     potential_headings_indices = []
    #     for i, line in enumerate(lines):
    #         line_stripped = line.strip()
    #         
    #         # Skip lines already formatted or empty or list items
    #         if not line_stripped or line_stripped.startswith(('#', '*', '-')):
    #             continue
    #             
    #         # Potential heading: relatively short line, not list item
    #         if len(line_stripped) < 80:
    #             # Check context: preceded or followed by an empty line
    #             prev_line_empty = (i == 0) or (i > 0 and not lines[i-1].strip())
    #             next_line_empty = (i == len(lines) - 1) or (i+1 < len(lines) and not lines[i+1].strip())
    #             
    #             # Heuristic: require surrounding empty lines or be short & preceded by empty
    #             if (prev_line_empty and next_line_empty) or (prev_line_empty and len(line_stripped) < 60):
    #                 potential_headings_indices.append(i)
    #
    #     # Apply heading formats after identifying all potential candidates
    #     if potential_headings_indices:
    #         temp_lines = list(lines) # Work on a copy
    #         for i in potential_headings_indices:
    #             line_stripped = temp_lines[i].strip()
    #             # Determine header level based on length
    #             if len(line_stripped) < 25:
    #                 lines[i] = f"## {line_stripped}"
    #             elif len(line_stripped) < 60:
    #                 lines[i] = f"### {line_stripped}"
    #             # Note: Longer lines identified as potential headings are not modified
    #         
    #         content = '\n'.join(lines)
    #     
    #     return content 