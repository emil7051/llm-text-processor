import unittest
from unittest.mock import patch, MagicMock

from src.textcleaner.utils.word_simplifier import WordNetSimplifier, NLTK_AVAILABLE

# Assume nltk is available for most tests unless specifically testing unavailability
MODULE_PATH = "src.textcleaner.utils.word_simplifier"


class TestWordNetSimplifier(unittest.TestCase):
    """Tests for the WordNetSimplifier class."""

    @patch.object(WordNetSimplifier, '_ensure_nltk_resources', return_value=None) 
    def setUp(self, mock_ensure_resources):
        """Set up a WordNetSimplifier instance for tests."""
        self.simplifier_min_5 = WordNetSimplifier(min_word_length=5)
        self.simplifier_min_3 = WordNetSimplifier(min_word_length=3)
        self.assertEqual(mock_ensure_resources.call_count, 2)

    @patch(f'{MODULE_PATH}.NLTK_AVAILABLE', True)
    @patch.object(WordNetSimplifier, '_get_synonyms')
    @patch.object(WordNetSimplifier, '_ensure_nltk_resources', return_value=None)
    def test_basic_simplification(self, mock_ensure_resources, mock_get_synonyms):
        """Test basic word simplification."""
        mock_get_synonyms.side_effect = lambda word: {
            "utilize": ["use"],
            "demonstration": ["demo", "display"],
            "endeavours": ["try", "strive"],
            "transmute": ["alter", "change"],
            "intricate": ["complex", "fancy"],
            "alternatives": ["options"],
            "methodologies": ["methods"],
            "necessitates": ["needs"],
            "deliberation": ["thought"]
        }.get(word, [])

        text = "This is a demonstration of the vocabulary simplification utility. It endeavours to transmute intricate expressions into simpler alternatives."
        expected = "This is a demo of the vocabulary simplification utility. It try to alter complex expressions into simpler options."
        result = self.simplifier_min_5.simplify(text)
        self.assertEqual(result, expected)

        text_2 = "Utilizing complex methodologies necessitates careful deliberation."
        expected_2 = "Use complex methods needs careful thought."
        result_2 = self.simplifier_min_5.simplify(text_2)
        self.assertEqual(result_2, expected_2)

    @patch(f'{MODULE_PATH}.NLTK_AVAILABLE', True)
    @patch.object(WordNetSimplifier, '_get_synonyms')
    @patch.object(WordNetSimplifier, '_ensure_nltk_resources', return_value=None)
    def test_min_word_length(self, mock_ensure_resources, mock_get_synonyms):
        """Test that words shorter than min_word_length are ignored."""
        mock_get_synonyms.side_effect = lambda word: {
            "word": ["wd"],
            "longer": ["long"]
        }.get(word, [])
        
        text = "A word and a longer one."
        
        expected_5 = "A word and a long one."
        result_5 = self.simplifier_min_5.simplify(text)
        self.assertEqual(result_5, expected_5)
        mock_get_synonyms.assert_called_once_with('longer') 
        
        mock_get_synonyms.reset_mock()
        
        expected_3 = "A wd and a long one."
        result_3 = self.simplifier_min_3.simplify(text)
        self.assertEqual(result_3, expected_3)
        self.assertEqual(mock_get_synonyms.call_count, 4)
        mock_get_synonyms.assert_any_call('word')
        mock_get_synonyms.assert_any_call('longer')

    @patch(f'{MODULE_PATH}.NLTK_AVAILABLE', True)
    @patch.object(WordNetSimplifier, '_get_synonyms')
    @patch.object(WordNetSimplifier, '_ensure_nltk_resources', return_value=None)
    def test_non_alpha_words_ignored(self, mock_ensure_resources, mock_get_synonyms):
        """Test that words with numbers or symbols are ignored."""
        text = "Simplify word123 and word-symbol but not regular."
        expected = "Simplify word123 and word-symbol but not regular."
        
        result = self.simplifier_min_5.simplify(text)
        self.assertEqual(result, expected)
        self.assertEqual(mock_get_synonyms.call_count, 3)
        mock_get_synonyms.assert_any_call('simplify')
        mock_get_synonyms.assert_any_call('regular')

    @patch(f'{MODULE_PATH}.NLTK_AVAILABLE', True)
    @patch.object(WordNetSimplifier, '_get_synonyms')
    @patch.object(WordNetSimplifier, '_ensure_nltk_resources', return_value=None)
    def test_capitalization_handling(self, mock_ensure_resources, mock_get_synonyms):
        """Test capitalization handling (proper nouns ignored, first letter preserved)."""
        mock_get_synonyms.side_effect = lambda word: {
            "utilizing": ["use"],
            "methodologies": ["methods"]
        }.get(word, [])

        text = "Alice is Utilizing complex Methodologies."
        expected = "Alice is Use complex Methods."
        result = self.simplifier_min_5.simplify(text)
        self.assertEqual(result, expected)
        mock_get_synonyms.assert_any_call('utilizing')
        mock_get_synonyms.assert_any_call('methodologies')

    @patch(f'{MODULE_PATH}.NLTK_AVAILABLE', True)
    @patch.object(WordNetSimplifier, '_get_synonyms')
    @patch.object(WordNetSimplifier, '_ensure_nltk_resources', return_value=None)
    def test_punctuation_preserved(self, mock_ensure_resources, mock_get_synonyms):
        """Test that surrounding punctuation is preserved."""
        mock_get_synonyms.side_effect = lambda word: ["use"] if word == 'utilize' else []
        
        text = "Is utilizing, (or Utilizing!) complex?"
        expected = "Is use, (or Use!) complex?"
        result = self.simplifier_min_5.simplify(text)
        self.assertEqual(result, expected)
        self.assertEqual(mock_get_synonyms.call_count, 3)
        mock_get_synonyms.assert_any_call('utilize')

    @patch(f'{MODULE_PATH}.NLTK_AVAILABLE', True)
    @patch.object(WordNetSimplifier, '_get_synonyms')
    @patch.object(WordNetSimplifier, '_ensure_nltk_resources', return_value=None)
    def test_no_synonym_found(self, mock_ensure_resources, mock_get_synonyms):
        """Test behavior when no shorter synonym is found."""
        mock_get_synonyms.return_value = []
        
        text = "This complexword has no shorter synonym."
        expected = "This complexword has no shorter synonym."
        result = self.simplifier_min_5.simplify(text)
        self.assertEqual(result, expected)
        self.assertEqual(mock_get_synonyms.call_count, 3)

    @patch(f'{MODULE_PATH}.NLTK_AVAILABLE', False)
    def test_nltk_unavailable(self):
        """Test that the original text is returned if NLTK is unavailable."""
        with patch.object(WordNetSimplifier, '_ensure_nltk_resources', return_value=None) as mock_ensure: 
             simplifier = WordNetSimplifier(min_word_length=5) 
             mock_ensure.assert_called_once()
             text = "Utilizing complex methodologies."
             result = simplifier.simplify(text)
             self.assertEqual(result, text) 

    @patch.object(WordNetSimplifier, '_ensure_nltk_resources', return_value=None) 
    def test_empty_input(self, mock_ensure_resources):
        """Test that empty input returns empty output."""
        result = self.simplifier_min_5.simplify("")
        self.assertEqual(result, "")

    @patch(f'{MODULE_PATH}.NLTK_AVAILABLE', True)
    @patch(f'{MODULE_PATH}.wordnet.ensure_loaded', side_effect=Exception("NLTK Error"))
    @patch.object(WordNetSimplifier, '_ensure_nltk_resources', return_value=None)
    def test_error_handling(self, mock_ensure_resources, mock_ensure_loaded):
        """Test that original text is returned on internal error."""
        text = "Utilizing complex methodologies."
        result = self.simplifier_min_5.simplify(text)
        self.assertEqual(result, text)
        mock_ensure_loaded.assert_called_once()


if __name__ == '__main__':
    unittest.main() 