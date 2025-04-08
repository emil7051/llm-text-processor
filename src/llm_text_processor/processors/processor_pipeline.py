"""Processing pipeline for text content."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from llm_text_processor.config.config_manager import ConfigManager


class BaseProcessor(ABC):
    """Base class for all text processors.
    
    Each processor is responsible for a specific aspect of text processing,
    such as structure preservation, content cleaning, or optimization.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the processor.
        
        Args:
            config: Configuration manager instance.
        """
        self.config = config or ConfigManager()
        
    @abstractmethod
    def process(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Process the content.
        
        Args:
            content: The content to process.
            metadata: Optional metadata about the content.
            
        Returns:
            Processed content.
        """
        pass


class StructureProcessor(BaseProcessor):
    """Processor for preserving document structure.
    
    This processor ensures that structural elements like headings,
    lists, tables, etc. are properly preserved.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the structure processor.
        
        Args:
            config: Configuration manager instance.
        """
        super().__init__(config)
        # Get structure-specific configuration
        self.preserve_headings = self.config.get("structure.preserve_headings", True)
        self.preserve_lists = self.config.get("structure.preserve_lists", True)
        self.preserve_tables = self.config.get("structure.preserve_tables", True)
        self.preserve_links = self.config.get("structure.preserve_links", True)
        
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
            
        # Structure preservation is mostly handled by the converters directly,
        # but we can do some additional post-processing here if needed
        processed_content = content
        
        # Additional structure processing can be implemented here
        # This could involve things like standardizing heading formats,
        # ensuring consistent list formatting, etc.
        
        return processed_content


class ContentCleaner(BaseProcessor):
    """Processor for cleaning content.
    
    This processor removes extraneous content like headers, footers,
    page numbers, watermarks, etc.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the content cleaner.
        
        Args:
            config: Configuration manager instance.
        """
        super().__init__(config)
        # Get cleaning-specific configuration
        self.remove_headers_footers = self.config.get("cleaning.remove_headers_footers", True)
        self.remove_page_numbers = self.config.get("cleaning.remove_page_numbers", True)
        self.remove_watermarks = self.config.get("cleaning.remove_watermarks", True)
        self.clean_whitespace = self.config.get("cleaning.clean_whitespace", True)
        self.normalize_unicode = self.config.get("cleaning.normalize_unicode", True)
        self.remove_boilerplate = self.config.get("cleaning.remove_boilerplate", True)
        self.remove_duplicate_content = self.config.get("cleaning.remove_duplicate_content", True)
        
    def process(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Process the content to clean it.
        
        Removes extraneous content and cleans up formatting.
        
        Args:
            content: The content to process.
            metadata: Optional metadata about the content.
            
        Returns:
            Cleaned content.
        """
        if not content:
            return content
            
        processed_content = content
        
        # Clean whitespace
        if self.clean_whitespace:
            import re
            # Remove excessive whitespace (more than 2 newlines)
            processed_content = re.sub(r'\n{3,}', '\n\n', processed_content)
            # Remove trailing whitespace on lines
            processed_content = re.sub(r' +$', '', processed_content, flags=re.MULTILINE)
            # Normalize spaces (more than 1 space becomes 1 space)
            processed_content = re.sub(r' {2,}', ' ', processed_content)
        
        # Normalize Unicode
        if self.normalize_unicode:
            import unicodedata
            processed_content = unicodedata.normalize('NFKC', processed_content)
        
        # Additional cleaning will be implemented in future versions
        # This could involve things like removing headers/footers,
        # detecting and removing watermarks, etc.
        
        return processed_content


class ContentOptimizer(BaseProcessor):
    """Processor for optimizing content for token efficiency.
    
    This processor performs optimizations to reduce token usage
    while preserving essential information.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the content optimizer.
        
        Args:
            config: Configuration manager instance.
        """
        super().__init__(config)
        # Get optimization-specific configuration
        self.abbreviate_common_terms = self.config.get("optimization.abbreviate_common_terms", False)
        self.simplify_citations = self.config.get("optimization.simplify_citations", True)
        self.simplify_references = self.config.get("optimization.simplify_references", True)
        self.simplify_urls = self.config.get("optimization.simplify_urls", False)
        self.max_line_length = self.config.get("optimization.max_line_length", 80)
        
    def process(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Process the content to optimize it.
        
        Performs optimizations to reduce token usage.
        
        Args:
            content: The content to process.
            metadata: Optional metadata about the content.
            
        Returns:
            Optimized content.
        """
        if not content:
            return content
            
        processed_content = content
        
        # Simplify citations
        if self.simplify_citations:
            import re
            # Replace citation patterns with simplified versions
            # Example: (Smith et al., 2020) -> [Smith 2020]
            processed_content = re.sub(
                r'\(([^)]+?et al\.,?\s+\d{4}[^)]*)\)', 
                r'[\1]', 
                processed_content
            )
        
        # Optimize line length
        if self.max_line_length > 0:
            import textwrap
            lines = processed_content.split('\n')
            wrapped_lines = []
            
            for line in lines:
                # Don't wrap headings, list items, table rows, etc.
                if (
                    line.startswith('#') or 
                    line.startswith('* ') or 
                    line.startswith('- ') or 
                    line.startswith('| ') or
                    not line.strip()
                ):
                    wrapped_lines.append(line)
                else:
                    # Wrap text to max line length
                    wrapped = textwrap.fill(
                        line, 
                        width=self.max_line_length,
                        break_long_words=False,
                        break_on_hyphens=True
                    )
                    wrapped_lines.append(wrapped)
            
            processed_content = '\n'.join(wrapped_lines)
        
        # Additional optimization will be implemented in future versions
        
        return processed_content


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
        self.config = config or ConfigManager()
        self.processors: List[BaseProcessor] = []
        self._setup_processors()
        
    def _setup_processors(self) -> None:
        """Set up the processors based on configuration."""
        cleaning_level = self.config.get("processing.cleaning_level", "standard")
        
        # Add structure processor
        self.processors.append(StructureProcessor(self.config))
        
        # Add content cleaner
        self.processors.append(ContentCleaner(self.config))
        
        # Add content optimizer
        if cleaning_level in ["standard", "aggressive"]:
            self.processors.append(ContentOptimizer(self.config))
            
        # Additional processors can be added here based on configuration
        
    def process(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Process content through all processors in the pipeline.
        
        Args:
            content: The content to process.
            metadata: Optional metadata about the content.
            
        Returns:
            Fully processed content.
        """
        processed_content = content
        
        for processor in self.processors:
            processed_content = processor.process(processed_content, metadata)
            
        return processed_content
