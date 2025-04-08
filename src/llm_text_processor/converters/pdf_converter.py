"""Converter for PDF files."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PyPDF2 import PdfReader
import pdfminer
from pdfminer.high_level import extract_text as pdfminer_extract_text

from llm_text_processor.converters.base import BaseConverter
from llm_text_processor.config.config_manager import ConfigManager


class PDFConverter(BaseConverter):
    """Converter for PDF files.
    
    Extracts text and metadata from PDF files using a combination of
    PyPDF2 and pdfminer.six for better accuracy.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the PDF converter.
        
        Args:
            config: Configuration manager instance.
        """
        super().__init__(config)
        self.supported_extensions = [".pdf"]
        
        # Get PDF-specific configuration
        self.detect_columns = self.config.get("formats.pdf.detect_columns", True)
        self.handle_tables = self.config.get("formats.pdf.handle_tables", True)
        self.min_line_length = self.config.get("formats.pdf.min_line_length", 10)
        self.heading_sensitivity = self.config.get("formats.pdf.heading_detection_sensitivity", 0.7)
    
    def convert(self, file_path: Union[str, Path]) -> Tuple[str, Dict[str, Any]]:
        """Convert a PDF file to text and extract metadata.
        
        Combines multiple extraction methods for better results and
        attempts to preserve document structure.
        
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
            
            # First try with PyPDF2
            text_pypdf = self._extract_with_pypdf(file_path)
            
            # Then try with pdfminer
            text_pdfminer = self._extract_with_pdfminer(file_path)
            
            # Choose the better extraction result or combine them
            # For now, prefer pdfminer which generally gives better results
            # with formatting, but fall back to PyPDF2 if pdfminer fails or gives
            # much shorter results
            final_text = self._select_best_extraction(text_pypdf, text_pdfminer)
            
            # Post-process the text to clean it up and improve its structure
            final_text = self._post_process_text(final_text)
            
            return final_text, metadata
            
        except Exception as e:
            raise RuntimeError(f"Error extracting text from PDF: {str(e)}") from e
            
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
                if hasattr(doc_info, "title") and doc_info.title:
                    metadata["title"] = doc_info.title
                if hasattr(doc_info, "author") and doc_info.author:
                    metadata["author"] = doc_info.author
                if hasattr(doc_info, "subject") and doc_info.subject:
                    metadata["subject"] = doc_info.subject
                if hasattr(doc_info, "creator") and doc_info.creator:
                    metadata["creator"] = doc_info.creator
                
            return metadata
            
        except Exception as e:
            # Return basic metadata if extraction fails
            return {
                "file_stats": self.get_stats(file_path),
                "metadata_extraction_error": str(e)
            }
    
    def _extract_with_pypdf(self, file_path: Path) -> str:
        """Extract text using PyPDF2.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Extracted text.
        """
        try:
            reader = PdfReader(file_path)
            text_parts = []
            
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                
                # Add page number as a separator if it's a multi-page document
                if len(reader.pages) > 1:
                    text_parts.append(f"\n\n## Page {i+1}\n\n")
                    
                text_parts.append(page_text)
                
            return "\n\n".join(text_parts)
            
        except Exception as e:
            # Return empty string on error, the pdfminer method will be used instead
            return ""
    
    def _extract_with_pdfminer(self, file_path: Path) -> str:
        """Extract text using pdfminer.six.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Extracted text.
        """
        try:
            return pdfminer_extract_text(file_path)
        except Exception as e:
            # Return empty string on error, the PyPDF2 method will be used instead
            return ""
    
    def _select_best_extraction(self, text_pypdf: str, text_pdfminer: str) -> str:
        """Select the better extraction result or combine them.
        
        Args:
            text_pypdf: Text extracted with PyPDF2.
            text_pdfminer: Text extracted with pdfminer.
            
        Returns:
            The best text extraction result.
        """
        # If one extraction is empty, use the other
        if not text_pypdf.strip():
            return text_pdfminer
        if not text_pdfminer.strip():
            return text_pypdf
            
        # If pdfminer result is significantly shorter, it might have failed
        # to extract some content, so use PyPDF2 result instead
        if len(text_pdfminer) < len(text_pypdf) * 0.5:
            return text_pypdf
            
        # Otherwise, prefer pdfminer which generally gives better results with formatting
        return text_pdfminer
    
    def _post_process_text(self, text: str) -> str:
        """Clean up and improve the structure of the extracted text.
        
        Args:
            text: Raw extracted text.
            
        Returns:
            Processed text with improved structure.
        """
        if not text:
            return text
            
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Clean up whitespace
        text = re.sub(r' {2,}', ' ', text)
        
        # Attempt to detect and format bullet points
        text = re.sub(r'^\s*[•·⦿⦾⦿⁃⁌⁍◦▪▫◘◙◦➢➣➤●○◼◻►▻▷▹➔→⇒⟹⟾⟶⇝⇢⤷⟼⟿⤳⤻⤔⟴]+ *', '* ', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*[-–—] *', '* ', text, flags=re.MULTILINE)
        
        # Try to identify headings in the text for better structure
        lines = text.split('\n')
        for i in range(len(lines)):
            line = lines[i].strip()
            
            # Skip lines that are already formatted as headings
            if line.startswith('#'):
                continue
                
            # Potential heading: short line (not starting with * or - for lists)
            if line and len(line) < 60 and not line.startswith('*') and not line.startswith('-'):
                # Check if next line is empty or if previous line is empty (heading pattern)
                if (i+1 < len(lines) and not lines[i+1].strip()) or (i > 0 and not lines[i-1].strip()):
                    # Determine header level based on length
                    if len(line) < 20:
                        lines[i] = f"## {line}"
                    else:
                        lines[i] = f"### {line}"
        
        return '\n'.join(lines)
