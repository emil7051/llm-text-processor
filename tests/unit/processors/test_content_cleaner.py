import unittest
import pytest
from unittest.mock import patch, MagicMock, call

from textcleaner.processors.content_cleaner import ContentCleaner
# Add other necessary imports here

# Define the path to the utility functions to mock
UTILS_PATH = 'textcleaner.processors.content_cleaner.cc_utils'

@pytest.mark.unit
class TestContentCleaner(unittest.TestCase):
    """Test suite for the ContentCleaner."""

    def setUp(self):
        """Set up test fixtures, if needed."""
        pass # Add setup logic if necessary

    def tearDown(self):
        """Tear down test fixtures, if needed."""
        pass # Add teardown logic if necessary

    def test_init_stores_flags(self):
        """Test that the constructor stores the configuration flags."""
        processor = ContentCleaner(
            remove_headers_footers=True,
            remove_page_numbers=True, # Included for completeness, though unused
            remove_watermarks=False,
            clean_whitespace=True,
            normalize_unicode=False,
            remove_boilerplate=True,
            remove_duplicate_content=False,
            remove_irrelevant_metadata=False,
            merge_short_paragraphs=True,
            remove_footnotes=False,
            join_paragraph_lines=False # Added
        )
        self.assertTrue(processor.remove_headers_footers)
        self.assertTrue(processor.clean_whitespace)
        self.assertFalse(processor.normalize_unicode)
        self.assertTrue(processor.remove_boilerplate)
        self.assertFalse(processor.remove_duplicate_content)
        self.assertTrue(processor.merge_short_paragraphs)
        # Add asserts for other flags if they become active

    def test_process_empty_content(self):
        """Test processing empty content returns empty content."""
        processor = ContentCleaner(False, False, False, False, False, False, False, False, False, False, False) # Added False
        self.assertEqual(processor.process(""), "")
        self.assertEqual(processor.process("   "), "")

    # Use a single complex patch to test call order and interactions
    @patch(f'{UTILS_PATH}.normalize_unicode')
    @patch(f'{UTILS_PATH}.merge_short_paragraphs')
    @patch(f'{UTILS_PATH}.remove_boilerplate_text')
    @patch(f'{UTILS_PATH}.remove_duplicates')
    @patch(f'{UTILS_PATH}.join_paragraph_lines') # Added mock
    @patch(f'{UTILS_PATH}.clean_whitespace')
    @patch(f'{UTILS_PATH}.remove_headers_footers')
    def test_process_all_flags_true(self, mock_rm_hf, mock_clean_ws, mock_join_pl, mock_rm_dup, mock_rm_bp, mock_merge_sp, mock_norm_uni):
        """Test processing calls all utils in order when all relevant flags are True."""
        processor = ContentCleaner(
            remove_headers_footers=True,
            remove_page_numbers=False, # Ignored
            remove_watermarks=False, # Ignored
            clean_whitespace=True,
            normalize_unicode=True,
            remove_boilerplate=True,
            remove_duplicate_content=True,
            remove_irrelevant_metadata=False, # Ignored
            merge_short_paragraphs=True,
            remove_footnotes=False,
            join_paragraph_lines=True # Added True, assuming it should run if enabled
        )
        
        input_content = " Test Content \nHeader\nFooter\nDuplicate Para\nDuplicate Para\nBoilerplate Text\nShort Para 1\n\nShort Para 2\nÃ© "
        # Simulate the content transformation through the NEW pipeline order
        mock_rm_hf.return_value = "Header Removed"
        mock_clean_ws.return_value = "Whitespace Cleaned"
        mock_join_pl.return_value = "Lines Joined"
        mock_rm_dup.return_value = "Duplicates Removed"
        mock_rm_bp.return_value = "Boilerplate Removed"
        mock_merge_sp.return_value = "Short Paras Merged"
        mock_norm_uni.return_value = "Final Content No Strip"

        result = processor.process(input_content)

        # Assert calls in the NEW correct order with intermediate results
        # (Footnotes would be called here if enabled)
        mock_rm_hf.assert_called_once_with(input_content)
        mock_clean_ws.assert_called_once_with("Header Removed") # After header removal
        mock_join_pl.assert_called_once_with("Whitespace Cleaned") # After whitespace
        mock_rm_dup.assert_called_once_with("Lines Joined") # After joining lines
        mock_rm_bp.assert_called_once_with("Duplicates Removed") # After duplicate removal
        mock_merge_sp.assert_called_once_with("Boilerplate Removed") # After boilerplate
        mock_norm_uni.assert_called_once_with("Short Paras Merged") # After merging
        
        # Final result should be the output of the last step, stripped
        self.assertEqual(result, "Final Content No Strip") # .strip() is applied
        
    # Patch only the necessary utils for this specific test
    @patch(f'{UTILS_PATH}.clean_whitespace')
    @patch(f'{UTILS_PATH}.normalize_unicode')
    def test_process_subset_flags_true(self, mock_norm_uni, mock_clean_ws):
        """Test processing calls only relevant utils when a subset of flags are True."""
        processor = ContentCleaner(
            remove_headers_footers=False, # Off
            remove_page_numbers=False,
            remove_watermarks=False,
            clean_whitespace=True, # On
            normalize_unicode=True, # On
            remove_boilerplate=False, # Off
            remove_duplicate_content=False, # Off
            remove_irrelevant_metadata=False,
            merge_short_paragraphs=False, # Off
            remove_footnotes=False,
            join_paragraph_lines=False # Added False
        )
        
        input_content = " Test \n Content Ã© "
        # Simulate transformations
        mock_clean_ws.return_value = "Test Content é" # Whitespace cleaned, maybe trailing space
        mock_norm_uni.return_value = "Test Content é" # Unicode normalized (no change here)
        
        result = processor.process(input_content)
        
        # Verify only the expected functions were called
        mock_clean_ws.assert_called_once_with(input_content) 
        mock_norm_uni.assert_called_once_with("Test Content é") # Called with clean_ws output
        
        # Check other mocks were NOT called (need to patch them to check assert_not_called)
        with patch(f'{UTILS_PATH}.remove_headers_footers') as mock_rm_hf, \
             patch(f'{UTILS_PATH}.remove_duplicates') as mock_rm_dup, \
             patch(f'{UTILS_PATH}.remove_boilerplate_text') as mock_rm_bp, \
             patch(f'{UTILS_PATH}.merge_short_paragraphs') as mock_merge_sp:
            
            # Re-run process within this context to check non-calls
            mock_clean_ws.reset_mock()
            mock_norm_uni.reset_mock()
            mock_clean_ws.return_value = "Test Content é"
            mock_norm_uni.return_value = "Test Content é"
            processor.process(input_content)

            mock_rm_hf.assert_not_called()
            mock_rm_dup.assert_not_called()
            mock_rm_bp.assert_not_called()
            mock_merge_sp.assert_not_called()
        
        self.assertEqual(result, "Test Content é") # Final result is stripped
        
    @patch(f'{UTILS_PATH}.normalize_unicode')
    @patch(f'{UTILS_PATH}.merge_short_paragraphs')
    @patch(f'{UTILS_PATH}.clean_whitespace')
    @patch(f'{UTILS_PATH}.remove_boilerplate_text')
    @patch(f'{UTILS_PATH}.remove_duplicates')
    @patch(f'{UTILS_PATH}.remove_headers_footers')
    def test_process_all_flags_false(self, mock_rm_hf, mock_rm_dup, mock_rm_bp, mock_clean_ws, mock_merge_sp, mock_norm_uni):
        """Test processing calls no utils when all flags are False."""
        processor = ContentCleaner(False, False, False, False, False, False, False, False, False, False, False) # Added False
        processor.process("Some test content")
        # Assert that none of the utility functions were called
        mock_rm_hf.assert_not_called()
        mock_rm_dup.assert_not_called()
        mock_rm_bp.assert_not_called()
        mock_clean_ws.assert_not_called()
        mock_merge_sp.assert_not_called()
        mock_norm_uni.assert_not_called()
        
        # Result should be the original content, stripped
        self.assertEqual(processor.process("  Raw Content  "), "Raw Content")

    @patch(f'{UTILS_PATH}.remove_footnotes')
    @patch(f'{UTILS_PATH}.remove_headers_footers')
    def test_process_remove_footnotes_flag(self, mock_rm_hf, mock_rm_fn):
        """Test processing calls remove_footnotes when flag is True, after headers/footers."""
        # Test case 1: remove_footnotes = True
        processor_true = ContentCleaner(
            remove_headers_footers=True,
            remove_page_numbers=False, 
            remove_watermarks=False,
            clean_whitespace=False,
            normalize_unicode=False,
            remove_boilerplate=False,
            remove_duplicate_content=False,
            remove_irrelevant_metadata=False,
            merge_short_paragraphs=False,
            remove_footnotes=True,
            join_paragraph_lines=False # Added False
        )
        
        input_content = "Header\nActual Content\n1. Footnote https://example.com\nFooter"
        mock_rm_hf.return_value = "Actual Content\n1. Footnote https://example.com"
        mock_rm_fn.return_value = "Actual Content"

        processor_true.process(input_content)

        # Assert remove_footnotes was called after remove_headers_footers
        mock_rm_hf.assert_called_once_with(input_content)
        mock_rm_fn.assert_called_once_with("Actual Content\n1. Footnote https://example.com")

        # Reset mocks for the next case
        mock_rm_hf.reset_mock()
        mock_rm_fn.reset_mock()

        # Test case 2: remove_footnotes = False
        processor_false = ContentCleaner(
            remove_headers_footers=True,
            remove_page_numbers=False,
            remove_watermarks=False,
            clean_whitespace=False,
            normalize_unicode=False,
            remove_boilerplate=False,
            remove_duplicate_content=False,
            remove_irrelevant_metadata=False,
            merge_short_paragraphs=False,
            remove_footnotes=False,
            join_paragraph_lines=False # Added False
        )
        mock_rm_hf.reset_mock()
        mock_rm_fn.reset_mock()

        mock_rm_hf.return_value = "1. Footnote http://example.com\nContent"

        processor_false.process(input_content)

        # Assert remove_footnotes was NOT called
        mock_rm_hf.assert_called_once_with(input_content)
        mock_rm_fn.assert_not_called()
        
    # Patch only the necessary utils for this specific test


if __name__ == "__main__":
    unittest.main()
