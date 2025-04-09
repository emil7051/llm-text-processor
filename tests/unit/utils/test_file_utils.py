"""
Unit tests for file utility functions
"""

import os
import tempfile
import unittest
from pathlib import Path

import pytest

from textcleaner.utils.file_utils import (
    sanitize_filename,
    ensure_dir_exists,
    find_files,
    split_path_by_extension,
    resolve_output_dir,
    determine_output_format_and_extension
)
from textcleaner.config.config_manager import ConfigManager
from textcleaner.utils.security import SecurityUtils
from textcleaner.core.file_registry import FileTypeRegistry
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestFileUtils(unittest.TestCase):
    """Test suite for file utility functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create some test files
        self.pdf_file = self.test_dir / "test_doc.pdf"
        self.docx_file = self.test_dir / "test_doc.docx"
        self.txt_file = self.test_dir / "test_doc.txt"
        
        # Create the files
        self.pdf_file.touch()
        self.docx_file.touch()
        self.txt_file.touch()
        
        # Create a subdirectory with files
        self.sub_dir = self.test_dir / "subdir"
        self.sub_dir.mkdir()
        
        self.sub_pdf = self.sub_dir / "subdir_doc.pdf"
        self.sub_pdf.touch()
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.temp_dir.cleanup()
    
    def test_sanitize_filename(self):
        """Test sanitizing filenames to be safe for filesystems"""
        # Test removing invalid characters
        self.assertEqual(sanitize_filename("file/with/slashes.txt"), "file_with_slashes.txt")
        
        # Test removing reserved characters
        self.assertEqual(sanitize_filename("file:with:colons.txt"), "file_with_colons.txt")
        
        # Test removing control characters
        self.assertEqual(sanitize_filename("file\nwith\tnewlines.txt"), "file_with_newlines.txt")
    
    def test_ensure_dir_exists(self):
        """Test ensuring a directory exists"""
        # Test creating a new directory
        new_dir = self.test_dir / "new_dir"
        result = ensure_dir_exists(new_dir)
        
        self.assertTrue(new_dir.exists())
        self.assertTrue(new_dir.is_dir())
        self.assertEqual(result, new_dir)
        
        # Test with an existing directory
        result = ensure_dir_exists(new_dir)
        self.assertEqual(result, new_dir)
    
    def test_find_files(self):
        """Test finding files with specific extensions"""
        # Find all files recursively first
        all_files = list(find_files(self.test_dir, recursive=True))
        
        # Filter for PDF files
        pdf_files = [f for f in all_files if f.suffix.lower() == ".pdf"]
        assert len(pdf_files) == 2
        assert self.pdf_file in pdf_files
        assert self.sub_pdf in pdf_files

        # Filter for TXT files (non-recursively)
        txt_files_non_recursive = list(find_files(self.test_dir, recursive=False))
        txt_files_non_recursive = [f for f in txt_files_non_recursive if f.suffix.lower() == ".txt"]
        assert len(txt_files_non_recursive) == 1
        assert self.txt_file in txt_files_non_recursive
        assert self.sub_dir / "subdir_doc.txt" not in txt_files_non_recursive

        # Filter for TXT files (recursively)
        txt_files_recursive = [f for f in all_files if f.suffix.lower() == ".txt"]
        assert len(txt_files_recursive) == 1
        assert self.txt_file in txt_files_recursive

    def test_find_files_non_existent(self):
        """Test finding files in a non-existent directory"""
        non_existent_dir = self.test_dir / "nonexistent"
        with self.assertRaises(FileNotFoundError):
            list(find_files(non_existent_dir))
    
    def test_split_path_by_extension(self):
        """Test splitting a path into base and extension"""
        # Test with a PDF file
        base, ext = split_path_by_extension(self.pdf_file)
        self.assertEqual(base, self.test_dir / "test_doc")
        self.assertEqual(ext, ".pdf")
        
        # Test with a file with no extension
        no_ext_file = self.test_dir / "file_without_extension"
        no_ext_file.touch()
        
        base, ext = split_path_by_extension(no_ext_file)
        self.assertEqual(base, no_ext_file)
        self.assertEqual(ext, "")

    # --- Tests for resolve_output_dir ---

    @patch('textcleaner.utils.file_utils.ensure_dir_exists')
    @patch('textcleaner.utils.security.SecurityUtils')
    @patch('textcleaner.config.config_manager.ConfigManager')
    def test_resolve_output_dir_param_provided_str(self, MockConfigManager, MockSecurityUtils, mock_ensure_dir):
        """Test resolving output dir when a string path is provided."""
        mock_config = MockConfigManager()
        mock_security = MockSecurityUtils()
        mock_security.validate_output_path.return_value = (True, None)
        output_dir_str = "some/output/dir"
        expected_path = Path(output_dir_str)

        result_path = resolve_output_dir(output_dir_str, mock_config, mock_security)

        self.assertEqual(result_path, expected_path)
        mock_security.validate_output_path.assert_called_once_with(expected_path)
        mock_ensure_dir.assert_called_once_with(expected_path)
        mock_config.get.assert_not_called() # Config should not be used

    @patch('textcleaner.utils.file_utils.ensure_dir_exists')
    @patch('textcleaner.utils.security.SecurityUtils')
    @patch('textcleaner.config.config_manager.ConfigManager')
    def test_resolve_output_dir_param_provided_path(self, MockConfigManager, MockSecurityUtils, mock_ensure_dir):
        """Test resolving output dir when a Path object is provided."""
        mock_config = MockConfigManager()
        mock_security = MockSecurityUtils()
        mock_security.validate_output_path.return_value = (True, None)
        output_dir_path = Path("some/output/path_obj")

        result_path = resolve_output_dir(output_dir_path, mock_config, mock_security)

        self.assertEqual(result_path, output_dir_path)
        mock_security.validate_output_path.assert_called_once_with(output_dir_path)
        mock_ensure_dir.assert_called_once_with(output_dir_path)
        mock_config.get.assert_not_called()

    @patch('textcleaner.utils.file_utils.ensure_dir_exists')
    @patch('textcleaner.utils.security.SecurityUtils')
    @patch('textcleaner.config.config_manager.ConfigManager')
    def test_resolve_output_dir_param_none_uses_config(self, MockConfigManager, MockSecurityUtils, mock_ensure_dir):
        """Test resolving output dir uses config when param is None."""
        mock_config = MockConfigManager()
        mock_security = MockSecurityUtils()
        mock_config.get.return_value = "config/default/dir"
        mock_security.validate_output_path.return_value = (True, None)
        expected_path = Path("config/default/dir")

        result_path = resolve_output_dir(None, mock_config, mock_security)

        self.assertEqual(result_path, expected_path)
        mock_config.get.assert_called_once_with("general.output_dir", "processed_files")
        mock_security.validate_output_path.assert_called_once_with(expected_path)
        mock_ensure_dir.assert_called_once_with(expected_path)

    @patch('textcleaner.utils.file_utils.ensure_dir_exists')
    @patch('textcleaner.utils.security.SecurityUtils')
    @patch('textcleaner.config.config_manager.ConfigManager')
    def test_resolve_output_dir_validation_fails(self, MockConfigManager, MockSecurityUtils, mock_ensure_dir):
        """Test resolving output dir raises PermissionError on validation failure."""
        mock_config = MockConfigManager()
        mock_security = MockSecurityUtils()
        output_dir_str = "invalid/dir"
        expected_path = Path(output_dir_str)
        mock_security.validate_output_path.return_value = (False, "Path is outside project")

        with self.assertRaisesRegex(PermissionError, "Output directory validation failed: Path is outside project"):
            resolve_output_dir(output_dir_str, mock_config, mock_security)

        mock_security.validate_output_path.assert_called_once_with(expected_path)
        mock_ensure_dir.assert_not_called() # Should not try to create dir if invalid

    @patch('textcleaner.utils.file_utils.ensure_dir_exists', side_effect=OSError("Disk full"))
    @patch('textcleaner.utils.security.SecurityUtils')
    @patch('textcleaner.config.config_manager.ConfigManager')
    def test_resolve_output_dir_creation_fails(self, MockConfigManager, MockSecurityUtils, mock_ensure_dir):
        """Test resolving output dir raises RuntimeError if ensure_dir_exists fails."""
        mock_config = MockConfigManager()
        mock_security = MockSecurityUtils()
        mock_security.validate_output_path.return_value = (True, None)
        output_dir_str = "some/dir"
        expected_path = Path(output_dir_str)

        with self.assertRaisesRegex(RuntimeError, f"Failed to create output directory {expected_path}: Disk full"):
            resolve_output_dir(output_dir_str, mock_config, mock_security)

        mock_security.validate_output_path.assert_called_once_with(expected_path)
        mock_ensure_dir.assert_called_once_with(expected_path)

    # --- Tests for determine_output_format_and_extension ---
    # TODO: Add tests here
    def test_determine_format_explicit_param(self):
        """Test format is determined by explicit parameter first."""
        mock_config = MagicMock(spec=ConfigManager)
        mock_registry = MagicMock(spec=FileTypeRegistry)
        mock_registry.get_default_extension.return_value = "json_ext"
        mock_config.get.side_effect = lambda key, default=None: {
            "output.default_format": "markdown", # Should be ignored
            "general.file_extension_mapping.json": "config_json" # Should be used
        }.get(key, default)

        fmt, ext = determine_output_format_and_extension(
            output_format_param="json",
            output_path_param=Path("output/file.txt"), # Should be ignored for format
            config=mock_config,
            file_registry=mock_registry
        )

        self.assertEqual(fmt, "json")
        self.assertEqual(ext, "config_json") # Extension from config mapping
        mock_config.get.assert_any_call("general.file_extension_mapping.json", None)
        mock_registry.get_default_extension.assert_not_called() # Not called because config had mapping

    def test_determine_format_guessed_from_path(self):
        """Test format is guessed from output_path_param if format param is None."""
        mock_config = MagicMock(spec=ConfigManager)
        mock_registry = MagicMock(spec=FileTypeRegistry)
        mock_registry.get_default_extension.return_value = "txt_ext" # Default from registry
        mock_config.get.side_effect = lambda key, default=None: {
            "output.default_format": "markdown", # Should be ignored
            "general.file_extension_mapping.plain_text": None # Simulate no mapping
        }.get(key, default)

        fmt, ext = determine_output_format_and_extension(
            output_format_param=None,
            output_path_param=Path("output/file.txt"),
            config=mock_config,
            file_registry=mock_registry
        )

        self.assertEqual(fmt, "plain_text") # Guessed from .txt
        self.assertEqual(ext, "txt_ext") # Extension from registry
        mock_config.get.assert_any_call("general.file_extension_mapping.plain_text", None)
        mock_registry.get_default_extension.assert_called_once_with("plain_text") # Expect only format_name

    def test_determine_format_from_config_default(self):
        """Test format uses config default if params are None/uninformative."""
        mock_config = MagicMock(spec=ConfigManager)
        mock_registry = MagicMock(spec=FileTypeRegistry)
        mock_registry.get_default_extension.return_value = "md_ext"
        mock_config.get.side_effect = lambda key, default=None: {
            "output.default_format": "markdown",
            "general.file_extension_mapping.markdown": None # Simulate no mapping
        }.get(key, default)

        fmt, ext = determine_output_format_and_extension(
            output_format_param=None,
            output_path_param=Path("output/file_no_ext"), # No informative extension
            config=mock_config,
            file_registry=mock_registry
        )

        self.assertEqual(fmt, "markdown") # From config default
        self.assertEqual(ext, "md_ext")   # Extension from registry
        mock_config.get.assert_any_call("output.default_format", "markdown")
        mock_config.get.assert_any_call("general.file_extension_mapping.markdown", None)
        mock_registry.get_default_extension.assert_called_once_with("markdown") # Expect only format_name

    def test_determine_extension_from_config_mapping(self):
        """Test extension uses config mapping even if registry differs."""
        mock_config = MagicMock(spec=ConfigManager)
        mock_registry = MagicMock(spec=FileTypeRegistry)
        mock_registry.get_default_extension.return_value = "md_registry"
        mock_config.get.side_effect = lambda key, default=None: {
            "output.default_format": "markdown",
            "general.file_extension_mapping.markdown": "md_config" # Mapping exists
        }.get(key, default)

        fmt, ext = determine_output_format_and_extension(
            output_format_param="markdown",
            output_path_param=None,
            config=mock_config,
            file_registry=mock_registry
        )

        self.assertEqual(fmt, "markdown")
        self.assertEqual(ext, "md_config") # Extension from config mapping
        mock_config.get.assert_any_call("general.file_extension_mapping.markdown", None)
        mock_registry.get_default_extension.assert_not_called()

    def test_determine_extension_registry_fallback(self):
        """Test extension falls back to registry if no config mapping."""
        mock_config = MagicMock(spec=ConfigManager)
        mock_registry = MagicMock(spec=FileTypeRegistry)
        mock_registry.get_default_extension.return_value = "csv_registry"
        mock_config.get.side_effect = lambda key, default=None: {
            "output.default_format": "csv",
            "general.file_extension_mapping.csv": None # No mapping
        }.get(key, default)

        fmt, ext = determine_output_format_and_extension(
            output_format_param="csv",
            output_path_param=None,
            config=mock_config,
            file_registry=mock_registry
        )

        self.assertEqual(fmt, "csv")
        self.assertEqual(ext, "csv_registry") # Extension from registry
        mock_config.get.assert_any_call("general.file_extension_mapping.csv", None)
        mock_registry.get_default_extension.assert_called_once_with("csv") # Expect only format_name

    def test_determine_extension_registry_key_error(self):
        """Test fallback extension if format is somehow not in registry."""
        mock_config = MagicMock(spec=ConfigManager)
        mock_registry = MagicMock(spec=FileTypeRegistry)
        # Simulate format not being found in the registry
        mock_registry.get_default_extension.side_effect = KeyError("Format 'custom' not found")
        mock_config.get.side_effect = lambda key, default=None: {
            "output.default_format": "custom", # Default to a custom format
            "general.file_extension_mapping.custom": None # No mapping
        }.get(key, default)

        fmt, ext = determine_output_format_and_extension(
            output_format_param="custom",
            output_path_param=None,
            config=mock_config,
            file_registry=mock_registry
        )

        self.assertEqual(fmt, "custom")
        self.assertEqual(ext, "custom") # Falls back to the format name itself
        mock_registry.get_default_extension.assert_called_once_with("custom") # Expect only format_name

    def test_determine_extension_registry_value_error(self):
        """Test raises ValueError if registry is invalid."""
        mock_config = MagicMock(spec=ConfigManager)
        # Pass an invalid object instead of a registry
        invalid_registry = object()
        mock_config.get.side_effect = lambda key, default=None: {
            "output.default_format": "markdown",
            "general.file_extension_mapping.markdown": None
        }.get(key, default)

        with self.assertRaisesRegex(ValueError, "Error getting default extension: Invalid or missing FileTypeRegistry"):
            determine_output_format_and_extension(
                output_format_param="markdown",
                output_path_param=None,
                config=mock_config,
                file_registry=invalid_registry # Pass invalid registry
            )


if __name__ == "__main__":
    unittest.main()
