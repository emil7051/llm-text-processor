"""Converter for handling Comma Separated Value (CSV) files."""

import csv
from pathlib import Path
from typing import Any, Dict, Tuple, Union, Optional

from textcleaner.config.config_manager import ConfigManager
from textcleaner.converters.base import BaseConverter
from textcleaner.utils.logging_config import get_logger

logger = get_logger(__name__)


class CSVConverter(BaseConverter):
    """Converter for CSV files."""

    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the CSV converter."""
        super().__init__(config=config)
        self.supported_extensions = ['.csv']
        # Load configuration options
        self.delimiter = self.config.get("formats.csv.delimiter", ",")
        self.quotechar = self.config.get("formats.csv.quotechar", '"')
        self.include_header = self.config.get("formats.csv.include_header", True)
        self.max_rows = self.config.get("formats.csv.max_rows", None)

    def convert(self, file_path: Union[str, Path]) -> Tuple[str, Dict[str, Any]]:
        """Convert a CSV file to raw text content and extract metadata."""
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self.can_handle(file_path):
            logger.error(f"Unsupported file type: {file_path}")
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        logger.info(f"Converting CSV file: {file_path}")
        content_lines = []
        metadata = self.get_stats(file_path)
        metadata['converter'] = self.__class__.__name__

        try:
            with open(file_path, 'r', newline='', encoding='utf-8-sig') as csvfile: # Use utf-8-sig to handle potential BOM
                # Use configured delimiter and quotechar
                reader = csv.reader(csvfile, delimiter=self.delimiter, quotechar=self.quotechar)
                header = None
                original_rows = 0
                for i, row in enumerate(reader):
                    original_rows += 1
                    if self.max_rows is not None and i >= self.max_rows:
                        logger.warning(f"Reached max_rows limit ({self.max_rows}) for {file_path}. Truncating file.")
                        metadata['truncated'] = True
                        break
                    
                    if i == 0 and not self.include_header:
                        header = row
                        metadata['header'] = header
                        continue
                    
                    # Handle potential empty cells or different data types gracefully
                    processed_row = []
                    for cell in row:
                        try:
                            processed_row.append(str(cell).strip())
                        except Exception as cell_err:
                            logger.warning(f"Could not process cell in row {i+1} of {file_path}: {cell_err}. Replacing with empty string.")
                            processed_row.append("") # Replace problematic cell with empty string
                    
                    content_lines.append(" ".join(processed_row))

            raw_content = "\n".join(content_lines)
            logger.debug(f"Successfully converted {file_path}. Extracted {len(raw_content)} characters from {len(content_lines)} rows (original: {original_rows}).")
            metadata['original_rows'] = original_rows
            metadata['processed_rows'] = len(content_lines)
            metadata['delimiter'] = self.delimiter
            metadata['quotechar'] = self.quotechar
            metadata['included_header'] = self.include_header if header is None else False

        except csv.Error as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
            raise RuntimeError(f"Failed to parse CSV file {file_path}: {e}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during CSV conversion of {file_path}: {e}")
            raise RuntimeError(f"Conversion failed for {file_path}") from e

        return raw_content, metadata 