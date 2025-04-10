"""Module for simplifying vocabulary using WordNet."""

import logging
import re
from typing import List, Optional

try:
    import nltk
    from nltk.corpus import wordnet
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

# Initialize logger
logger = logging.getLogger(__name__)

# Ensure necessary NLTK resources are downloaded automatically
# _ensure_nltk_resources()

class WordNetSimplifier:
    """Simplify complex vocabulary using WordNet.
    
    This class uses NLTK's WordNet to find simpler synonyms for complex words
    in the text, helping to reduce token usage by using more common words.
    """
    
    def __init__(self, min_word_length: int):
        """Initialize the WordNet simplifier.
        
        Args:
            min_word_length: Minimum word length to consider for simplification
        """
        self.min_word_length = min_word_length
        self.lemmatizer = WordNetLemmatizer()
        self._ensure_nltk_resources() # Call resource check during init
        
        if not NLTK_AVAILABLE:
            logger.warning("NLTK is not available, WordNetSimplifier will not work")
            return
    
    def _ensure_nltk_resources(self):
        """Downloads required NLTK resources ('wordnet', 'omw-1.4') if not found."""
        required_resources = ['wordnet', 'omw-1.4'] 
        try:
            for resource in required_resources:
                try:
                    # Use nltk.data.find to check without raising error on first miss
                    nltk.data.find(f'corpora/{resource}')
                    logger.debug(f"NLTK resource '{resource}' found.")
                except LookupError:
                    logger.info(f"NLTK resource '{resource}' not found. Attempting download...")
                    # Download the specific resource quietly
                    nltk.download(resource, quiet=True)
                    logger.info(f"NLTK resource '{resource}' downloaded successfully.")
            # Verify WordNet is loaded after download attempt
            wordnet.ensure_loaded()
            logger.debug("Required NLTK resources are available and WordNet is loaded.")
        except Exception as e:
            logger.error(f"Failed to download or verify required NLTK resources: {e}")
            # If resources fail, simplification might not work, but don't crash init
    
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
            # Check if WordNet is actually available before processing
            wordnet.ensure_loaded()
            # wordnet.synsets('test') # Quick check - avoid unnecessary calls
            
            # Split text while preserving delimiters (whitespace, punctuation)
            parts = re.split(r'(\W+)', text)
            result_parts = []
            
            for part in parts:
                if not part: # Skip empty strings from split
                    continue
                    
                # Check if the part is a word (alphanumeric, basically what \w matches)
                is_word = part.isalnum() # A simple check, might need refinement
                                         # Or use re.match(r'\w+$', part)
                
                if is_word and self._is_complex_word(part):
                    # Lemmatize the word before looking for synonyms
                    lemmatized_word = self.lemmatizer.lemmatize(part.lower())
                    # Also try lemmatizing as a verb, as default is noun
                    if lemmatized_word == part.lower(): # If noun lemmatization didn't change it
                        lemmatized_word = self.lemmatizer.lemmatize(part.lower(), pos='v')

                    synonyms = self._get_synonyms(lemmatized_word)
                    
                    # If no synonyms found for lemmatized word, try original word
                    if not synonyms and lemmatized_word != part.lower():
                         synonyms = self._get_synonyms(part.lower())

                    if synonyms:
                        # Use the first (shortest) synonym
                        replacement = synonyms[0]
                        # Preserve original capitalization
                        if part.istitle(): # Handle title case e.g. 'Utilizing' -> 'Use'
                            replacement = replacement.title()
                        elif part[0].isupper(): # Handle sentence start or other capitalized
                           replacement = replacement[0].upper() + replacement[1:]
                           
                        result_parts.append(replacement)
                    else:
                        result_parts.append(part) # No synonym found, keep original
                else:
                    # Keep original part (either non-complex word or delimiter)
                    result_parts.append(part)
            
            return "".join(result_parts)
            
        except Exception as e:
            logger.warning(f"Error in vocabulary simplification: {str(e)}")
            return text  # Return original text on error

# Example usage (optional, for testing)
if __name__ == '__main__':
    simplifier = WordNetSimplifier(min_word_length=5)
    
    test_text = "This is a demonstration of the vocabulary simplification utility. It endeavours to transmute intricate expressions into simpler alternatives."
    
    simplified_text = simplifier.simplify(test_text)
    print(f"Original: {test_text}")
    print(f"Simplified: {simplified_text}")
    
    test_text_2 = "Utilizing complex methodologies necessitates careful deliberation."
    simplified_text_2 = simplifier.simplify(test_text_2)
    print(f"Original: {test_text_2}")
    print(f"Simplified: {simplified_text_2}") 