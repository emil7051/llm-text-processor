"""Converter for Microsoft Office and OpenDocument files."""

# import os # Removed unused import
# import re # Removed unused import
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Document processing libraries
import docx
from docx.opc.exceptions import PackageNotFoundError
import pandas as pd
from pptx import Presentation
from pptx.exc import PackageNotFoundError as PptxPackageNotFoundError

from textcleaner.converters.base import BaseConverter
from textcleaner.config.config_manager import ConfigManager
from textcleaner.utils.logging_config import get_logger
from textcleaner.utils import office_processing as op_utils # Import the new utility module

logger = get_logger(__name__)


class OfficeConverter(BaseConverter):
    """Converter for Microsoft Office and OpenDocument formats.
    
    Handles various office document formats including:
    - Word documents (.doc, .docx, .odt)
    - Excel spreadsheets (.xls, .xlsx, .ods)
    - PowerPoint presentations (.ppt, .pptx, .odp)
    """
    
    def __init__(self, 
                 extract_comments: bool,
                 extract_tracked_changes: bool,
                 extract_hidden_content: bool,
                 max_excel_rows: int,
                 max_excel_cols: int,
                 config: Optional[ConfigManager] = None):
        """Initialize the Office document converter.
        
        Args:
            extract_comments: Whether to attempt extracting comments.
            extract_tracked_changes: Whether to attempt extracting tracked changes.
            extract_hidden_content: Whether to attempt extracting hidden content.
            max_excel_rows: Maximum rows to extract from Excel sheets.
            max_excel_cols: Maximum columns to extract from Excel sheets.
            config: Configuration manager instance (passed to BaseConverter).
        """
        super().__init__(config)
        self.supported_extensions = [
            # Microsoft Word
            ".doc", ".docx", 
            # Microsoft Excel
            ".xls", ".xlsx", 
            # Microsoft PowerPoint
            ".ppt", ".pptx",
            # OpenDocument formats
            ".odt", ".ods", ".odp"
        ]
        
        # Store specific configuration values
        self.extract_comments = extract_comments
        self.extract_tracked_changes = extract_tracked_changes
        self.extract_hidden_content = extract_hidden_content
        self.max_excel_rows = max_excel_rows
        self.max_excel_cols = max_excel_cols
        
    def convert(self, file_path: Union[str, Path]) -> Tuple[str, Dict[str, Any]]:
        """Convert an Office document to text and extract metadata.
        
        Routes to the appropriate converter based on file extension.
        
        Args:
            file_path: Path to the Office document.
            
        Returns:
            Tuple of (extracted_text, metadata_dict).
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file format is unsupported.
            RuntimeError: If extraction fails.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        if not file_path.exists():
            raise FileNotFoundError(f"Office document not found: {file_path}")
            
        file_extension = file_path.suffix.lower()
        
        try:
            # Route to the appropriate converter based on file extension
            if file_extension in [".docx", ".doc", ".odt"]:
                return self._convert_word_document(file_path)
            elif file_extension in [".xlsx", ".xls", ".ods"]:
                return self._convert_excel_spreadsheet(file_path)
            elif file_extension in [".pptx", ".ppt", ".odp"]:
                return self._convert_powerpoint_presentation(file_path)
            else:
                # This should be caught by can_handle, but added for robustness
                logger.error(f"Unsupported office document format encountered in convert: {file_extension}")
                raise ValueError(f"Unsupported office document format: {file_extension}")
                
        except (ValueError, PackageNotFoundError, PptxPackageNotFoundError, pd.errors.ParserError, IOError) as e:
            # Catch specific known errors from libraries or file issues
            logger.error(f"Failed to process Office file {file_path} ({type(e).__name__}): {e}")
            raise RuntimeError(f"Failed to process Office file: {str(e)}") from e
        except Exception as e:
            # Catch truly unexpected errors during routing/processing
            logger.exception(f"Unexpected error processing Office file {file_path}")
            raise RuntimeError(f"Unexpected error processing Office file: {str(e)}") from e
            
    def _convert_word_document(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Convert a Word document to text.
        
        Args:
            file_path: Path to the Word document.
            
        Returns:
            Tuple of (extracted_text, metadata_dict).
            
        Raises:
            RuntimeError: If extraction fails.
        """
        file_extension = file_path.suffix.lower()
        
        if file_extension == ".docx":
            try:
                doc = docx.Document(file_path)
                text, doc_metadata = op_utils.process_docx(file_path, doc)
                # Merge base stats with specific doc metadata
                metadata = {"file_stats": self.get_stats(file_path), **doc_metadata}
                return text, metadata
            except PackageNotFoundError as e:
                 logger.error(f"Could not find/read DOCX package {file_path}: {e}")
                 raise RuntimeError(f"Could not read DOCX file: {str(e)}") from e
            except Exception as e:
                 logger.exception(f"Unexpected error converting DOCX {file_path}")
                 raise RuntimeError(f"Unexpected error converting DOCX: {str(e)}") from e
        else:
            # For .doc and .odt, use LibreOffice conversion if available
            # Otherwise, provide a placeholder and message
            return (
                f"# {file_path.name}\n\n"
                f"*This document format ({file_extension}) requires additional processing.*\n\n",
                {"file_stats": self.get_stats(file_path)}
            )
    
    def _convert_excel_spreadsheet(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Convert an Excel spreadsheet to text.
        
        Args:
            file_path: Path to the Excel file.
            
        Returns:
            Tuple of (extracted_text, metadata_dict).
            
        Raises:
            RuntimeError: If extraction fails.
        """
        file_extension = file_path.suffix.lower()
        
        try:
            # Use the appropriate engine based on file extension
            if file_extension == ".xls":
                excel = pd.ExcelFile(file_path, engine='xlrd')
            else:  # .xlsx and .ods
                excel = pd.ExcelFile(file_path, engine='openpyxl')
                
            # Use the utility function for processing
            text, excel_metadata = op_utils.process_excel(
                file_path,
                excel,
                self.max_excel_rows,
                self.max_excel_cols
            )
            # Merge base stats with specific excel metadata
            metadata = {"file_stats": self.get_stats(file_path), **excel_metadata}
            return text, metadata
            
        except Exception as e:
            raise RuntimeError(f"Error extracting text from Excel file: {str(e)}") from e
        except pd.errors.ParserError as e:
            logger.error(f"Pandas parsing error reading Excel file {file_path}: {e}")
            raise RuntimeError(f"Failed to parse Excel file: {str(e)}") from e
        except (IOError, ValueError) as e: # Catch file access or engine errors
            logger.error(f"IO/Value error reading Excel file {file_path}: {e}")
            raise RuntimeError(f"Failed to read Excel file: {str(e)}") from e
        except Exception as e:
            logger.exception(f"Unexpected error extracting from Excel file {file_path}")
            raise RuntimeError(f"Unexpected error reading Excel file: {str(e)}") from e
            
    def _convert_powerpoint_presentation(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Convert a PowerPoint presentation to text.
        
        Args:
            file_path: Path to the PowerPoint file.
            
        Returns:
            Tuple of (extracted_text, metadata_dict).
            
        Raises:
            RuntimeError: If extraction fails.
        """
        file_extension = file_path.suffix.lower()
        
        if file_extension == ".pptx":
            try:
                prs = Presentation(file_path)
                text, pptx_metadata = op_utils.process_pptx(file_path, prs)
                # Merge base stats with specific pptx metadata
                metadata = {"file_stats": self.get_stats(file_path), **pptx_metadata}
                return text, metadata
            except PptxPackageNotFoundError as e:
                logger.error(f"Could not find/read PPTX package {file_path}: {e}")
                raise RuntimeError(f"Could not read PPTX file: {str(e)}") from e
            except Exception as e:
                logger.exception(f"Unexpected error converting PPTX {file_path}")
                raise RuntimeError(f"Unexpected error converting PPTX: {str(e)}") from e
        else:
            # For .ppt and .odp, use a placeholder
            return (
                f"# {file_path.name}\n\n"
                f"*This presentation format ({file_extension}) requires additional processing.*\n\n",
                {"file_stats": self.get_stats(file_path)}
            )
