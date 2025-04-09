"""Temporal expression optimization using Stanford's SUTime."""

from typing import Dict, List, Optional, Tuple
import re
import os
import json
from pathlib import Path
import logging

# Import Stanford NLP libraries conditionally to avoid hard dependency
try:
    from stanfordnlp.server import CoreNLPClient
    STANFORD_AVAILABLE = True
except ImportError:
    STANFORD_AVAILABLE = False


class TemporalExpressionOptimizer:
    """Optimizes temporal expressions in text for token efficiency.
    
    Uses Stanford's SUTime to detect and normalize temporal expressions
    for more efficient token usage.
    
    Example transformations:
    - "on the fifteenth of January" -> "on Jan 15"
    - "at around three o'clock in the afternoon" -> "around 3pm"
    - "during the year two thousand and twenty two" -> "during 2022"
    """
    
    def __init__(self, 
                 use_stanford: bool = True, 
                 custom_patterns: Optional[Dict[str, str]] = None):
        """Initialize the temporal expression optimizer.
        
        Args:
            use_stanford: Whether to use Stanford NLP for advanced processing.
                If False, will fall back to regex-based optimization.
            custom_patterns: Optional dictionary of custom regex patterns
                and their replacements.
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize Stanford CoreNLP if available and requested
        self.use_stanford = use_stanford and STANFORD_AVAILABLE
        self.client = None
        
        if self.use_stanford:
            try:
                # Create a CoreNLP client with SUTime annotator
                self.client = CoreNLPClient(
                    annotators=['tokenize', 'ssplit', 'pos', 'lemma', 'ner', 'sutime'],
                    timeout=30000,
                    memory='4G')
                self.logger.info("Initialized Stanford CoreNLP with SUTime for temporal expression processing")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Stanford CoreNLP: {e}")
                self.use_stanford = False
                
        # Fallback patterns for regex-based optimization
        self.patterns = {
            # Date patterns
            r'on the (\w+)\s+of\s+(\w+)': r'on \2 \1',  # on the fifteenth of January -> on January fifteenth
            r'(\d+)(?:st|nd|rd|th) of (\w+)': r'\2 \1',  # 15th of January -> January 15
            r'(\w+) the (\d+)(?:st|nd|rd|th)': r'\1 \2',  # January the 15th -> January 15
            
            # Time patterns
            r'(\d+) o\'clock in the (morning|afternoon|evening)': lambda m: f"{m.group(1)}{'am' if m.group(2)=='morning' else 'pm'}",
            r'at around (\d+) o\'clock': r'around \1:00',
            r'half past (\d+)': r'\1:30',
            r'quarter past (\d+)': r'\1:15',
            r'quarter to (\d+)': lambda m: f"{int(m.group(1))-1}:45",
            
            # Duration patterns
            r'for a period of (\d+) (\w+)': r'for \1 \2',
            r'over the course of (\d+) (\w+)': r'over \1 \2',
            
            # Temporal reference patterns
            r'at the present moment': r'now',
            r'at this point in time': r'now',
            r'in the near future': r'soon',
            r'up until now': r'until now',
            r'as of yet': r'yet',
            r'prior to this': r'before',
            r'subsequent to this': r'after',
        }
        
        # Add custom patterns if provided
        if custom_patterns:
            self.patterns.update(custom_patterns)
    
    def optimize(self, text: str) -> str:
        """Optimize temporal expressions in text.
        
        Args:
            text: Text to optimize.
            
        Returns:
            Text with optimized temporal expressions.
        """
        if not text:
            return text
            
        # Use Stanford SUTime if available
        if self.use_stanford and self.client:
            try:
                return self._stanford_optimize(text)
            except Exception as e:
                self.logger.warning(f"Stanford SUTime optimization failed: {e}")
                self.logger.info("Falling back to regex-based optimization")
                
        # Fall back to regex-based optimization
        return self._regex_optimize(text)
        
    def _stanford_optimize(self, text: str) -> str:
        """Optimize temporal expressions using Stanford SUTime.
        
        Args:
            text: Text to optimize.
            
        Returns:
            Text with optimized temporal expressions.
        """
        # Process text with CoreNLP to get annotations
        annotated = self.client.annotate(text)
        
        # Extract and process temporal expressions
        result = text
        offset = 0
        
        for sentence in annotated.sentence:
            if hasattr(sentence, 'mentions') and sentence.mentions:
                for mention in sentence.mentions:
                    if mention.hasNormalizedValue:
                        # Get the original text and its position
                        original = mention.originalText
                        start = mention.tokenStartInSentenceInclusive + sentence.tokenOffsetBegin
                        end = mention.tokenEndInSentenceExclusive + sentence.tokenOffsetBegin
                        
                        # Get the normalized value
                        normalized = mention.normalizedNER
                        
                        # Skip if normalization doesn't save tokens
                        if len(normalized) >= len(original):
                            continue
                            
                        # Replace the original with normalized in the result
                        char_start = text.find(original, offset)
                        if char_start >= 0:
                            char_end = char_start + len(original)
                            result = result[:char_start] + normalized + result[char_end:]
                            offset = char_start + len(normalized)
        
        return result
        
    def _regex_optimize(self, text: str) -> str:
        """Optimize temporal expressions using regex patterns.
        
        Args:
            text: Text to optimize.
            
        Returns:
            Text with optimized temporal expressions.
        """
        result = text
        
        # Apply each pattern
        for pattern, replacement in self.patterns.items():
            if callable(replacement):
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            else:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
                
        return result
        
    def __del__(self):
        """Clean up resources."""
        if self.client is not None:
            try:
                self.client.stop()
            except Exception:
                pass 