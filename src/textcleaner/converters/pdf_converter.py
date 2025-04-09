"""Converter for PDF files."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pypdf import PdfReader
from pypdf.errors import PdfReadError
from pdfminer.high_level import extract_text as pdfminer_extract_text
from pdfminer.pdfparser import PDFSyntaxError
from pdfminer.pdfdocument import PDFEncryptionError

from textcleaner.converters.base import BaseConverter
from textcleaner.config.config_manager import ConfigManager
from textcleaner.utils.logging_config import get_logger

logger = get_logger(__name__)

class PDFConverter(BaseConverter):
    """Converter for PDF files.
    
    Extracts text and metadata from PDF files using a combination of
    PyPDF2 (for metadata) and pdfminer.six (for text extraction).
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the PDF converter.
        
        Args:
            config: Configuration manager instance (currently unused).
        """
        # Call super().__init__ but note config is not actively used here
        # after prior refactoring moved post-processing logic.
        super().__init__(config) 
        self.supported_extensions = [".pdf"]
        
        # Configuration values previously used here are no longer needed
        # as post-processing happens in the pipeline.
    
    def convert(self, file_path: Union[str, Path]) -> Tuple[str, Dict[str, Any]]:
        """Convert a PDF file to text and extract metadata.
        
        Uses pdfminer.six for text extraction and PyPDF2 for metadata.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Tuple of (extracted_text, metadata_dict).
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
            RuntimeError: If extraction fails.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
            
        try:
            # Extract metadata using PyPDF2
            metadata = self._extract_metadata(file_path)
            
            # Extract text using pdfminer.six
            final_text = self._extract_with_pdfminer(file_path)
            
            # Raise an error if extraction returned an empty string
            if not final_text:
                # Log the failure before raising
                logger.error(f"PDF text extraction yielded empty result for: {file_path}")
                raise RuntimeError(f"Conversion resulted in empty content for {file_path}")

            return final_text, metadata
            
        except (FileNotFoundError, RuntimeError) as e:
             # Re-raise errors we expect the caller to handle
             raise e
        except Exception as e:
            # Catch any other unexpected exception during the overall conversion process
            logger.exception(f"Unexpected error during PDF conversion for {file_path}")
            raise RuntimeError(f"Unexpected error converting PDF {file_path}: {str(e)}") from e
    
    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from the PDF.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Dictionary containing metadata.
        """
        try:
            reader = PdfReader(file_path)
            metadata = {
                "page_count": len(reader.pages),
                "file_stats": self.get_stats(file_path),
            }
            
            # Get document info (title, author, etc.)
            doc_info = reader.metadata
            if doc_info:
                # Check attributes defensively
                metadata["title"] = getattr(doc_info, 'title', None)
                metadata["author"] = getattr(doc_info, 'author', None)
                metadata["subject"] = getattr(doc_info, 'subject', None)
                metadata["creator"] = getattr(doc_info, 'creator', None)
                # Remove None values
                metadata = {k: v for k, v in metadata.items() if v is not None}
                
            return metadata
            
        except (PdfReadError, IOError) as e:
            # Specific, potentially recoverable errors related to reading the PDF
            logger.warning(f"Could not read PDF metadata for {file_path} ({type(e).__name__}): {e}")
            return {
                "file_stats": self.get_stats(file_path),
                "metadata_extraction_error": f"PDF read error: {type(e).__name__}"
            }
        except Exception as e:
            # Unexpected errors during metadata extraction
            logger.exception(f"Unexpected error extracting PDF metadata for {file_path}")
            # Re-raise the exception to be caught by the main convert method's handler
            raise e
    
    def _extract_with_pdfminer(self, file_path: Path) -> str:
        """Extract text using pdfminer.six.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Extracted text, or empty string on failure.
        """
        try:
            return pdfminer_extract_text(file_path)
        except (PDFSyntaxError, PDFEncryptionError, OSError) as e:
            # Specific, potentially recoverable errors from pdfminer
            logger.error(f"pdfminer extraction failed for {file_path} ({type(e).__name__}): {e}")
            return "" # Return empty string on known extraction failures
        except ValueError as e:
            # Catch specific Ascii85 decoding error seen in tests
            if "Ascii85" in str(e):
                logger.error(f"pdfminer extraction failed for {file_path} due to Ascii85 decoding issue: {e}")
                return "" # Treat as known failure
            else:
                # Re-raise other ValueErrors
                logger.exception(f"Unexpected ValueError during pdfminer extraction for {file_path}")
                raise # Re-raise unexpected ValueError
        except Exception as e:
            # Unexpected errors during pdfminer processing
            logger.exception(f"Unexpected error during pdfminer extraction for {file_path}")
            return "" # Return empty string on unexpected failures too
    
    # Removed _post_process_text method as it's handled by pipeline
