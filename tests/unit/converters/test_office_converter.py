import unittest
import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path

# Import the class to test
from textcleaner.converters.office_converter import OfficeConverter
from textcleaner.config.config_manager import ConfigManager

# Import exceptions that might be raised or caught
from docx.opc.exceptions import PackageNotFoundError
from pptx.exc import PackageNotFoundError as PptxPackageNotFoundError
import pandas as pd


@pytest.mark.unit
class TestOfficeConverter(unittest.TestCase):
    """Test suite for the OfficeConverter."""

    def setUp(self):
        """Set up test fixtures for each test."""
        self.mock_config = MagicMock(spec=ConfigManager)
        # Provide default config values if needed by the converter's __init__ or methods
        # self.mock_config.get.return_value = ... 
        
        self.extract_comments = False
        self.extract_tracked_changes = False
        self.extract_hidden_content = False
        self.max_excel_rows = 1000
        self.max_excel_cols = 100
        
        self.converter = OfficeConverter(
            extract_comments=self.extract_comments,
            extract_tracked_changes=self.extract_tracked_changes,
            extract_hidden_content=self.extract_hidden_content,
            max_excel_rows=self.max_excel_rows,
            max_excel_cols=self.max_excel_cols,
            config=self.mock_config
        )
        
        # Create a dummy file path for tests that need a path object
        self.dummy_path = Path("dummy/path/doc.docx")

    def test_init_stores_configuration(self):
        """Test that the constructor stores configuration values."""
        self.assertEqual(self.converter.extract_comments, self.extract_comments)
        self.assertEqual(self.converter.extract_tracked_changes, self.extract_tracked_changes)
        self.assertEqual(self.converter.extract_hidden_content, self.extract_hidden_content)
        self.assertEqual(self.converter.max_excel_rows, self.max_excel_rows)
        self.assertEqual(self.converter.max_excel_cols, self.max_excel_cols)
        self.assertIn(".docx", self.converter.supported_extensions)
        self.assertIn(".xlsx", self.converter.supported_extensions)
        self.assertIn(".pptx", self.converter.supported_extensions)
        self.assertIn(".odt", self.converter.supported_extensions) # Check OpenDocument too

    # Patch the internal methods and Path.exists to test routing
    @patch.object(OfficeConverter, '_convert_word_document')
    @patch('pathlib.Path.exists', return_value=True)
    def test_convert_routes_docx(self, mock_exists, mock_convert_word):
        """Test that .docx files are routed to the Word converter."""
        test_path = Path("test.docx")
        mock_convert_word.return_value = ("word text", {"meta": "data"})
        
        result_text, result_meta = self.converter.convert(test_path)
        
        mock_exists.assert_called_once()
        mock_convert_word.assert_called_once_with(test_path)
        self.assertEqual(result_text, "word text")
        self.assertEqual(result_meta, {"meta": "data"})

    @patch.object(OfficeConverter, '_convert_excel_spreadsheet')
    @patch('pathlib.Path.exists', return_value=True)
    def test_convert_routes_xlsx(self, mock_exists, mock_convert_excel):
        """Test that .xlsx files are routed to the Excel converter."""
        test_path = Path("test.xlsx")
        mock_convert_excel.return_value = ("excel text", {"meta": "data"})
        
        result_text, result_meta = self.converter.convert(test_path)
        
        mock_exists.assert_called_once()
        mock_convert_excel.assert_called_once_with(test_path)
        self.assertEqual(result_text, "excel text")
        self.assertEqual(result_meta, {"meta": "data"})

    @patch.object(OfficeConverter, '_convert_powerpoint_presentation')
    @patch('pathlib.Path.exists', return_value=True)
    def test_convert_routes_pptx(self, mock_exists, mock_convert_ppt):
        """Test that .pptx files are routed to the PowerPoint converter."""
        test_path = Path("test.pptx")
        mock_convert_ppt.return_value = ("ppt text", {"meta": "data"})
        
        result_text, result_meta = self.converter.convert(test_path)
        
        mock_exists.assert_called_once()
        mock_convert_ppt.assert_called_once_with(test_path)
        self.assertEqual(result_text, "ppt text")
        self.assertEqual(result_meta, {"meta": "data"})
        
    @patch.object(OfficeConverter, '_convert_word_document')
    @patch('pathlib.Path.exists', return_value=True)
    def test_convert_routes_odt(self, mock_exists, mock_convert_word):
        """Test that .odt files are routed to the Word converter."""
        test_path = Path("test.odt")
        mock_convert_word.return_value = ("odt text", {"meta": "data"})
        self.converter.convert(test_path)
        mock_convert_word.assert_called_once_with(test_path)

    @patch.object(OfficeConverter, '_convert_excel_spreadsheet')
    @patch('pathlib.Path.exists', return_value=True)
    def test_convert_routes_ods(self, mock_exists, mock_convert_excel):
        """Test that .ods files are routed to the Excel converter."""
        test_path = Path("test.ods")
        mock_convert_excel.return_value = ("ods text", {"meta": "data"})
        self.converter.convert(test_path)
        mock_convert_excel.assert_called_once_with(test_path)

    @patch.object(OfficeConverter, '_convert_powerpoint_presentation')
    @patch('pathlib.Path.exists', return_value=True)
    def test_convert_routes_odp(self, mock_exists, mock_convert_ppt):
        """Test that .odp files are routed to the PowerPoint converter."""
        test_path = Path("test.odp")
        mock_convert_ppt.return_value = ("odp text", {"meta": "data"})
        self.converter.convert(test_path)
        mock_convert_ppt.assert_called_once_with(test_path)

    @patch('pathlib.Path.exists', return_value=True)
    def test_convert_unsupported_extension_raises_value_error(self, mock_exists):
        """Test that an unsupported file extension raises the correct exception."""
        test_path = Path("test.unsupported")
        # Check that the correct RuntimeError is raised due to the internal ValueError
        with self.assertRaisesRegex(RuntimeError, "Failed to process Office file: Unsupported office document format: .unsupported"):
            self.converter.convert(test_path)
        mock_exists.assert_called_once() # Ensure it checked existence first

    @patch('pathlib.Path.exists', return_value=False)
    def test_convert_file_not_found_raises_error(self, mock_exists):
        """Test that a non-existent file raises FileNotFoundError."""
        test_path = Path("non_existent_file.docx")
        with self.assertRaises(FileNotFoundError):
            self.converter.convert(test_path)
        mock_exists.assert_called_once()

    # --- Tests for _convert_word_document ---

    @patch('textcleaner.converters.office_converter.docx.Document')
    @patch('textcleaner.converters.office_converter.op_utils.process_docx')
    @patch.object(OfficeConverter, 'get_stats', return_value={"size": 100})
    def test_convert_word_docx_success(self, mock_get_stats, mock_process_docx, mock_docx_doc):
        """Test successful conversion of a .docx file."""
        test_path = Path("test.docx")
        mock_doc_instance = MagicMock()
        mock_docx_doc.return_value = mock_doc_instance
        mock_process_docx.return_value = ("word content", {"doc_prop": "val"})
        
        text, metadata = self.converter._convert_word_document(test_path)
        
        mock_docx_doc.assert_called_once_with(test_path)
        mock_process_docx.assert_called_once_with(test_path, mock_doc_instance)
        mock_get_stats.assert_called_once_with(test_path)
        self.assertEqual(text, "word content")
        self.assertEqual(metadata, {"file_stats": {"size": 100}, "doc_prop": "val"})

    @patch('textcleaner.converters.office_converter.docx.Document', side_effect=PackageNotFoundError("Not found"))
    def test_convert_word_docx_package_not_found(self, mock_docx_doc):
        """Test .docx conversion when the package cannot be found/read."""
        test_path = Path("corrupt.docx")
        with self.assertRaisesRegex(RuntimeError, "Could not read DOCX file: Not found"):
            self.converter._convert_word_document(test_path)
        mock_docx_doc.assert_called_once_with(test_path)
        
    @patch('textcleaner.converters.office_converter.docx.Document')
    @patch('textcleaner.converters.office_converter.op_utils.process_docx', side_effect=Exception("Processing failed"))
    def test_convert_word_docx_processing_exception(self, mock_process_docx, mock_docx_doc):
        """Test .docx conversion when op_utils.process_docx raises an exception."""
        test_path = Path("error.docx")
        mock_doc_instance = MagicMock()
        mock_docx_doc.return_value = mock_doc_instance
        
        with self.assertRaisesRegex(RuntimeError, "Unexpected error converting DOCX: Processing failed"):
            self.converter._convert_word_document(test_path)
            
        mock_docx_doc.assert_called_once_with(test_path)
        mock_process_docx.assert_called_once_with(test_path, mock_doc_instance)

    @patch.object(OfficeConverter, 'get_stats', return_value={"size": 50})
    def test_convert_word_doc_odt_placeholder(self, mock_get_stats):
        """Test conversion of legacy .doc and .odt returns placeholder."""
        for ext in [".doc", ".odt"]:
            with self.subTest(extension=ext):
                test_path = Path(f"legacy{ext}")
                text, metadata = self.converter._convert_word_document(test_path)
                self.assertIn(f"format ({ext}) requires additional processing", text)
                self.assertIn(test_path.name, text)
                self.assertEqual(metadata, {"file_stats": {"size": 50}})
                mock_get_stats.assert_called_with(test_path)

    # --- Tests for _convert_excel_spreadsheet ---

    @patch('textcleaner.converters.office_converter.pd.ExcelFile')
    @patch('textcleaner.converters.office_converter.op_utils.process_excel')
    @patch.object(OfficeConverter, 'get_stats', return_value={"size": 200})
    def test_convert_excel_xlsx_success(self, mock_get_stats, mock_process_excel, mock_excel_file):
        """Test successful conversion of a .xlsx file."""
        test_path = Path("test.xlsx")
        mock_excel_instance = MagicMock()
        mock_excel_file.return_value = mock_excel_instance
        mock_process_excel.return_value = ("excel content", {"sheet_names": ["Sheet1"]})
        
        text, metadata = self.converter._convert_excel_spreadsheet(test_path)
        
        mock_excel_file.assert_called_once_with(test_path, engine='openpyxl')
        mock_process_excel.assert_called_once_with(
            test_path, mock_excel_instance, self.max_excel_rows, self.max_excel_cols
        )
        mock_get_stats.assert_called_once_with(test_path)
        self.assertEqual(text, "excel content")
        self.assertEqual(metadata, {"file_stats": {"size": 200}, "sheet_names": ["Sheet1"]})

    @patch('textcleaner.converters.office_converter.pd.ExcelFile')
    @patch('textcleaner.converters.office_converter.op_utils.process_excel')
    @patch.object(OfficeConverter, 'get_stats', return_value={"size": 150})
    def test_convert_excel_xls_success(self, mock_get_stats, mock_process_excel, mock_excel_file):
        """Test successful conversion of a legacy .xls file uses xlrd engine."""
        test_path = Path("test.xls")
        mock_excel_instance = MagicMock()
        mock_excel_file.return_value = mock_excel_instance
        mock_process_excel.return_value = ("xls content", {"sheets": 1})
        
        text, metadata = self.converter._convert_excel_spreadsheet(test_path)
        
        mock_excel_file.assert_called_once_with(test_path, engine='xlrd') # Check engine
        mock_process_excel.assert_called_once_with(
            test_path, mock_excel_instance, self.max_excel_rows, self.max_excel_cols
        )
        mock_get_stats.assert_called_once_with(test_path)
        self.assertEqual(text, "xls content")
        self.assertEqual(metadata, {"file_stats": {"size": 150}, "sheets": 1})
        
    @patch('textcleaner.converters.office_converter.pd.ExcelFile', side_effect=pd.errors.ParserError("Bad format"))
    def test_convert_excel_parser_error(self, mock_excel_file):
        """Test Excel conversion handles pandas ParserError."""
        test_path = Path("bad.xlsx")
        with self.assertRaisesRegex(RuntimeError, "Error extracting text from Excel file: Bad format"):
            self.converter._convert_excel_spreadsheet(test_path)
        mock_excel_file.assert_called_once_with(test_path, engine='openpyxl')
        
    @patch('textcleaner.converters.office_converter.pd.ExcelFile', side_effect=IOError("Cannot open"))
    def test_convert_excel_io_error(self, mock_excel_file):
        """Test Excel conversion handles IOError."""
        test_path = Path("locked.xlsx")
        with self.assertRaisesRegex(RuntimeError, "Error extracting text from Excel file: Cannot open"):
            self.converter._convert_excel_spreadsheet(test_path)
        mock_excel_file.assert_called_once_with(test_path, engine='openpyxl')

    @patch('textcleaner.converters.office_converter.pd.ExcelFile')
    @patch('textcleaner.converters.office_converter.op_utils.process_excel', side_effect=Exception("Processing failed"))
    def test_convert_excel_processing_exception(self, mock_process_excel, mock_excel_file):
        """Test Excel conversion when op_utils.process_excel raises an exception."""
        test_path = Path("error.xlsx")
        mock_excel_instance = MagicMock()
        mock_excel_file.return_value = mock_excel_instance
        
        with self.assertRaisesRegex(RuntimeError, "Error extracting text from Excel file: Processing failed"):
            self.converter._convert_excel_spreadsheet(test_path)
            
        mock_excel_file.assert_called_once_with(test_path, engine='openpyxl')
        mock_process_excel.assert_called_once_with(
            test_path, mock_excel_instance, self.max_excel_rows, self.max_excel_cols
        )

    # --- Tests for _convert_powerpoint_presentation ---

    @patch('textcleaner.converters.office_converter.Presentation')
    @patch('textcleaner.converters.office_converter.op_utils.process_pptx')
    @patch.object(OfficeConverter, 'get_stats', return_value={"size": 300})
    def test_convert_powerpoint_pptx_success(self, mock_get_stats, mock_process_pptx, mock_presentation):
        """Test successful conversion of a .pptx file."""
        test_path = Path("test.pptx")
        mock_prs_instance = MagicMock()
        mock_presentation.return_value = mock_prs_instance
        mock_process_pptx.return_value = ("ppt content", {"slides": 10})
        
        text, metadata = self.converter._convert_powerpoint_presentation(test_path)
        
        mock_presentation.assert_called_once_with(test_path)
        mock_process_pptx.assert_called_once_with(test_path, mock_prs_instance)
        mock_get_stats.assert_called_once_with(test_path)
        self.assertEqual(text, "ppt content")
        self.assertEqual(metadata, {"file_stats": {"size": 300}, "slides": 10})

    @patch('textcleaner.converters.office_converter.Presentation', side_effect=PptxPackageNotFoundError("Corrupt"))
    def test_convert_powerpoint_pptx_package_not_found(self, mock_presentation):
        """Test .pptx conversion when the package cannot be found/read."""
        test_path = Path("corrupt.pptx")
        with self.assertRaisesRegex(RuntimeError, "Could not read PPTX file: Corrupt"):
            self.converter._convert_powerpoint_presentation(test_path)
        mock_presentation.assert_called_once_with(test_path)
        
    @patch('textcleaner.converters.office_converter.Presentation')
    @patch('textcleaner.converters.office_converter.op_utils.process_pptx', side_effect=Exception("Processing error"))
    def test_convert_powerpoint_pptx_processing_exception(self, mock_process_pptx, mock_presentation):
        """Test .pptx conversion when op_utils.process_pptx raises an exception."""
        test_path = Path("error.pptx")
        mock_prs_instance = MagicMock()
        mock_presentation.return_value = mock_prs_instance
        
        with self.assertRaisesRegex(RuntimeError, "Unexpected error converting PPTX: Processing error"):
            self.converter._convert_powerpoint_presentation(test_path)
            
        mock_presentation.assert_called_once_with(test_path)
        mock_process_pptx.assert_called_once_with(test_path, mock_prs_instance)

    @patch.object(OfficeConverter, 'get_stats', return_value={"size": 80})
    def test_convert_powerpoint_ppt_odp_placeholder(self, mock_get_stats):
        """Test conversion of legacy .ppt and .odp returns placeholder."""
        for ext in [".ppt", ".odp"]:
            with self.subTest(extension=ext):
                test_path = Path(f"legacy{ext}")
                text, metadata = self.converter._convert_powerpoint_presentation(test_path)
                self.assertIn(f"format ({ext}) requires additional processing", text)
                self.assertIn(test_path.name, text)
                self.assertEqual(metadata, {"file_stats": {"size": 80}})
                mock_get_stats.assert_called_with(test_path)

    # --- Test overall exception handling in convert() ---
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch.object(OfficeConverter, '_convert_word_document', side_effect=RuntimeError("Internal Word Error"))
    def test_convert_catches_internal_runtime_error(self, mock_convert_word, mock_exists):
        """Test that the main convert method catches internal RuntimeErrors."""
        test_path = Path("runtime_error.docx")
        # The convert method should catch the RuntimeError and re-raise it
        # with a more generic message for the user.
        with self.assertRaisesRegex(RuntimeError, "Unexpected error processing Office file: Internal Word Error"):
            self.converter.convert(test_path)
        mock_exists.assert_called_once()
        mock_convert_word.assert_called_once_with(test_path)

    @patch('pathlib.Path.exists', return_value=True)
    @patch.object(OfficeConverter, '_convert_excel_spreadsheet', side_effect=ValueError("Bad Excel Value"))
    def test_convert_catches_internal_value_error(self, mock_convert_excel, mock_exists):
        """Test that the main convert method catches ValueErrors from internal methods."""
        test_path = Path("error.xlsx")
        with self.assertRaisesRegex(RuntimeError, "Failed to process Office file: Bad Excel Value"):
            self.converter.convert(test_path)
        mock_convert_excel.assert_called_once_with(test_path)


if __name__ == "__main__":
    unittest.main()
