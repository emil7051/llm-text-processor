"""
Tests for the FileTypeRegistry class
"""

import pytest
from pathlib import Path

from textcleaner.core.file_registry import FileTypeRegistry


@pytest.fixture
def file_registry():
    """Create a FileTypeRegistry instance for testing"""
    return FileTypeRegistry()


def test_get_default_extension(file_registry):
    """Test getting default extensions for formats"""
    assert file_registry.get_default_extension("markdown") == "md"
    assert file_registry.get_default_extension("plain_text") == "txt"
    assert file_registry.get_default_extension("json") == "json"
    assert file_registry.get_default_extension("csv") == "csv"
    
    # Test with unknown format (should return default)
    assert file_registry.get_default_extension("unknown_format") == "txt"
    
    # Test case insensitivity
    assert file_registry.get_default_extension("MARKDOWN") == "md"


def test_is_supported_extension(file_registry):
    """Test checking if file extensions are supported"""
    # Create some test paths
    pdf_path = Path("test.pdf")
    docx_path = Path("test.docx")
    invalid_path = Path("test.xyz")
    
    # Check supported extensions
    assert file_registry.is_supported_extension(pdf_path)
    assert file_registry.is_supported_extension(docx_path)
    
    # Check unsupported extension
    assert not file_registry.is_supported_extension(invalid_path)


def test_should_process_file(file_registry):
    """Test determining if a file should be processed"""
    # Create test paths
    pdf_path = Path("test.pdf")
    docx_path = Path("test.docx")
    invalid_path = Path("test.xyz")
    
    # Test with no file extensions filter
    assert file_registry.should_process_file(pdf_path)
    assert file_registry.should_process_file(docx_path)
    assert not file_registry.should_process_file(invalid_path)
    
    # Test with file extensions filter
    pdf_extensions = [".pdf"]
    assert file_registry.should_process_file(pdf_path, pdf_extensions)
    assert not file_registry.should_process_file(docx_path, pdf_extensions)


def test_get_supported_formats(file_registry):
    """Test getting supported formats for a file"""
    # Create test paths
    pdf_path = Path("test.pdf")
    docx_path = Path("test.docx")
    invalid_path = Path("test.xyz")
    
    # Check supported formats
    pdf_formats = file_registry.get_supported_formats(pdf_path)
    assert "markdown" in pdf_formats
    assert "plain_text" in pdf_formats
    
    docx_formats = file_registry.get_supported_formats(docx_path)
    assert "markdown" in docx_formats
    assert "plain_text" in docx_formats
    
    # Check unsupported file
    assert file_registry.get_supported_formats(invalid_path) == []


def test_get_all_supported_extensions(file_registry):
    """Test getting all supported extensions"""
    extensions = file_registry.get_all_supported_extensions()
    
    # Verify common extensions are included
    assert ".pdf" in extensions
    assert ".docx" in extensions
    assert ".html" in extensions
    assert ".txt" in extensions
    assert ".md" in extensions


def test_register_extension(file_registry):
    """Test registering a new file extension"""
    # Create a custom extension
    custom_ext = ".custom"
    custom_formats = ["markdown", "plain_text"]
    
    # Verify it's not initially supported
    assert not file_registry.is_supported_extension(Path("test.custom"))
    
    # Register the extension
    file_registry.register_extension(custom_ext, custom_formats)
    
    # Verify it's now supported
    assert file_registry.is_supported_extension(Path("test.custom"))
    assert file_registry.get_supported_formats(Path("test.custom")) == custom_formats
    
    # Test registration without leading dot
    file_registry.register_extension("another", ["markdown"])
    assert file_registry.is_supported_extension(Path("test.another"))


def test_register_format(file_registry):
    """Test registering a new output format"""
    # Register a new format
    file_registry.register_format("custom_format", "cst")
    
    # Verify the format is registered
    assert file_registry.get_default_extension("custom_format") == "cst"
    
    # Test with leading dot in extension
    file_registry.register_format("another_format", ".anf")
    assert file_registry.get_default_extension("another_format") == "anf"
