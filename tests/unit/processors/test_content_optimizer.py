import unittest
from unittest.mock import patch, MagicMock

from textcleaner.processors.content_optimizer import ContentOptimizer

# Define paths for mocking
OPTIMIZER_MODULE_PATH = 'textcleaner.processors.content_optimizer'
UTILS_PATH = 'textcleaner.utils'
REPLACEMENTS_PATH = f'{UTILS_PATH}.replacement_dictionaries'
WORDNET_PATH = f'{UTILS_PATH}.word_simplifier'
CO_UTILS_PATH = f'{UTILS_PATH}.content_optimizations'

class TestContentOptimizerInit(unittest.TestCase):
    """Tests the __init__ method of ContentOptimizer."""

    def test_init_all_features_available_and_on(self):
        """Test initialization when all dependencies are available and features are on."""
        base_config = {
            "abbreviate_common_terms": True,
            "simplify_citations": True,
            "simplify_references": False, # Not used
            "simplify_urls": True,
            "max_line_length": 80,
            "simplify_vocabulary": True,
            "min_word_length": 4,
            "condense_repetitive_patterns": True,
            "remove_redundant_phrases": True,
            "remove_excessive_punctuation": True,
            "domain_abbreviations": ["medical"]
        }
        
        with patch(f'{OPTIMIZER_MODULE_PATH}._replacements_available', True), \
             patch(f'{OPTIMIZER_MODULE_PATH}._wordnet_available', True), \
             patch(f'{OPTIMIZER_MODULE_PATH}.TextSimplifier') as mock_text_simp, \
             patch(f'{OPTIMIZER_MODULE_PATH}.DomainTextOptimizer') as mock_domain_opt, \
             patch(f'{OPTIMIZER_MODULE_PATH}.WordNetSimplifier') as mock_word_simp:
                 
            optimizer = ContentOptimizer(**base_config)
            
            self.assertIsNotNone(optimizer.text_simplifier)
            self.assertIsNotNone(optimizer.domain_optimizer)
            self.assertIsNotNone(optimizer.word_simplifier)
            mock_text_simp.assert_called_once()
            mock_domain_opt.assert_called_once_with(domains=["medical"])
            mock_word_simp.assert_called_once_with(min_word_length=4)
            self.assertEqual(optimizer.config["max_line_length"], 80)

    def test_init_vocab_not_available(self):
        """Test init when NLTK is not available but simplify_vocabulary is True."""
        config_no_vocab = {
            "abbreviate_common_terms": False,
            "simplify_citations": False,
            "simplify_references": False,
            "simplify_urls": False,
            "max_line_length": 0,
            "simplify_vocabulary": True,      # Flag on, dependency off
            "min_word_length": 4,
            "condense_repetitive_patterns": False,
            "remove_redundant_phrases": False,
            "remove_excessive_punctuation": False,
            "domain_abbreviations": []
        }
        
        with patch(f'{OPTIMIZER_MODULE_PATH}._replacements_available', True), \
             patch(f'{OPTIMIZER_MODULE_PATH}._wordnet_available', False), \
             patch(f'{OPTIMIZER_MODULE_PATH}.WordNetSimplifier') as mock_word_simp:
                 
            optimizer = ContentOptimizer(**config_no_vocab)
            
            self.assertIsNotNone(optimizer.text_simplifier)
            self.assertIsNone(optimizer.domain_optimizer)
            self.assertIsNone(optimizer.word_simplifier)
            mock_word_simp.assert_not_called()

    def test_init_vocab_disabled_in_config(self):
        """Test init when simplify_vocabulary is False in config."""
        config_vocab_off = {
            "abbreviate_common_terms": False,
            "simplify_citations": False,
            "simplify_references": False,
            "simplify_urls": False,
            "max_line_length": 0,
            "simplify_vocabulary": False,     # Flag off
            "min_word_length": 4,
            "condense_repetitive_patterns": False,
            "remove_redundant_phrases": False,
            "remove_excessive_punctuation": False,
            "domain_abbreviations": []
        }
        
        with patch(f'{OPTIMIZER_MODULE_PATH}._replacements_available', True), \
             patch(f'{OPTIMIZER_MODULE_PATH}._wordnet_available', True), \
             patch(f'{OPTIMIZER_MODULE_PATH}.WordNetSimplifier') as mock_word_simp:
                 
            optimizer = ContentOptimizer(**config_vocab_off)
            
            self.assertIsNone(optimizer.word_simplifier)
            mock_word_simp.assert_not_called()

class TestContentOptimizerProcess(unittest.TestCase):
    """Tests the process method of ContentOptimizer."""

    def setUp(self):
        """Set up mocks common to process tests."""
        # Mock the helper classes
        self.mock_text_simp_cls = MagicMock()
        self.mock_domain_opt_cls = MagicMock()
        self.mock_word_simp_cls = MagicMock()
        
        self.mock_text_simp = MagicMock()
        self.mock_domain_opt = MagicMock()
        self.mock_word_simp = MagicMock()
        
        self.mock_text_simp_cls.return_value = self.mock_text_simp
        self.mock_domain_opt_cls.return_value = self.mock_domain_opt
        self.mock_word_simp_cls.return_value = self.mock_word_simp
        
        # Mock the utility functions
        self.mock_remove_redundant = MagicMock()
        self.mock_condense_patterns = MagicMock()
        self.mock_remove_punctuation = MagicMock()
        self.mock_simplify_citations = MagicMock()
        self.mock_simplify_urls = MagicMock()
        self.mock_optimize_lines = MagicMock()

        # Common config for process tests - enable everything
        self.config_all_on = {
            "abbreviate_common_terms": True,
            "simplify_citations": True,
            "simplify_references": False,
            "simplify_urls": True,
            "max_line_length": 80,
            "simplify_vocabulary": True,
            "min_word_length": 4,
            "condense_repetitive_patterns": True,
            "remove_redundant_phrases": True,
            "remove_excessive_punctuation": True,
            "domain_abbreviations": ["medical"]
        }

    def test_process_calls_all_enabled_optimizers(self):
        """Verify process calls all optimizers when flags are True and dependencies available."""
        with patch(f'{OPTIMIZER_MODULE_PATH}._replacements_available', True), \
             patch(f'{OPTIMIZER_MODULE_PATH}._wordnet_available', True), \
             patch(f'{OPTIMIZER_MODULE_PATH}.TextSimplifier', self.mock_text_simp_cls), \
             patch(f'{OPTIMIZER_MODULE_PATH}.DomainTextOptimizer', self.mock_domain_opt_cls), \
             patch(f'{OPTIMIZER_MODULE_PATH}.WordNetSimplifier', self.mock_word_simp_cls), \
             patch(f'{CO_UTILS_PATH}.remove_redundant_phrases', self.mock_remove_redundant), \
             patch(f'{CO_UTILS_PATH}.condense_repetitive_patterns', self.mock_condense_patterns), \
             patch(f'{CO_UTILS_PATH}.remove_excessive_punctuation', self.mock_remove_punctuation), \
             patch(f'{CO_UTILS_PATH}.simplify_citations', self.mock_simplify_citations), \
             patch(f'{CO_UTILS_PATH}.simplify_urls', self.mock_simplify_urls), \
             patch(f'{CO_UTILS_PATH}.optimize_line_length', self.mock_optimize_lines):
                 
            optimizer = ContentOptimizer(**self.config_all_on)
            input_content = "Start Content"
            
            # Set up mock return values to track call order
            self.mock_text_simp.simplify.return_value = "TextSimp"
            self.mock_domain_opt.optimize.return_value = "DomainOpt"
            self.mock_word_simp.simplify.return_value = "WordSimp"
            self.mock_remove_redundant.return_value = "RedundantRemoved"
            self.mock_condense_patterns.return_value = "PatternsCondensed"
            self.mock_remove_punctuation.return_value = "PunctuationRemoved"
            self.mock_simplify_citations.return_value = "CitationsSimplified"
            self.mock_simplify_urls.return_value = "UrlsSimplified"
            self.mock_optimize_lines.return_value = "LinesOptimized"
            
            result = optimizer.process(input_content)
            
            # Check calls with expected intermediate results
            self.mock_text_simp.simplify.assert_called_once_with(input_content)
            self.mock_domain_opt.optimize.assert_called_once_with("TextSimp")
            self.mock_word_simp.simplify.assert_called_once_with("DomainOpt")
            self.mock_remove_redundant.assert_called_once_with("WordSimp")
            self.mock_condense_patterns.assert_called_once_with("RedundantRemoved")
            self.mock_remove_punctuation.assert_called_once_with("PatternsCondensed")
            self.mock_simplify_citations.assert_called_once_with("PunctuationRemoved")
            self.mock_simplify_urls.assert_called_once_with("CitationsSimplified")
            self.mock_optimize_lines.assert_called_once_with("UrlsSimplified", 80)
            
            self.assertEqual(result, "LinesOptimized")

    def test_process_skips_disabled_optimizers(self):
        """Verify process skips optimizers when flags are False."""
        config_some_off = {
            "abbreviate_common_terms": False, # Off
            "simplify_citations": False,    # Off
            "simplify_references": False,
            "simplify_urls": True,
            "max_line_length": 0,         # Off
            "simplify_vocabulary": False,     # Off
            "min_word_length": 4,
            "condense_repetitive_patterns": True,
            "remove_redundant_phrases": False,    # Off
            "remove_excessive_punctuation": True,
            "domain_abbreviations": []
        }
        
        with patch(f'{OPTIMIZER_MODULE_PATH}._replacements_available', True), \
             patch(f'{OPTIMIZER_MODULE_PATH}._wordnet_available', True), \
             patch(f'{OPTIMIZER_MODULE_PATH}.TextSimplifier', self.mock_text_simp_cls), \
             patch(f'{OPTIMIZER_MODULE_PATH}.DomainTextOptimizer', self.mock_domain_opt_cls), \
             patch(f'{OPTIMIZER_MODULE_PATH}.WordNetSimplifier', self.mock_word_simp_cls), \
             patch(f'{CO_UTILS_PATH}.remove_redundant_phrases', self.mock_remove_redundant), \
             patch(f'{CO_UTILS_PATH}.condense_repetitive_patterns', self.mock_condense_patterns), \
             patch(f'{CO_UTILS_PATH}.remove_excessive_punctuation', self.mock_remove_punctuation), \
             patch(f'{CO_UTILS_PATH}.simplify_citations', self.mock_simplify_citations), \
             patch(f'{CO_UTILS_PATH}.simplify_urls', self.mock_simplify_urls), \
             patch(f'{CO_UTILS_PATH}.optimize_line_length', self.mock_optimize_lines):
                 
            optimizer = ContentOptimizer(**config_some_off)
            input_content = "Start Content"
            
            # Set up mock return values 
            self.mock_simplify_urls.return_value = "UrlSimp"
            self.mock_condense_patterns.return_value = "PatternsCond"
            self.mock_remove_punctuation.return_value = "PunctRemoved"
            
            result = optimizer.process(input_content)
            
            # Check only enabled steps were called
            self.mock_text_simp.simplify.assert_not_called()
            self.mock_domain_opt.optimize.assert_not_called()
            self.mock_word_simp.simplify.assert_not_called()
            self.mock_remove_redundant.assert_not_called()
            self.mock_simplify_citations.assert_not_called()
            self.mock_optimize_lines.assert_not_called()
            
            self.mock_condense_patterns.assert_called_once_with(input_content) # First active step
            self.mock_remove_punctuation.assert_called_once_with("PatternsCond")
            self.mock_simplify_urls.assert_called_once_with("PunctRemoved")

            self.assertEqual(result, "UrlSimp") # Corrected: Final result is from simplify_urls

    def test_process_handles_empty_content(self):
        """Test process returns empty string immediately for empty input."""
        optimizer = ContentOptimizer(**self.config_all_on) # Config doesn't matter here
        result = optimizer.process("")
        self.assertEqual(result, "")
        # Ensure no mocks were called
        self.mock_text_simp.simplify.assert_not_called()
        self.mock_word_simp.simplify.assert_not_called()
        self.mock_remove_redundant.assert_not_called()

if __name__ == '__main__':
    unittest.main()
