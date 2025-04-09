import unittest
import pytest
from unittest.mock import patch, MagicMock

from textcleaner.processors.structure_processor import StructureProcessor
# Add other necessary imports here

# Define the path to the utility functions to mock
UTILS_PATH = 'textcleaner.processors.structure_processor.so_utils'

@pytest.mark.unit
class TestStructureProcessor(unittest.TestCase):
    """Test suite for the StructureProcessor."""

    def setUp(self):
        """Set up test fixtures, if needed."""
        pass # Add setup logic if necessary

    def tearDown(self):
        """Tear down test fixtures, if needed."""
        pass # Add teardown logic if necessary

    def test_init_stores_flags(self):
        """Test that the constructor stores the configuration flags."""
        processor = StructureProcessor(preserve_headings=True, preserve_lists=False, preserve_tables=True, preserve_links=True)
        self.assertTrue(processor.preserve_headings)
        self.assertFalse(processor.preserve_lists)
        # Assert other flags if they become relevant later

    def test_process_empty_content(self):
        """Test processing empty content returns empty content."""
        processor = StructureProcessor(preserve_headings=True, preserve_lists=True, preserve_tables=True, preserve_links=True)
        result = processor.process("")
        self.assertEqual(result, "")

    @patch(f'{UTILS_PATH}.standardize_lists')
    @patch(f'{UTILS_PATH}.format_headings')
    def test_process_preserve_headings_only(self, mock_format_headings, mock_standardize_lists):
        """Test processing calls only format_headings when preserve_headings=True, preserve_lists=True."""
        processor = StructureProcessor(preserve_headings=True, preserve_lists=True, preserve_tables=False, preserve_links=False)
        input_content = "# Heading\n* List item"
        mock_format_headings.return_value = "Formatted Heading Content"
        
        result = processor.process(input_content)
        
        mock_standardize_lists.assert_not_called() # preserve_lists is True
        mock_format_headings.assert_called_once_with(input_content)
        self.assertEqual(result, "Formatted Heading Content")

    @patch(f'{UTILS_PATH}.standardize_lists')
    @patch(f'{UTILS_PATH}.format_headings')
    def test_process_preserve_nothing(self, mock_format_headings, mock_standardize_lists):
        """Test processing calls only standardize_lists when preserve_headings=False, preserve_lists=False."""
        processor = StructureProcessor(preserve_headings=False, preserve_lists=False, preserve_tables=False, preserve_links=False)
        input_content = "# Heading\n* List item"
        mock_standardize_lists.return_value = "Standardized List Content"
        
        result = processor.process(input_content)
        
        mock_standardize_lists.assert_called_once_with(input_content)
        mock_format_headings.assert_not_called() # preserve_headings is False
        self.assertEqual(result, "Standardized List Content")

    @patch(f'{UTILS_PATH}.standardize_lists')
    @patch(f'{UTILS_PATH}.format_headings')
    def test_process_standardize_lists_format_headings(self, mock_format_headings, mock_standardize_lists):
        """Test processing calls both utils when preserve_headings=True, preserve_lists=False."""
        processor = StructureProcessor(preserve_headings=True, preserve_lists=False, preserve_tables=False, preserve_links=False)
        input_content = "# Heading\n* List item"
        
        # Define side effects for sequential calls
        mock_standardize_lists.return_value = "List Standardized"
        mock_format_headings.return_value = "Headings Formatted"
        
        result = processor.process(input_content)
        
        # Check calls in order
        mock_standardize_lists.assert_called_once_with(input_content)
        # format_headings should be called with the output of standardize_lists
        mock_format_headings.assert_called_once_with("List Standardized") 
        
        self.assertEqual(result, "Headings Formatted") # Final result is from format_headings

    @patch(f'{UTILS_PATH}.standardize_lists')
    @patch(f'{UTILS_PATH}.format_headings')
    def test_process_preserve_all_calls_nothing(self, mock_format_headings, mock_standardize_lists):
        """Test processing calls neither util when preserve_headings=False, preserve_lists=True."""
        # Note: Logically, preserve_lists=True should imply headings are also preserved as-is,
        # but current implementation allows preserve_headings=False, preserve_lists=True.
        processor = StructureProcessor(preserve_headings=False, preserve_lists=True, preserve_tables=False, preserve_links=False)
        input_content = "# Heading\n* List item"
        
        result = processor.process(input_content)
        
        mock_standardize_lists.assert_not_called()
        mock_format_headings.assert_not_called()
        self.assertEqual(result, input_content) # Content should be unchanged

if __name__ == "__main__":
    unittest.main()
