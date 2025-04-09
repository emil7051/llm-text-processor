"""Unit tests for the PDFConverter class."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from textcleaner.converters.pdf_converter import PDFConverter
from textcleaner.utils.logging_config import get_logger
from pypdf.errors import PdfReadError
from pdfminer.pdfparser import PDFSyntaxError
from pdfminer.pdfdocument import PDFEncryptionError

# Mock logger to prevent actual logging during tests
@pytest.fixture(autouse=True)
def mock_logging():
    # Patch the logger instance directly in the module where it's used
    with patch('textcleaner.converters.pdf_converter.logger', autospec=True) as mock_log:
        yield mock_log

@pytest.fixture
def pdf_converter():
    """Fixture to create a PDFConverter instance."""
    return PDFConverter()

@pytest.fixture
def mock_path():
    """Fixture for a mocked Path object."""
    mock = MagicMock(spec=Path)
    mock.exists.return_value = True
    mock.__str__.return_value = "/fake/path/document.pdf"
    mock.name = "document.pdf" # Needed for logging if extraction fails
    return mock

# --- Test Initialization ---

def test_pdf_converter_initialization(pdf_converter):
    """Test the basic initialization of PDFConverter."""
    assert pdf_converter.supported_extensions == [".pdf"]
    # config is not used, so no need to check it specifically unless behavior changes

# --- Test convert Method (Happy Path) ---

@patch('textcleaner.converters.pdf_converter.PdfReader')
@patch('textcleaner.converters.pdf_converter.pdfminer_extract_text')
@patch.object(PDFConverter, 'get_stats', return_value={"size": 1024, "last_modified": 1234567890})
def test_convert_success(mock_get_stats, mock_extract_text, mock_pdf_reader, pdf_converter, mock_path):
    """Test successful conversion of a PDF file."""
    # --- Arrange ---
    # Mock PdfReader metadata
    mock_metadata = MagicMock()
    mock_metadata.title = "Test Title"
    mock_metadata.author = "Test Author"
    mock_metadata.subject = None # Test filtering None values
    mock_metadata.creator = "Test Creator"
    
    mock_reader_instance = MagicMock()
    mock_reader_instance.metadata = mock_metadata
    mock_reader_instance.pages = [MagicMock()] * 3 # Simulate 3 pages
    mock_pdf_reader.return_value = mock_reader_instance
    
    # Mock pdfminer text extraction
    expected_text = "This is the extracted text from the PDF."
    mock_extract_text.return_value = expected_text
    
    expected_metadata = {
        "page_count": 3,
        "file_stats": {"size": 1024, "last_modified": 1234567890},
        "title": "Test Title",
        "author": "Test Author",
        # subject should be excluded
        "creator": "Test Creator"
    }

    # --- Act ---
    text, metadata = pdf_converter.convert(mock_path)

    # --- Assert ---
    assert text == expected_text
    assert metadata == expected_metadata
    
    mock_path.exists.assert_called_once()
    mock_pdf_reader.assert_called_once_with(mock_path)
    mock_extract_text.assert_called_once_with(mock_path)
    mock_get_stats.assert_called_once_with(mock_path)

@patch('textcleaner.converters.pdf_converter.PdfReader')
@patch('textcleaner.converters.pdf_converter.pdfminer_extract_text')
@patch.object(PDFConverter, 'get_stats', return_value={"size": 500})
def test_convert_success_with_string_path(mock_get_stats, mock_extract_text, mock_pdf_reader, pdf_converter):
    """Test successful conversion when path is provided as a string."""
    # --- Arrange ---
    file_path_str = "/fake/string/path.pdf"
    
    # Mock Path object's behavior when initialized with the string
    with patch('textcleaner.converters.pdf_converter.Path') as mock_path_class:
        mock_path_instance = MagicMock(spec=Path)
        mock_path_instance.exists.return_value = True
        mock_path_instance.__str__.return_value = file_path_str
        mock_path_class.return_value = mock_path_instance

        mock_reader_instance = MagicMock()
        mock_reader_instance.metadata = None # No metadata case
        mock_reader_instance.pages = [MagicMock()] # 1 page
        mock_pdf_reader.return_value = mock_reader_instance
        
        expected_text = "Text from string path."
        mock_extract_text.return_value = expected_text
        
        expected_metadata = {
            "page_count": 1,
            "file_stats": {"size": 500}
        }

        # --- Act ---
        text, metadata = pdf_converter.convert(file_path_str)

        # --- Assert ---
        assert text == expected_text
        assert metadata == expected_metadata
        
        mock_path_class.assert_called_once_with(file_path_str)
        mock_path_instance.exists.assert_called_once()
        mock_pdf_reader.assert_called_once_with(mock_path_instance)
        mock_extract_text.assert_called_once_with(mock_path_instance)
        mock_get_stats.assert_called_once_with(mock_path_instance)

# Add more tests for edge cases and errors below...

# --- Test convert Method (Error Cases) ---

def test_convert_file_not_found(pdf_converter, mock_path):
    """Test conversion when the input file does not exist."""
    # --- Arrange ---
    mock_path.exists.return_value = False
    
    # --- Act & Assert ---
    with pytest.raises(FileNotFoundError, match="PDF file not found: /fake/path/document.pdf"):
        pdf_converter.convert(mock_path)
    
    mock_path.exists.assert_called_once()

@patch('textcleaner.converters.pdf_converter.PdfReader')
@patch.object(PDFConverter, 'get_stats', return_value={"size": 100})
def test_convert_metadata_read_error(mock_get_stats, mock_pdf_reader, pdf_converter, mock_path, mock_logging):
    """Test handling of PdfReadError during metadata extraction."""
    # --- Arrange ---
    mock_pdf_reader.side_effect = PdfReadError("Corrupted PDF")
    
    # Metadata extraction fails, but text extraction should still be attempted
    with patch('textcleaner.converters.pdf_converter.pdfminer_extract_text') as mock_extract_text:
        mock_extract_text.return_value = "Text extracted despite metadata error."
        
        expected_metadata = {
            "file_stats": {"size": 100},
            "metadata_extraction_error": "PDF read error: PdfReadError"
        }
        expected_text = "Text extracted despite metadata error."

        # --- Act ---
        text, metadata = pdf_converter.convert(mock_path)

        # --- Assert ---
        assert text == expected_text
        assert metadata == expected_metadata
        
        mock_path.exists.assert_called_once()
        mock_pdf_reader.assert_called_once_with(mock_path)
        mock_extract_text.assert_called_once_with(mock_path)
        mock_get_stats.assert_called_with(mock_path) # Called only in the error handler
        assert mock_get_stats.call_count == 1
        # Assert on the mock logger directly
        mock_logging.warning.assert_called_once_with(
            f"Could not read PDF metadata for {mock_path} (PdfReadError): Corrupted PDF"
        )

@patch('textcleaner.converters.pdf_converter.PdfReader')
@patch.object(PDFConverter, 'get_stats', return_value={"size": 100})
@patch('textcleaner.converters.pdf_converter.pdfminer_extract_text')
def test_convert_metadata_unexpected_error(mock_extract_text, mock_get_stats, mock_pdf_reader, pdf_converter, mock_path, mock_logging):
    """Test handling of unexpected Exception during metadata extraction.
    
    This should be caught by the main convert method's exception handler.
    """
    # --- Arrange ---
    mock_pdf_reader.side_effect = Exception("Something unexpected")
    # Set a return value for mock_extract_text, though it shouldn't be called
    mock_extract_text.return_value = "Should not reach here" 
    
    # --- Act & Assert ---
    # Expect a RuntimeError raised by the main convert method
    with pytest.raises(RuntimeError, match="Unexpected error converting PDF /fake/path/document.pdf: Something unexpected"):
        pdf_converter.convert(mock_path)

    # Assert that the initial exception was logged in _extract_metadata
    mock_logging.exception.assert_any_call(
        f"Unexpected error extracting PDF metadata for {mock_path}"
    )
    # Assert that the final exception was logged in convert
    mock_logging.exception.assert_any_call(
        f"Unexpected error during PDF conversion for {mock_path}"
    )
    # Assert that mock_extract_text was NOT called
    mock_extract_text.assert_not_called()
    # Assert that get_stats was NOT called (error happens before it in _extract_metadata)
    mock_get_stats.assert_not_called()

@patch('textcleaner.converters.pdf_converter.PdfReader')
@patch('textcleaner.converters.pdf_converter.pdfminer_extract_text')
@patch.object(PDFConverter, 'get_stats', return_value={"size": 100})
def test_convert_text_extraction_pdfminer_error(mock_get_stats, mock_extract_text, mock_pdf_reader, pdf_converter, mock_path, mock_logging):
    """Test handling of pdfminer errors (PDFSyntaxError)."""
    # --- Arrange ---
    # Simulate successful metadata extraction
    mock_reader_instance = MagicMock()
    mock_reader_instance.metadata = None
    mock_reader_instance.pages = [MagicMock()]
    mock_pdf_reader.return_value = mock_reader_instance
    
    # Simulate pdfminer failure
    mock_extract_text.side_effect = PDFSyntaxError("Invalid PDF structure")
    
    expected_metadata = {
        "page_count": 1,
        "file_stats": {"size": 100}
    }
    expected_text = "" # Should return empty string on pdfminer error

    # --- Act ---
    text, metadata = pdf_converter.convert(mock_path)

    # --- Assert ---
    assert text == expected_text
    assert metadata == expected_metadata
    
    mock_pdf_reader.assert_called_once_with(mock_path)
    mock_extract_text.assert_called_once_with(mock_path)
    mock_get_stats.assert_called_once_with(mock_path)
    mock_logging.error.assert_called_once_with(
        f"pdfminer extraction failed for {mock_path} (PDFSyntaxError): Invalid PDF structure"
    )

@patch('textcleaner.converters.pdf_converter.PdfReader')
@patch('textcleaner.converters.pdf_converter.pdfminer_extract_text')
@patch.object(PDFConverter, 'get_stats', return_value={"size": 100})
def test_convert_text_extraction_unexpected_error(mock_get_stats, mock_extract_text, mock_pdf_reader, pdf_converter, mock_path, mock_logging):
    """Test handling of unexpected Exception during pdfminer extraction."""
    # --- Arrange ---
    # Simulate successful metadata extraction
    mock_reader_instance = MagicMock()
    mock_reader_instance.metadata = None
    mock_reader_instance.pages = [MagicMock()]
    mock_pdf_reader.return_value = mock_reader_instance
    
    # Simulate pdfminer failure
    mock_extract_text.side_effect = Exception("Something broke in pdfminer")
    
    expected_metadata = {
        "page_count": 1,
        "file_stats": {"size": 100}
    }
    expected_text = "" # Should return empty string on unexpected pdfminer error

    # --- Act ---
    text, metadata = pdf_converter.convert(mock_path)

    # --- Assert ---
    assert text == expected_text
    assert metadata == expected_metadata
    
    mock_extract_text.assert_called_once_with(mock_path)
    mock_logging.exception.assert_called_once_with(
        f"Unexpected error during pdfminer extraction for {mock_path}"
    )

@patch('textcleaner.converters.pdf_converter.PdfReader')
@patch('textcleaner.converters.pdf_converter.pdfminer_extract_text')
@patch.object(PDFConverter, 'get_stats', return_value={"size": 100})
def test_convert_empty_text_extraction(mock_get_stats, mock_extract_text, mock_pdf_reader, pdf_converter, mock_path, mock_logging):
    """Test the case where pdfminer returns an empty string."""
    # --- Arrange ---
    # Simulate successful metadata extraction
    mock_reader_instance = MagicMock()
    mock_reader_instance.metadata = None
    mock_reader_instance.pages = [MagicMock()]
    mock_pdf_reader.return_value = mock_reader_instance
    
    # Simulate pdfminer returning empty text
    mock_extract_text.return_value = ""
    
    expected_metadata = {
        "page_count": 1,
        "file_stats": {"size": 100}
    }
    expected_text = ""

    # --- Act ---
    text, metadata = pdf_converter.convert(mock_path)

    # --- Assert ---
    assert text == expected_text
    assert metadata == expected_metadata
    
    mock_extract_text.assert_called_once_with(mock_path)
    # Verify warning is logged
    mock_logging.warning.assert_called_once_with(
         f"PDF text extraction yielded empty result for: {mock_path}"
    )

@patch('textcleaner.converters.pdf_converter.PdfReader', side_effect=Exception("Top level failure"))
def test_convert_unexpected_general_exception(mock_pdf_reader, pdf_converter, mock_path, mock_logging):
    """Test handling of an unexpected exception in the main convert method."""
    # --- Arrange ---
    # Exception raised before text extraction is even called
    
    # --- Act & Assert ---
    with pytest.raises(RuntimeError, match="Unexpected error converting PDF /fake/path/document.pdf: Top level failure"):
        pdf_converter.convert(mock_path)
        
    # Check that the final error message was logged
    mock_logging.exception.assert_any_call(
        "Unexpected error during PDF conversion for /fake/path/document.pdf"
    )

# Parametrize pdfminer known error types
@pytest.mark.parametrize("error_type, error_msg", [
    (PDFSyntaxError, "Bad syntax"),
    (PDFEncryptionError, "Encrypted file"),
    (OSError, "Cannot open file")
])
@patch('textcleaner.converters.pdf_converter.PdfReader')
@patch('textcleaner.converters.pdf_converter.pdfminer_extract_text')
@patch.object(PDFConverter, 'get_stats', return_value={"size": 100})
def test_convert_text_extraction_pdfminer_known_errors(mock_get_stats, mock_extract_text, mock_pdf_reader, pdf_converter, mock_path, mock_logging, error_type, error_msg):
    """Test handling of various known pdfminer errors."""
    # --- Arrange ---
    mock_reader_instance = MagicMock()
    mock_reader_instance.metadata = None
    mock_reader_instance.pages = [MagicMock()]
    mock_pdf_reader.return_value = mock_reader_instance
    
    mock_extract_text.side_effect = error_type(error_msg)
    
    expected_metadata = {
        "page_count": 1,
        "file_stats": {"size": 100}
    }
    expected_text = ""

    # --- Act ---
    text, metadata = pdf_converter.convert(mock_path)

    # --- Assert ---
    assert text == expected_text
    assert metadata == expected_metadata
    
    mock_extract_text.assert_called_once_with(mock_path)
    mock_logging.error.assert_called_once_with(
        f"pdfminer extraction failed for {mock_path} ({error_type.__name__}): {error_msg}"
    ) 