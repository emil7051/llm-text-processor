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
            merge_short_paragraphs=True
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
        processor = ContentCleaner(False, False, False, False, False, False, False, False, False)
        result = processor.process("")
        self.assertEqual(result, "")

    # Use a single complex patch to test call order and interactions
    @patch(f'{UTILS_PATH}.normalize_unicode')
    @patch(f'{UTILS_PATH}.merge_short_paragraphs')
    @patch(f'{UTILS_PATH}.clean_whitespace')
    @patch(f'{UTILS_PATH}.remove_boilerplate_text')
    @patch(f'{UTILS_PATH}.remove_duplicates')
    @patch(f'{UTILS_PATH}.remove_headers_footers')
    def test_process_all_flags_true(self, mock_rm_hf, mock_rm_dup, mock_rm_bp, mock_clean_ws, mock_merge_sp, mock_norm_uni):
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
            merge_short_paragraphs=True
        )
        
        input_content = " Raw Content "
        # Simulate the content transformation through the pipeline
        mock_rm_hf.return_value = "No HF"
        mock_rm_dup.return_value = "No HF Dup"
        mock_rm_bp.return_value = "No HF Dup BP"
        mock_clean_ws.return_value = "No HF Dup BP CleanWS"
        mock_merge_sp.return_value = "No HF Dup BP CleanWS MergedSP"
        mock_norm_uni.return_value = "Final Content No Strip"

        result = processor.process(input_content)

        # Assert calls in the correct order with intermediate results
        mock_rm_hf.assert_called_once_with(input_content)
        mock_rm_dup.assert_called_once_with("No HF")
        mock_rm_bp.assert_called_once_with("No HF Dup")
        mock_clean_ws.assert_called_once_with("No HF Dup BP")
        mock_merge_sp.assert_called_once_with("No HF Dup BP CleanWS")
        mock_norm_uni.assert_called_once_with("No HF Dup BP CleanWS MergedSP")
        
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
            merge_short_paragraphs=False # Off
        )
        
        input_content = "  Some Content\t\u00A0  "
        # Simulate transformations
        mock_clean_ws.return_value = "Some Content " # Whitespace cleaned, maybe trailing space
        mock_norm_uni.return_value = "Some Content " # Unicode normalized (no change here)
        
        result = processor.process(input_content)
        
        # Verify only the expected functions were called
        mock_clean_ws.assert_called_once_with(input_content) 
        mock_norm_uni.assert_called_once_with("Some Content ") # Called with clean_ws output
        
        # Check other mocks were NOT called (need to patch them to check assert_not_called)
        with patch(f'{UTILS_PATH}.remove_headers_footers') as mock_rm_hf, \
             patch(f'{UTILS_PATH}.remove_duplicates') as mock_rm_dup, \
             patch(f'{UTILS_PATH}.remove_boilerplate_text') as mock_rm_bp, \
             patch(f'{UTILS_PATH}.merge_short_paragraphs') as mock_merge_sp:
            
            # Re-run process within this context to check non-calls
            mock_clean_ws.reset_mock()
            mock_norm_uni.reset_mock()
            mock_clean_ws.return_value = "Some Content "
            mock_norm_uni.return_value = "Some Content "
            processor.process(input_content)

            mock_rm_hf.assert_not_called()
            mock_rm_dup.assert_not_called()
            mock_rm_bp.assert_not_called()
            mock_merge_sp.assert_not_called()
        
        self.assertEqual(result, "Some Content") # Final result is stripped
        
    @patch(f'{UTILS_PATH}.normalize_unicode')
    @patch(f'{UTILS_PATH}.merge_short_paragraphs')
    @patch(f'{UTILS_PATH}.clean_whitespace')
    @patch(f'{UTILS_PATH}.remove_boilerplate_text')
    @patch(f'{UTILS_PATH}.remove_duplicates')
    @patch(f'{UTILS_PATH}.remove_headers_footers')
    def test_process_all_flags_false(self, mock_rm_hf, mock_rm_dup, mock_rm_bp, mock_clean_ws, mock_merge_sp, mock_norm_uni):
        """Test processing calls no utils when all flags are False."""
        processor = ContentCleaner(False, False, False, False, False, False, False, False, False)
        input_content = "  Raw Content  "
        
        result = processor.process(input_content)
        
        # Verify no utility functions were called
        mock_rm_hf.assert_not_called()
        mock_rm_dup.assert_not_called()
        mock_rm_bp.assert_not_called()
        mock_clean_ws.assert_not_called()
        mock_merge_sp.assert_not_called()
        mock_norm_uni.assert_not_called()
        
        # Result should be the original content, stripped
        self.assertEqual(result, "Raw Content")


if __name__ == "__main__":
    unittest.main()
