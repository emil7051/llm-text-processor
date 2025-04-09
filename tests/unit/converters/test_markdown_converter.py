import unittest
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import os
import time

# Import the class to test
from textcleaner.converters.markdown_converter import MarkdownConverter
from textcleaner.config.config_manager import ConfigManager

# Mock yaml import - crucial to avoid dependency
# mock_yaml = MagicMock() # Remove global mock


@pytest.mark.unit
class TestMarkdownConverter(unittest.TestCase):
    """Test suite for the MarkdownConverter."""

    def setUp(self):
        """Set up test fixtures for each test."""
        self.mock_config = MagicMock(spec=ConfigManager)
        # Patch yaml globally for all tests in this class - REMOVED
        # self.yaml_patcher = patch.dict('sys.modules', {'yaml': mock_yaml})
        # self.yaml_patcher.start()
        # self.addCleanup(self.yaml_patcher.stop) # Ensure patch stops even on test failures
        
        self.converter = MarkdownConverter(config=self.mock_config)
        self.test_file_path = Path("test_dir/test_file.md")
        
        # Reset mock for each test - REMOVED
        # mock_yaml.reset_mock()

    def test_init_sets_supported_extensions(self):
        """Test that the constructor correctly sets supported extensions."""
        self.assertEqual(self.converter.supported_extensions, [".md", ".markdown"])

    @patch('pathlib.Path.exists', return_value=True)
    @patch('textcleaner.converters.markdown_converter.MarkdownConverter.get_stats')
    @patch("builtins.open", new_callable=mock_open, read_data='''# Heading 1

Some content.''')
    def test_convert_success_no_frontmatter(self, mock_file_open, mock_get_stats, mock_exists):
        """Test successful conversion of a markdown file without frontmatter."""
        mock_stats_data = {"file_size_bytes": 50, "created_at": time.time(), "modified_at": time.time()}
        mock_get_stats.return_value = mock_stats_data
        
        content, metadata = self.converter.convert(self.test_file_path)
        
        mock_exists.assert_called_once_with()
        mock_file_open.assert_called_once_with(self.test_file_path, "r", encoding="utf-8")
        mock_get_stats.assert_called_once_with(self.test_file_path)
        # mock_yaml.safe_load.assert_not_called() # Cannot assert on non-existent mock
        
        expected_content = '''# Heading 1

Some content.'''
        self.assertEqual(content, expected_content)
        self.assertEqual(metadata["file_name"], "test_file.md")
        self.assertEqual(metadata["file_extension"], ".md")
        self.assertEqual(metadata["file_stats"]["size_bytes"], mock_stats_data["file_size_bytes"])
        self.assertNotIn("frontmatter", metadata) # Ensure no frontmatter key exists
        self.assertIn("headings", metadata)
        self.assertEqual(metadata["headings"], [{'level': 1, 'text': 'Heading 1'}])

    @patch('pathlib.Path.exists', return_value=True)
    @patch('textcleaner.converters.markdown_converter.MarkdownConverter.get_stats')
    def test_convert_success_with_frontmatter(self, mock_get_stats, mock_exists):
        """Test successful conversion with valid YAML frontmatter."""
        frontmatter_text = '''title: Test Title
author: Tester
tags: [tag1, tag2]'''
        frontmatter = f'''---
{frontmatter_text}
---
'''
        body = '''# Real Heading

Body content.'''
        file_content = frontmatter + body
        
        mock_stats_data = {"file_size_bytes": len(file_content), "created_at": time.time(), "modified_at": time.time()}
        mock_get_stats.return_value = mock_stats_data
        
        # Mock yaml parsing
        parsed_frontmatter = {"title": "Test Title", "author": "Tester", "tags": ["tag1", "tag2"]}
        # Patch yaml.safe_load specifically for this test
        with patch('textcleaner.converters.markdown_converter.yaml.safe_load', return_value=parsed_frontmatter) as mock_safe_load:
            with patch("builtins.open", mock_open(read_data=file_content)) as mock_file_open:
                content, metadata = self.converter.convert(self.test_file_path)
            
            mock_exists.assert_called_once_with()
            mock_file_open.assert_called_once_with(self.test_file_path, "r", encoding="utf-8")
            mock_get_stats.assert_called_once_with(self.test_file_path)
            # Verify yaml was called with the extracted frontmatter text (without leading/trailing newlines)
            mock_safe_load.assert_called_once_with(frontmatter_text) 
        
        # Content should be the body only
        self.assertEqual(content, body)
        
        # Check metadata includes frontmatter and specific fields
        self.assertEqual(metadata["frontmatter"], parsed_frontmatter)
        self.assertEqual(metadata["title"], "Test Title")
        self.assertEqual(metadata["author"], "Tester")
        self.assertEqual(metadata["tags"], ["tag1", "tag2"])
        self.assertNotIn("description", metadata) # Check non-present field isn't added
        self.assertEqual(metadata["headings"], [{'level': 1, 'text': 'Real Heading'}])
        self.assertEqual(metadata["file_stats"]["size_bytes"], mock_stats_data["file_size_bytes"]) 
        
    @patch('pathlib.Path.exists', return_value=True)
    @patch('textcleaner.converters.markdown_converter.MarkdownConverter.get_stats')
    def test_convert_invalid_frontmatter(self, mock_get_stats, mock_exists):
        """Test conversion when frontmatter exists but is invalid YAML."""
        frontmatter_text = '''title: Test Title
author: Tester
invalid yaml: - [ ]'''
        frontmatter = f'''---
{frontmatter_text}
---
'''
        body = '''# Body
''' 
        file_content = frontmatter + body
        
        mock_stats_data = {"file_size_bytes": len(file_content), "created_at": time.time(), "modified_at": time.time()}
        mock_get_stats.return_value = mock_stats_data
        
        # Simulate YAML parsing error
        # Patch yaml.safe_load specifically for this test
        with patch('textcleaner.converters.markdown_converter.yaml.safe_load', side_effect=Exception("YAML parse error")) as mock_safe_load:
            with patch("builtins.open", mock_open(read_data=file_content)) as mock_file_open:
                content, metadata = self.converter.convert(self.test_file_path)
                
            # Content should still be the body (frontmatter removed despite parse error)
            self.assertEqual(content, body)
            # Metadata should NOT contain frontmatter key or parsed fields
            self.assertNotIn("frontmatter", metadata)
            self.assertNotIn("title", metadata)
            mock_safe_load.assert_called_once_with(frontmatter_text) # Ensure it was attempted with correct text
        # Other metadata should be present
        self.assertEqual(metadata["headings"], [{'level': 1, 'text': 'Body'}])
        self.assertEqual(metadata["file_stats"]["size_bytes"], mock_stats_data["file_size_bytes"]) 
        
    @patch('pathlib.Path.exists', return_value=True)
    @patch('textcleaner.converters.markdown_converter.MarkdownConverter.get_stats')
    @patch("builtins.open", new_callable=mock_open, read_data='''# H1
## H2
### H3
Not a heading
#### H4 # Also valid''')
    def test_extract_headings(self, mock_file_open, mock_get_stats, mock_exists):
        """Test extraction of various levels of ATX headings."""
        mock_stats_data = {"file_size_bytes": 100, "created_at": time.time(), "modified_at": time.time()}
        mock_get_stats.return_value = mock_stats_data
        
        _, metadata = self.converter.convert(self.test_file_path)
        
        expected_headings = [
            {"level": 1, "text": "H1"},
            {"level": 2, "text": "H2"},
            {"level": 3, "text": "H3"},
            {"level": 4, "text": "H4 # Also valid"} # Correct expected text
        ]
        self.assertEqual(metadata.get("headings"), expected_headings)
        
    @patch('pathlib.Path.exists', return_value=True)
    @patch('textcleaner.converters.markdown_converter.MarkdownConverter.get_stats')
    @patch("builtins.open", new_callable=mock_open, read_data="No headings here.")
    def test_no_headings_found(self, mock_file_open, mock_get_stats, mock_exists):
        """Test conversion when no headings are present."""
        mock_stats_data = {"file_size_bytes": 20, "created_at": time.time(), "modified_at": time.time()}
        mock_get_stats.return_value = mock_stats_data
        
        _, metadata = self.converter.convert(self.test_file_path)
        self.assertNotIn("headings", metadata) # Key shouldn't exist if list is empty

    @patch('pathlib.Path.exists', return_value=False)
    def test_convert_file_not_found(self, mock_exists):
        """Test conversion raises FileNotFoundError for non-existent file."""
        with self.assertRaises(FileNotFoundError):
            self.converter.convert(self.test_file_path)
        mock_exists.assert_called_once_with()

    @patch('pathlib.Path.exists', return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_convert_unicode_decode_error(self, mock_file_open, mock_exists):
        """Test conversion raises ValueError for files with encoding issues."""
        mock_file_open.side_effect = UnicodeDecodeError('utf-8', b'\x80abc', 0, 1, 'invalid start byte')
        
        with self.assertRaisesRegex(ValueError, "File is not a valid markdown file or has an unsupported encoding"):
            self.converter.convert(self.test_file_path)
            
        mock_exists.assert_called_once_with()
        mock_file_open.assert_called_once_with(self.test_file_path, "r", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
