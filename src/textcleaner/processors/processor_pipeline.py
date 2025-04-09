"""Processing pipeline for text content."""

# from abc import ABC, abstractmethod # Removed unused imports
from typing import Any, Dict, List, Optional
import time

from textcleaner.config.config_manager import ConfigManager
from textcleaner.utils.logging_config import get_logger # Added logger import

# Import base and concrete processors
from .base import BaseProcessor # Import from the new base.py
from .structure_processor import StructureProcessor
from .content_cleaner import ContentCleaner
from .content_optimizer import ContentOptimizer

# BaseProcessor class definition removed from here

class ProcessorPipeline:
    """Chain of processors to clean and structure content.
    
    Manages a pipeline of processors that are applied in sequence to
    transform raw content into clean, well-structured, token-efficient text.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the processor pipeline.
        
        Args:
            config: Configuration manager instance.
        """
        self.logger = get_logger(__name__) # Add logger initialization
        self.config = config or ConfigManager()
        self.processors: List[BaseProcessor] = []
        self._setup_processors()
        
    def _setup_processors(self) -> None:
        """Set up the processors based on configuration."""
        # Ensure the list is clear before setting up
        self.processors = [] 
        
        # --- Add Structure Processor ---        
        if self.config.get("processing.enable_structure_processor", True):
             self.processors.append(StructureProcessor(
                 preserve_headings=self.config.get("structure.preserve_headings", True),
                 preserve_lists=self.config.get("structure.preserve_lists", True),
                 preserve_tables=self.config.get("structure.preserve_tables", True),
                 preserve_links=self.config.get("structure.preserve_links", True)
             ))
        
        # --- Add Content Cleaner --- 
        if self.config.get("processing.enable_content_cleaner", True):
            self.processors.append(ContentCleaner(
                remove_headers_footers=self.config.get("cleaning.remove_headers_footers", True),
                remove_page_numbers=self.config.get("cleaning.remove_page_numbers", True),
                remove_watermarks=self.config.get("cleaning.remove_watermarks", True),
                clean_whitespace=self.config.get("cleaning.clean_whitespace", True),
                normalize_unicode=self.config.get("cleaning.normalize_unicode", True),
                remove_boilerplate=self.config.get("cleaning.remove_boilerplate", True),
                remove_duplicate_content=self.config.get("cleaning.remove_duplicate_content", True),
                remove_irrelevant_metadata=self.config.get("cleaning.remove_irrelevant_metadata", True),
                merge_short_paragraphs=self.config.get("cleaning.merge_short_paragraphs", True),
                remove_footnotes=self.config.get("cleaning.remove_footnotes", False),
                join_paragraph_lines=self.config.get("cleaning.join_paragraph_lines", True)
            ))
        
        # --- Add Content Optimizer --- 
        # Conditionally add optimizer based on config flag and cleaning level
        cleaning_level = self.config.get("processing.cleaning_level", "standard")
        if self.config.get("processing.enable_optimizer", True) and cleaning_level != "minimal": 
            self.processors.append(ContentOptimizer(
                abbreviate_common_terms=self.config.get("optimization.abbreviate_common_terms", False),
                simplify_citations=self.config.get("optimization.simplify_citations", True),
                simplify_references=self.config.get("optimization.simplify_references", True),
                simplify_urls=self.config.get("optimization.simplify_urls", False),
                max_line_length=self.config.get("optimization.max_line_length", 0), # Default 0 (no wrap)
                optimize_temporal=self.config.get("optimization.optimize_temporal", False),
                use_stanford_nlp=self.config.get("optimization.use_stanford_nlp", False),
                simplify_vocabulary=self.config.get("optimization.simplify_vocabulary", False),
                min_word_length=self.config.get("optimization.min_word_length", 5),
                download_nltk_resources=self.config.get("optimization.download_nltk_resources", True),
                condense_repetitive_patterns=self.config.get("optimization.condense_repetitive_patterns", True),
                remove_redundant_phrases=self.config.get("optimization.remove_redundant_phrases", True),
                remove_excessive_punctuation=self.config.get("optimization.remove_excessive_punctuation", True),
                domain_abbreviations=self.config.get("optimization.domain_abbreviations", [])
            ))
            
        # TODO: Consider a more dynamic way to load/configure processors based on config.
        
    def process(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Process content through all enabled processors in the pipeline.
        
        Args:
            content: The content to process.
            metadata: Optional metadata about the content.
            
        Returns:
            Fully processed content.
        """
        processed_content = content
        # Log initial content length
        self.logger.debug(f"Initial content length: {len(processed_content)}")
        
        for processor in self.processors:
            processor_name = processor.__class__.__name__
            start_time = time.time()
            # Log content length before processing
            self.logger.debug(f"Before {processor_name}: length={len(processed_content)}")
            processed_content = processor.process(processed_content, metadata)
            end_time = time.time()
            # Log content length after processing and time taken
            self.logger.debug(f"After {processor_name}: length={len(processed_content)}, took {end_time - start_time:.4f}s")
            
        return processed_content
