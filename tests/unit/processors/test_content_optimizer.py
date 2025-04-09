import unittest
import pytest
from unittest.mock import patch, MagicMock, call

from textcleaner.processors.content_optimizer import ContentOptimizer
# Add other necessary imports here

# Define paths for mocking
OPTIMIZER_MODULE_PATH = 'textcleaner.processors.content_optimizer'
CO_UTILS_PATH = f'{OPTIMIZER_MODULE_PATH}.co_utils'
TEXT_SIMPLIFIER_PATH = f'{OPTIMIZER_MODULE_PATH}.TextSimplifier'
DOMAIN_OPTIMIZER_PATH = f'{OPTIMIZER_MODULE_PATH}.DomainTextOptimizer'
TEMPORAL_OPTIMIZER_PATH = f'{OPTIMIZER_MODULE_PATH}.TemporalExpressionOptimizer'
WORDNET_SIMPLIFIER_PATH = f'{OPTIMIZER_MODULE_PATH}.WordNetSimplifier'

# Default config used for many tests
DEFAULT_OPTIMIZER_CONFIG = {
    "abbreviate_common_terms": False,
    "simplify_citations": False,
    "simplify_references": False,
    "simplify_urls": False,
    "max_line_length": 0,
    "optimize_temporal": False,
    "use_stanford_nlp": False,
    "simplify_vocabulary": False,
    "min_word_length": 3,
    "download_nltk_resources": False,
    "condense_repetitive_patterns": False,
    "remove_redundant_phrases": False,
    "remove_excessive_punctuation": False,
    "domain_abbreviations": []
}

@pytest.mark.unit
class TestContentOptimizerInit(unittest.TestCase):
    """Test suite specifically for ContentOptimizer initialization."""

    # Helper to create config easily
    def create_config(self, **kwargs):
        config = DEFAULT_OPTIMIZER_CONFIG.copy()
        config.update(kwargs)
        return config

    @patch(f'{OPTIMIZER_MODULE_PATH}._wordnet_available', True)
    @patch(f'{OPTIMIZER_MODULE_PATH}._temporal_available', True)
    @patch(f'{OPTIMIZER_MODULE_PATH}._replacements_available', True)
    @patch(WORDNET_SIMPLIFIER_PATH)
    @patch(TEMPORAL_OPTIMIZER_PATH)
    @patch(DOMAIN_OPTIMIZER_PATH)
    @patch(TEXT_SIMPLIFIER_PATH)
    def test_init_all_available_all_flags_on(self, mock_text_simp, mock_domain_opt, mock_temp_opt, mock_word_simp, *_): # *_ ignores availability mocks
        """Test init instantiates all helpers when available and flags are on."""
        config = self.create_config(
            abbreviate_common_terms=True,
            optimize_temporal=True,
            simplify_vocabulary=True,
            simplify_citations=True,
            domain_abbreviations=["medical"], # Need domain for DomainOptimizer
            use_stanford_nlp=True, # For Temporal
            min_word_length=5, # For WordNet
            download_nltk_resources=True # For WordNet
        )
        optimizer = ContentOptimizer(**config)
        
        mock_text_simp.assert_called_once_with()
        mock_domain_opt.assert_called_once_with(domains=["medical"])
        mock_temp_opt.assert_called_once_with(use_stanford=True)
        mock_word_simp.assert_called_once_with(min_word_length=5, download_resources=True)
        self.assertIsNotNone(optimizer.text_simplifier)
        self.assertIsNotNone(optimizer.domain_optimizer)
        self.assertIsNotNone(optimizer.temporal_optimizer)
        self.assertIsNotNone(optimizer.word_simplifier)
        # Check basic config stored
        self.assertTrue(optimizer.config["simplify_citations"]) # Should be default or from config

    @patch(f'{OPTIMIZER_MODULE_PATH}._wordnet_available', False) # WordNet NOT available
    @patch(f'{OPTIMIZER_MODULE_PATH}._temporal_available', True)
    @patch(f'{OPTIMIZER_MODULE_PATH}._replacements_available', True)
    @patch(WORDNET_SIMPLIFIER_PATH)
    @patch(TEMPORAL_OPTIMIZER_PATH)
    @patch(DOMAIN_OPTIMIZER_PATH)
    @patch(TEXT_SIMPLIFIER_PATH)
    def test_init_some_unavailable_flags_on(self, mock_text_simp, mock_domain_opt, mock_temp_opt, mock_word_simp, *_): 
        """Test init does not instantiate helpers if dependency is unavailable, even if flag is on."""
        config = self.create_config(
            abbreviate_common_terms=True,
            optimize_temporal=True,
            simplify_vocabulary=True, # Flag is on, but _wordnet_available is False
            domain_abbreviations=[] # No domain 
        )
        optimizer = ContentOptimizer(**config)
        
        mock_text_simp.assert_called_once_with()
        mock_domain_opt.assert_not_called() # domain_abbreviations is empty
        mock_temp_opt.assert_called_once_with(use_stanford=False) # Default use_stanford
        mock_word_simp.assert_not_called() # Dependency unavailable
        self.assertIsNotNone(optimizer.text_simplifier)
        self.assertIsNone(optimizer.domain_optimizer)
        self.assertIsNotNone(optimizer.temporal_optimizer)
        self.assertIsNone(optimizer.word_simplifier) # Should be None
        
    @patch(f'{OPTIMIZER_MODULE_PATH}._wordnet_available', True)
    @patch(f'{OPTIMIZER_MODULE_PATH}._temporal_available', False) # Temporal NOT available
    @patch(f'{OPTIMIZER_MODULE_PATH}._replacements_available', False) # Replacements NOT available
    @patch(WORDNET_SIMPLIFIER_PATH)
    @patch(TEMPORAL_OPTIMIZER_PATH)
    @patch(DOMAIN_OPTIMIZER_PATH)
    @patch(TEXT_SIMPLIFIER_PATH)
    def test_init_some_unavailable_other_flags_on(self, mock_text_simp, mock_domain_opt, mock_temp_opt, mock_word_simp, *_):
        """Test init with different unavailable dependencies."""
        config = self.create_config(
            abbreviate_common_terms=True, # Flag on, dependency off
            optimize_temporal=True,      # Flag on, dependency off
            simplify_vocabulary=True,    # Flag on, dependency on
            domain_abbreviations=["tech"]
        )
        optimizer = ContentOptimizer(**config)
        
        mock_text_simp.assert_not_called()
        mock_domain_opt.assert_not_called() # Requires text_simplifier first
        mock_temp_opt.assert_not_called()
        mock_word_simp.assert_called_once_with(min_word_length=3, download_resources=False) # Defaults
        self.assertIsNone(optimizer.text_simplifier)
        self.assertIsNone(optimizer.domain_optimizer)
        self.assertIsNone(optimizer.temporal_optimizer)
        self.assertIsNotNone(optimizer.word_simplifier)

    @patch(f'{OPTIMIZER_MODULE_PATH}._wordnet_available', True)
    @patch(f'{OPTIMIZER_MODULE_PATH}._temporal_available', True)
    @patch(f'{OPTIMIZER_MODULE_PATH}._replacements_available', True)
    @patch(WORDNET_SIMPLIFIER_PATH)
    @patch(TEMPORAL_OPTIMIZER_PATH)
    @patch(DOMAIN_OPTIMIZER_PATH)
    @patch(TEXT_SIMPLIFIER_PATH)
    def test_init_all_available_flags_off(self, mock_text_simp, mock_domain_opt, mock_temp_opt, mock_word_simp, *_): 
        """Test init instantiates nothing if all flags are off, even if dependencies available."""
        config = self.create_config( # All flags False by default
            abbreviate_common_terms=False,
            optimize_temporal=False,
            simplify_vocabulary=False
        )
        optimizer = ContentOptimizer(**config)
        
        mock_text_simp.assert_not_called()
        mock_domain_opt.assert_not_called()
        mock_temp_opt.assert_not_called()
        mock_word_simp.assert_not_called()
        self.assertIsNone(optimizer.text_simplifier)
        self.assertIsNone(optimizer.domain_optimizer)
        self.assertIsNone(optimizer.temporal_optimizer)
        self.assertIsNone(optimizer.word_simplifier)
        # Check other config stored
        self.assertEqual(optimizer.config["max_line_length"], 0)

# Separate class for process tests to keep setup clean
@pytest.mark.unit
class TestContentOptimizerProcess(unittest.TestCase):
    """Test suite for ContentOptimizer process method."""
    
    # Helper to create optimizer with mocked helpers
    def create_optimizer_with_mocks(self, config):
        # Assume dependencies are available for process tests
        with patch(f'{OPTIMIZER_MODULE_PATH}._wordnet_available', True), \
             patch(f'{OPTIMIZER_MODULE_PATH}._temporal_available', True), \
             patch(f'{OPTIMIZER_MODULE_PATH}._replacements_available', True), \
             patch(WORDNET_SIMPLIFIER_PATH) as self.mock_word_simp_cls, \
             patch(TEMPORAL_OPTIMIZER_PATH) as self.mock_temp_opt_cls, \
             patch(DOMAIN_OPTIMIZER_PATH) as self.mock_domain_opt_cls, \
             patch(TEXT_SIMPLIFIER_PATH) as self.mock_text_simp_cls:
            
            # Create mock instances for the helper classes
            self.mock_text_simp = MagicMock()
            self.mock_domain_opt = MagicMock()
            self.mock_temp_opt = MagicMock()
            self.mock_word_simp = MagicMock()
            
            # Configure class mocks to return instance mocks
            self.mock_text_simp_cls.return_value = self.mock_text_simp
            self.mock_domain_opt_cls.return_value = self.mock_domain_opt
            self.mock_temp_opt_cls.return_value = self.mock_temp_opt
            self.mock_word_simp_cls.return_value = self.mock_word_simp

            optimizer = ContentOptimizer(**config)
            return optimizer

    def test_process_empty_content(self):
        """Test processing empty content returns empty content."""
        config = DEFAULT_OPTIMIZER_CONFIG.copy()
        optimizer = self.create_optimizer_with_mocks(config)
        result = optimizer.process("")
        self.assertEqual(result, "")

    # Patch all co_utils functions
    @patch(f'{CO_UTILS_PATH}.optimize_line_length')
    @patch(f'{CO_UTILS_PATH}.simplify_urls')
    @patch(f'{CO_UTILS_PATH}.simplify_citations')
    @patch(f'{CO_UTILS_PATH}.remove_excessive_punctuation')
    @patch(f'{CO_UTILS_PATH}.condense_repetitive_patterns')
    @patch(f'{CO_UTILS_PATH}.remove_redundant_phrases')
    def test_process_all_on(self, mock_rm_redund, mock_condense, mock_rm_punct, mock_simp_cite, mock_simp_url, mock_opt_line):
        """Test process calls all helpers and utils in order when all flags are on."""
        config = DEFAULT_OPTIMIZER_CONFIG.copy()
        config.update({
            "abbreviate_common_terms": True,
            "domain_abbreviations": ["test"], # To activate domain optimizer
            "optimize_temporal": True,
            "simplify_vocabulary": True,
            "remove_redundant_phrases": True,
            "condense_repetitive_patterns": True,
            "remove_excessive_punctuation": True,
            "simplify_citations": True,
            "simplify_urls": True,
            "max_line_length": 80,
        })
        optimizer = self.create_optimizer_with_mocks(config)
        
        input_content = "Start"
        # Define side effects to track content changes
        self.mock_text_simp.simplify.return_value = "TextSimp"
        self.mock_domain_opt.optimize.return_value = "DomainOpt"
        self.mock_temp_opt.optimize.return_value = "TemporalOpt"
        self.mock_word_simp.simplify.return_value = "WordSimp"
        mock_rm_redund.return_value = "RmRedund"
        mock_condense.return_value = "Condense"
        mock_rm_punct.return_value = "RmPunct"
        mock_simp_cite.return_value = "SimpCite"
        mock_simp_url.return_value = "SimpUrl"
        mock_opt_line.return_value = "OptLine"
        
        result = optimizer.process(input_content)
        
        # Assert calls in correct order with intermediate content
        self.mock_text_simp.simplify.assert_called_once_with(input_content)
        self.mock_domain_opt.optimize.assert_called_once_with("TextSimp")
        self.mock_temp_opt.optimize.assert_called_once_with("DomainOpt")
        self.mock_word_simp.simplify.assert_called_once_with("TemporalOpt")
        mock_rm_redund.assert_called_once_with("WordSimp")
        mock_condense.assert_called_once_with("RmRedund")
        mock_rm_punct.assert_called_once_with("Condense")
        mock_simp_cite.assert_called_once_with("RmPunct")
        mock_simp_url.assert_called_once_with("SimpCite")
        mock_opt_line.assert_called_once_with("SimpUrl", 80)
        
        self.assertEqual(result, "OptLine")

    # Patch only the relevant co_utils function
    @patch(f'{CO_UTILS_PATH}.simplify_citations')
    def test_process_subset_on(self, mock_simp_cite):
        """Test process calls only relevant helpers and utils."""
        config = DEFAULT_OPTIMIZER_CONFIG.copy()
        config.update({
            "simplify_vocabulary": True, # Helper flag
            "simplify_citations": True, # Util flag
            "max_line_length": 0 # Util off
        })
        optimizer = self.create_optimizer_with_mocks(config)
        
        input_content = "Cite [1] word."
        self.mock_word_simp.simplify.return_value = "WordSimp Out"
        mock_simp_cite.return_value = "SimpCite Out"
        
        # Mock other helpers/utils to check they aren't called
        with patch(f'{CO_UTILS_PATH}.optimize_line_length') as mock_opt_line, \
             patch(f'{CO_UTILS_PATH}.simplify_urls') as mock_simp_url:
             
            result = optimizer.process(input_content)

            # Check expected calls
            self.mock_word_simp.simplify.assert_called_once_with(input_content)
            mock_simp_cite.assert_called_once_with("WordSimp Out")
            
            # Check helpers not called
            self.mock_text_simp.simplify.assert_not_called()
            self.mock_domain_opt.optimize.assert_not_called()
            self.mock_temp_opt.optimize.assert_not_called()
            
            # Check utils not called
            mock_opt_line.assert_not_called()
            mock_simp_url.assert_not_called()
            # ... (could patch and check all others too)
        
        self.assertEqual(result, "SimpCite Out")

    # No co_utils patches needed if none should be called
    def test_process_all_off(self):
        """Test process calls nothing when all flags are off."""
        config = DEFAULT_OPTIMIZER_CONFIG.copy() # All flags default to False
        optimizer = self.create_optimizer_with_mocks(config)
        
        input_content = "Input Content"
        
        # Need to patch utils to check they aren't called
        with patch(f'{CO_UTILS_PATH}.optimize_line_length') as mock_opt_line, \
             patch(f'{CO_UTILS_PATH}.simplify_urls') as mock_simp_url, \
             patch(f'{CO_UTILS_PATH}.simplify_citations') as mock_simp_cite, \
             patch(f'{CO_UTILS_PATH}.remove_excessive_punctuation') as mock_rm_punct, \
             patch(f'{CO_UTILS_PATH}.condense_repetitive_patterns') as mock_condense, \
             patch(f'{CO_UTILS_PATH}.remove_redundant_phrases') as mock_rm_redund:
             
            result = optimizer.process(input_content)

            # Check helpers not called
            self.mock_text_simp.simplify.assert_not_called()
            self.mock_domain_opt.optimize.assert_not_called()
            self.mock_temp_opt.optimize.assert_not_called()
            self.mock_word_simp.simplify.assert_not_called()
            
            # Check utils not called
            mock_rm_redund.assert_not_called()
            mock_condense.assert_not_called()
            mock_rm_punct.assert_not_called()
            mock_simp_cite.assert_not_called()
            mock_simp_url.assert_not_called()
            mock_opt_line.assert_not_called()
            
        self.assertEqual(result, input_content) # Should return original content


if __name__ == "__main__":
    unittest.main()
