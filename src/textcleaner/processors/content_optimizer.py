"""Processor for optimizing content for token efficiency."""

# import re # Removed unused import
# import textwrap # Removed unused import
from typing import Any, Dict, List, Optional

from .base import BaseProcessor
from textcleaner.utils.logging_config import get_logger
from textcleaner.utils import content_optimizations as co_utils

# Conditional imports for optimizers
try:
    from textcleaner.utils.replacement_dictionaries import TextSimplifier, DomainTextOptimizer
    _replacements_available = True
except ImportError:
    _replacements_available = False

try:
    from textcleaner.utils.word_simplifier import WordNetSimplifier
    _wordnet_available = True
except ImportError:
    _wordnet_available = False


class ContentOptimizer(BaseProcessor):
    """Processor for optimizing content for token efficiency.
    
    Performs optimizations like abbreviation, simplification of citations/URLs,
    vocabulary simplification, and pattern condensation.
    """
    
    def __init__(self, 
                 abbreviate_common_terms: bool,
                 simplify_citations: bool,
                 simplify_references: bool, # Note: Not used
                 simplify_urls: bool,
                 max_line_length: int,
                 min_word_length: int,
                 condense_repetitive_patterns: bool,
                 remove_redundant_phrases: bool,
                 remove_excessive_punctuation: bool,
                 domain_abbreviations: List[str] = [],
                 simplify_vocabulary: bool = True,
                 ):
        """Initialize the content optimizer."""
        self.logger = get_logger(__name__)
        
        # Store config flags
        self.config = {
            "abbreviate_common_terms": abbreviate_common_terms,
            "simplify_citations": simplify_citations,
            # "simplify_references": simplify_references, # Removed unused config item
            "simplify_urls": simplify_urls,
            "max_line_length": max_line_length,
            "condense_repetitive_patterns": condense_repetitive_patterns,
            "remove_redundant_phrases": remove_redundant_phrases,
            "remove_excessive_punctuation": remove_excessive_punctuation,
        }

        # Setup helper utilities based on availability and config
        self.text_simplifier = None
        self.domain_optimizer = None
        self.word_simplifier = None
        
        # Initialize replacement tools if available
        if _replacements_available:
            self.text_simplifier = TextSimplifier()
            if domain_abbreviations:
                self.domain_optimizer = DomainTextOptimizer(domains=domain_abbreviations)
        else:
            self.logger.warning("Replacement dictionaries not available, cannot use TextSimplifier or DomainTextOptimizer.")
                
        if simplify_vocabulary:
            if _wordnet_available:
                self.word_simplifier = WordNetSimplifier(
                    min_word_length=min_word_length
                )
                self.logger.debug("WordNetSimplifier enabled.")
            else:
                self.logger.warning("NLTK not available, cannot simplify vocabulary (simplify_vocabulary=True).")
        else:
            self.word_simplifier = None
            self.logger.debug("Vocabulary simplification disabled by configuration (simplify_vocabulary=False).")
        
    def process(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Apply all configured optimization steps to the content."""
        if not content:
            return content
            
        processed_content = content
        
        # Apply optimizations step-by-step
        if self.text_simplifier and self.config.get("abbreviate_common_terms"):
            processed_content = self.text_simplifier.simplify(processed_content)
        if self.domain_optimizer:
            processed_content = self.domain_optimizer.optimize(processed_content)
        if self.word_simplifier:
            processed_content = self.word_simplifier.simplify(processed_content)
            
        if self.config["remove_redundant_phrases"]:
            processed_content = co_utils.remove_redundant_phrases(processed_content)
        if self.config["condense_repetitive_patterns"]:
            processed_content = co_utils.condense_repetitive_patterns(processed_content)
        if self.config["remove_excessive_punctuation"]:
            processed_content = co_utils.remove_excessive_punctuation(processed_content)
        if self.config["simplify_citations"]:
            processed_content = co_utils.simplify_citations(processed_content)
        if self.config["simplify_urls"]:
            processed_content = co_utils.simplify_urls(processed_content)
        if self.config["max_line_length"] > 0:
            processed_content = co_utils.optimize_line_length(processed_content, self.config["max_line_length"])
        
        return processed_content 