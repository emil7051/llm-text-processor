"""
Unit tests for file utility functions
"""

import os
import tempfile
import unittest
from pathlib import Path

import pytest

from llm_text_processor.utils.file_utils import (
    sanitize_filename,
    ensure_dir_exists,
    find_files,
    split_path_by_extension
)


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
        # Find PDF files
        pdf_files = find_files(self.test_dir, extensions=["pdf"])
        self.assertEqual(len(pdf_files), 2)
        self.assertIn(self.pdf_file, pdf_files)
        self.assertIn(self.sub_pdf, pdf_files)
        
        # Find PDF and DOCX files
        pdf_docx_files = find_files(self.test_dir, extensions=["pdf", "docx"])
        self.assertEqual(len(pdf_docx_files), 3)
        
        # Find only in the root directory, not recursive
        root_files = find_files(self.test_dir, recursive=False)
        self.assertEqual(len(root_files), 3)
    
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


if __name__ == "__main__":
    unittest.main()
