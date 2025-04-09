"""Module for simplifying vocabulary using WordNet."""

import logging
import re
from typing import List, Optional

try:
    import nltk
    from nltk.corpus import wordnet
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

class WordNetSimplifier:
    """Simplify complex vocabulary using WordNet.
    
    This class uses NLTK's WordNet to find simpler synonyms for complex words
    in the text, helping to reduce token usage by using more common words.
    """
    
    def __init__(self, min_word_length: int = 5, download_resources: bool = True):
        """Initialize the WordNet simplifier.
        
        Args:
            min_word_length: Minimum word length to consider for simplification
            download_resources: Whether to download required NLTK resources
        """
        self.logger = logging.getLogger(__name__)
        self.min_word_length = min_word_length
        
        if not NLTK_AVAILABLE:
            self.logger.warning("NLTK is not available, WordNetSimplifier will not work")
            return
            
        # Download required NLTK resources if needed
        if download_resources:
            self._download_nltk_resources()
    
    def _download_nltk_resources(self):
        """Download required NLTK resources."""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('wordnet', quiet=True)
            # No need to download punkt_tab, it's not a standard resource
            self.logger.info("NLTK resources downloaded successfully")
        except Exception as e:
            self.logger.warning(f"Failed to download NLTK resources: {str(e)}")
    
    def _get_synonyms(self, word: str) -> List[str]:
        """Get synonyms for a word from WordNet.
        
        Args:
            word: Word to find synonyms for
            
        Returns:
            List of synonyms, sorted by commonality (most common first)
        """
        if not NLTK_AVAILABLE:
            return []
            
        synonyms = set()
        
        # Find all synsets for the word
        synsets = wordnet.synsets(word)
        
        # Collect all lemmas (word forms) from all synsets
        for synset in synsets:
            for lemma in synset.lemmas():
                synonym = lemma.name().replace('_', ' ')
                if synonym != word and len(synonym) < len(word):
                    synonyms.add(synonym)
        
        # Sort synonyms by length (shorter words are typically simpler)
        return sorted(list(synonyms), key=len)
    
    def _is_complex_word(self, word: str) -> bool:
        """Check if a word is complex enough to be simplified.
        
        Args:
            word: Word to check
            
        Returns:
            True if the word is complex, False otherwise
        """
        # Skip short words
        if len(word) < self.min_word_length:
            return False
            
        # Skip words with special characters or numbers
        if not word.isalpha():
            return False
            
        # Skip capitalized words (names, proper nouns)
        if word[0].isupper() and word[1:].islower():
            return False
            
        return True
    
    def simplify(self, text: str) -> str:
        """Simplify complex vocabulary in text.
        
        Args:
            text: Text to simplify
            
        Returns:
            Text with complex words replaced by simpler synonyms
        """
        if not NLTK_AVAILABLE or not text:
            return text
            
        try:
            # Simple word tokenization without relying on nltk tokenizers
            # Split by whitespace and punctuation
            words = re.findall(r'\b\w+\b', text)
            simplified_words = []
            
            for word in words:
                if self._is_complex_word(word):
                    synonyms = self._get_synonyms(word.lower())
                    if synonyms:
                        # Use the first (shortest) synonym
                        simplified_words.append(synonyms[0])
                    else:
                        simplified_words.append(word)
                else:
                    simplified_words.append(word)
            
            # Reconstruct text while preserving punctuation and spacing
            simplified_text = text
            
            # Replace words with their simplified versions, preserving case
            for i, original_word in enumerate(words):
                if i < len(simplified_words) and original_word.lower() != simplified_words[i].lower():
                    # Preserve capitalization
                    replacement = simplified_words[i]
                    if original_word[0].isupper():
                        replacement = replacement[0].upper() + replacement[1:]
                    
                    # Replace whole word with word boundaries
                    pattern = r'\b' + re.escape(original_word) + r'\b'
                    simplified_text = re.sub(pattern, replacement, simplified_text, count=1)
            
            return simplified_text
            
        except Exception as e:
            self.logger.warning(f"Error in vocabulary simplification: {str(e)}")
            return text  # Return original text on error 