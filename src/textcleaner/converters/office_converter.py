"""Converter for Microsoft Office and OpenDocument files."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Document processing libraries
import docx
import pandas as pd
from pptx import Presentation

from textcleaner.converters.base import BaseConverter
from textcleaner.config.config_manager import ConfigManager


class OfficeConverter(BaseConverter):
    """Converter for Microsoft Office and OpenDocument formats.
    
    Handles various office document formats including:
    - Word documents (.doc, .docx, .odt)
    - Excel spreadsheets (.xls, .xlsx, .ods)
    - PowerPoint presentations (.ppt, .pptx, .odp)
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the Office document converter.
        
        Args:
            config: Configuration manager instance.
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
        
        # Get Office-specific configuration
        self.extract_comments = self.config.get("formats.office.extract_comments", False)
        self.extract_tracked_changes = self.config.get("formats.office.extract_tracked_changes", False)
        self.extract_hidden_content = self.config.get("formats.office.extract_hidden_content", False)
        self.max_excel_rows = self.config.get("formats.office.max_excel_rows", 1000)
        self.max_excel_cols = self.config.get("formats.office.max_excel_cols", 20)
        
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
                raise ValueError(f"Unsupported office document format: {file_extension}")
                
        except Exception as e:
            raise RuntimeError(f"Error extracting text from office document: {str(e)}") from e
            
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
                return self._convert_docx(file_path)
            except Exception as e:
                raise RuntimeError(f"Error extracting text from DOCX: {str(e)}") from e
        else:
            # For .doc and .odt, use LibreOffice conversion if available
            # Otherwise, provide a placeholder and message
            return (
                f"# {file_path.name}\n\n"
                f"*This document format ({file_extension}) requires additional processing.*\n\n",
                {"file_stats": self.get_stats(file_path)}
            )
    
    def _convert_docx(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Convert a DOCX file to text.
        
        Args:
            file_path: Path to the DOCX file.
            
        Returns:
            Tuple of (extracted_text, metadata_dict).
        """
        doc = docx.Document(file_path)
        text_parts = []
        
        # Extract metadata
        metadata = {
            "file_stats": self.get_stats(file_path),
            "paragraph_count": len(doc.paragraphs),
            "section_count": len(doc.sections),
        }
        
        # Try to extract core properties
        try:
            core_props = doc.core_properties
            if core_props.title:
                metadata["title"] = core_props.title
            if core_props.author:
                metadata["author"] = core_props.author
            if core_props.last_modified_by:
                metadata["last_modified_by"] = core_props.last_modified_by
        except:
            pass
            
        # Process the document structure
        
        # Add title if available
        if "title" in metadata:
            text_parts.append(f"# {metadata['title']}\n")
        else:
            # Use filename as title if no title in metadata
            text_parts.append(f"# {file_path.stem}\n")
        
        # Process paragraphs
        in_list = False
        current_heading_level = 0
        
        for paragraph in doc.paragraphs:
            # Skip empty paragraphs
            if not paragraph.text.strip():
                # Add a newline to preserve paragraph breaks
                text_parts.append("")
                continue
                
            # Check for headings
            if paragraph.style.name.startswith('Heading'):
                heading_level = int(paragraph.style.name[-1])
                prefix = '#' * heading_level
                text_parts.append(f"\n{prefix} {paragraph.text}\n")
                current_heading_level = heading_level
                in_list = False
                continue
                
            # Check for list items
            if paragraph.style.name.startswith('List'):
                if not in_list:
                    text_parts.append("")
                    in_list = True
                text_parts.append(f"* {paragraph.text}")
                continue
            
            # Regular paragraph
            in_list = False
            text_parts.append(paragraph.text)
            
        # Extract tables
        table_count = 0
        for table in doc.tables:
            table_count += 1
            text_parts.append(f"\n### Table {table_count}\n")
            
            rows = []
            for i, row in enumerate(table.rows):
                if i == 0:
                    # Header row
                    header = " | ".join(cell.text for cell in row.cells)
                    rows.append(f"| {header} |")
                    # Add separator row
                    rows.append(f"| {' | '.join(['---'] * len(row.cells))} |")
                else:
                    # Data row
                    data = " | ".join(cell.text for cell in row.cells)
                    rows.append(f"| {data} |")
            
            text_parts.append("\n".join(rows))
            text_parts.append("\n")
            
        metadata["table_count"] = table_count
            
        return "\n".join(text_parts), metadata
        
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
                
            text_parts = [f"# {file_path.name}\n"]
            sheet_count = len(excel.sheet_names)
            
            metadata = {
                "file_stats": self.get_stats(file_path),
                "sheet_count": sheet_count,
                "sheets": {}
            }
            
            # Process each sheet
            for sheet_index, sheet_name in enumerate(excel.sheet_names):
                clean_name = re.sub(r'[^\w\s.-]', '_', sheet_name)
                
                # Add sheet as a section header
                if sheet_count > 1:
                    text_parts.append(f"## Sheet: {clean_name}\n")
                
                # Read the sheet data
                try:
                    df = pd.read_excel(excel, sheet_name=sheet_name)
                    
                    # Add sheet info to metadata
                    metadata["sheets"][clean_name] = {
                        "row_count": len(df),
                        "column_count": len(df.columns),
                    }
                    
                    # Apply row and column limits
                    if len(df) > self.max_excel_rows:
                        df = df.head(self.max_excel_rows)
                        text_parts.append(f"*Note: Table truncated to {self.max_excel_rows} rows*\n")
                        
                    if len(df.columns) > self.max_excel_cols:
                        df = df.iloc[:, :self.max_excel_cols]
                        text_parts.append(f"*Note: Table truncated to {self.max_excel_cols} columns*\n")
                    
                    # Handle empty dataframe
                    if df.empty:
                        text_parts.append("*Empty sheet*\n")
                        continue
                        
                    # Replace NaN with empty string
                    df = df.fillna("")
                    
                    # Convert column names to strings
                    df.columns = df.columns.astype(str)
                    
                    # Generate markdown table
                    header = "| " + " | ".join(str(col) for col in df.columns) + " |"
                    separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
                    
                    rows = []
                    for _, row in df.iterrows():
                        row_str = "| " + " | ".join(str(val).replace("\n", "<br>") for val in row.values) + " |"
                        rows.append(row_str)
                    
                    text_parts.append(header)
                    text_parts.append(separator)
                    text_parts.extend(rows)
                    text_parts.append("\n")
                    
                except Exception as sheet_error:
                    text_parts.append(f"*Error reading sheet {clean_name}: {str(sheet_error)}*\n")
                
                # Add separator between sheets
                if sheet_index < sheet_count - 1:
                    text_parts.append("---\n")
            
            return "\n".join(text_parts), metadata
            
        except Exception as e:
            raise RuntimeError(f"Error extracting text from Excel file: {str(e)}") from e
            
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
                return self._convert_pptx(file_path)
            except Exception as e:
                raise RuntimeError(f"Error extracting text from PPTX: {str(e)}") from e
        else:
            # For .ppt and .odp, use a placeholder
            return (
                f"# {file_path.name}\n\n"
                f"*This presentation format ({file_extension}) requires additional processing.*\n\n",
                {"file_stats": self.get_stats(file_path)}
            )
    
    def _convert_pptx(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Convert a PPTX file to text.
        
        Args:
            file_path: Path to the PPTX file.
            
        Returns:
            Tuple of (extracted_text, metadata_dict).
        """
        prs = Presentation(file_path)
        text_parts = [f"# {file_path.name}\n"]
        
        metadata = {
            "file_stats": self.get_stats(file_path),
            "slide_count": len(prs.slides),
        }
        
        # Process each slide
        for i, slide in enumerate(prs.slides):
            # Add slide number and title
            slide_num = i + 1
            text_parts.append(f"## Slide {slide_num}")
            
            # Add slide title if available
            if slide.shapes.title and slide.shapes.title.text:
                text_parts.append(f": {slide.shapes.title.text}\n")
            else:
                text_parts.append("\n")
            
            # Extract text from all shapes in the slide
            shape_texts = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    # Skip the title as we've already added it
                    if shape == slide.shapes.title:
                        continue
                    # Add shape text
                    shape_texts.append(shape.text)
            
            # Add bullet points for shape texts if there are multiple
            if len(shape_texts) > 1:
                for text in shape_texts:
                    text_parts.append(f"* {text}")
            elif shape_texts:
                text_parts.append(shape_texts[0])
            
            # Add a divider between slides
            text_parts.append("\n---\n")
        
        return "\n".join(text_parts), metadata
