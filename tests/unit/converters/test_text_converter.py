import unittest
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import os
import time

# Import the class to test
from textcleaner.converters.text_converter import TextConverter
from textcleaner.config.config_manager import ConfigManager


@pytest.mark.unit
class TestTextConverter(unittest.TestCase):
    """Test suite for the TextConverter."""

    def setUp(self):
        """Set up test fixtures for each test."""
        self.mock_config = MagicMock(spec=ConfigManager)
        self.converter = TextConverter(config=self.mock_config)
        self.test_file_path = Path("test_dir/test_file.txt")

    def test_init_sets_supported_extensions(self):
        """Test that the constructor correctly sets supported extensions."""
        self.assertEqual(self.converter.supported_extensions, [".txt"])

    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.stat')
    @patch("builtins.open", new_callable=mock_open, read_data="Test file content.")
    def test_convert_success(self, mock_file_open, mock_stat, mock_exists):
        """Test successful conversion of a valid text file."""
        # Setup mock stat result
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 100
        mock_stat_result.st_ctime = time.time() - 3600 # 1 hour ago
        mock_stat_result.st_mtime = time.time()       # Now
        mock_stat.return_value = mock_stat_result
        
        content, metadata = self.converter.convert(self.test_file_path)
        
        mock_exists.assert_called_once_with()
        mock_file_open.assert_called_once_with(self.test_file_path, "r", encoding="utf-8")
        mock_stat.assert_called_once_with()
        
        self.assertEqual(content, "Test file content.")
        self.assertEqual(metadata["file_name"], "test_file.txt")
        self.assertEqual(metadata["file_extension"], ".txt")
        self.assertEqual(metadata["file_stats"]["size_bytes"], 100)
        self.assertEqual(metadata["file_stats"]["created_at"], mock_stat_result.st_ctime)
        self.assertEqual(metadata["file_stats"]["modified_at"], mock_stat_result.st_mtime)

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
        # Simulate UnicodeDecodeError during read
        mock_file_open.side_effect = UnicodeDecodeError('utf-8', b'\x80abc', 0, 1, 'invalid start byte')
        
        with self.assertRaisesRegex(ValueError, "File is not a valid text file or has an unsupported encoding"):
            self.converter.convert(self.test_file_path)
            
        mock_exists.assert_called_once_with()
        mock_file_open.assert_called_once_with(self.test_file_path, "r", encoding="utf-8")

    @patch('pathlib.Path.exists', return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_convert_other_read_error(self, mock_file_open, mock_exists):
        """Test conversion propagates other file reading errors."""
        # Simulate a generic OSError during read
        mock_file_open.side_effect = OSError("Disk read error")
        
        with self.assertRaises(OSError):
            self.converter.convert(self.test_file_path)
            
        mock_exists.assert_called_once_with()
        mock_file_open.assert_called_once_with(self.test_file_path, "r", encoding="utf-8")
        
    def test_convert_accepts_string_path(self):
        """Test that convert accepts a string path argument."""
        # Use patch.object to avoid patching builtins globally for this test
        with patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'stat', return_value=MagicMock(st_size=10)), \
             patch("builtins.open", mock_open(read_data="content")):
            
            # Call convert with a string path
            content, _ = self.converter.convert(str(self.test_file_path))
            self.assertEqual(content, "content")


if __name__ == "__main__":
    unittest.main()
