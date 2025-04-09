"""Output management for processed text."""

import json
import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
# Import markdown-it-py
try:
    from markdown_it import MarkdownIt
    from markdown_it.token import Token # For table parsing
    _markdown_it_available = True
except ImportError:
    _markdown_it_available = False

from textcleaner.config.config_manager import ConfigManager
from textcleaner.utils.logging_config import get_logger # Import logger


# Get logger for warnings
logger = get_logger(__name__)

class BaseOutputWriter(ABC):
    """Base class for all output format writers."""
    
    @abstractmethod
    def write(
        self, 
        content: str, 
        output_path: Path, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Write content to the output file.
        
        Args:
            content: The content to write.
            output_path: Path to the output file.
            metadata: Optional metadata to include.
            
        Raises:
            IOError: If the file cannot be written.
        """
        pass


class MarkdownWriter(BaseOutputWriter):
    """Writer for Markdown output format."""
    
    def __init__(self, include_metadata: bool, metadata_position: str):
        """Initialize the Markdown writer.
        
        Args:
            include_metadata: Whether to include metadata in the output.
            metadata_position: Position of metadata ('start' or 'end').
        """
        self.include_metadata = include_metadata
        self.metadata_position = metadata_position
        
    def write(
        self, 
        content: str, 
        output_path: Path, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Write content as Markdown.
        
        Args:
            content: The content to write.
            output_path: Path to the output file.
            metadata: Optional metadata to include.
            
        Raises:
            IOError: If the file cannot be written.
        """
        # Use stored configuration values
        include_metadata = self.include_metadata
        
        # Initialize metadata section content
        metadata_content = ""
        
        # Add metadata section if requested and available
        if include_metadata and metadata:
            metadata_items = [] # Use a list to build the section
            
            # Add basic metadata
            if "title" in metadata:
                metadata_items.append(f"- Title: {metadata['title']}")
            if "author" in metadata:
                metadata_items.append(f"- Author: {metadata['author']}")
            
            # Add file stats
            if "file_stats" in metadata:
                stats = metadata["file_stats"]
                if "file_size_kb" in stats:
                    metadata_items.append(f"- File Size: {stats['file_size_kb']:.2f} KB") # Format KB
                    
            # Add document-specific metadata
            if "page_count" in metadata:
                metadata_items.append(f"- Pages: {metadata['page_count']}")
            elif "slide_count" in metadata:
                metadata_items.append(f"- Slides: {metadata['slide_count']}")
            elif "sheet_count" in metadata:
                metadata_items.append(f"- Sheets: {metadata['sheet_count']}")
                
            # Add conversion stats if available (use metrics if nested)
            metrics = metadata.get("metrics", {}) # Check if metrics are nested
            if "token_reduction_percent" in metrics:
                 metadata_items.append(f"- Token Reduction: {metrics['token_reduction_percent']:.2f}%") # Format %

            # Construct the metadata section only if items were added
            if metadata_items:
                metadata_content = "## Document Metadata\\n\\n" + "\\n".join(metadata_items)

        # Combine content and metadata based on config
        if metadata_content:
            if self.metadata_position == "end":
                final_content = content + "\\n\\n" + metadata_content
            else: # Default to 'start' or if position is invalid
                final_content = metadata_content + "\\n\\n" + content
        else:
            # If no metadata, just use the original content
            final_content = content

        # Write to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
        except IOError as e:
            logger.error(f"Failed to write Markdown file {output_path}: {e}")
            raise # Re-raise the exception


class PlainTextWriter(BaseOutputWriter):
    """Writer for plain text output format."""
    
    def __init__(self):
        """Initialize the PlainTextWriter."""
        self.parser = None
        if _markdown_it_available:
            # Configure markdown-it for plain text output
            # We disable all rules that produce HTML-like tags
            self.parser = MarkdownIt(
                options_update={
                    'html': False, # Disable raw HTML
                    'linkify': False, # Disable autolinks
                }
            ).disable([
                'image', 'table', 'heading', 'hr', 'list', 
                'blockquote', 'code', 'fence', 'html_block', 
                'html_inline', 'lheading', 'reference', 'link'
            ])
        else:
            logger.warning("markdown-it-py not found. Plain text output might be suboptimal using regex.")

    def write(
        self, 
        content: str, 
        output_path: Path, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Write content as plain text.
        
        Args:
            content: The content to write (assumed to be Markdown).
            output_path: Path to the output file.
            metadata: Optional metadata (currently ignored by this writer).
            
        Raises:
            IOError: If the file cannot be written.
        """
        # For plain text, convert markdown to plain text
        if self.parser:
            plain_content = self.parser.render(content).strip()
        else:
            # Fallback to basic regex if library not available
            plain_content = self._markdown_to_plain_fallback(content)
        
        # Write to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(plain_content)
        except IOError as e:
            logger.error(f"Failed to write plain text file {output_path}: {e}")
            raise # Re-raise the exception
    
    def _markdown_to_plain_fallback(self, markdown: str) -> str:
        """Basic regex-based fallback to convert markdown to plain text."""
        import re
        
        logger.debug("Using regex fallback for plain text conversion.")
        # Replace headings
        plain = re.sub(r'^#{1,6}\\s+(.+)$\\n?', r'\\1\\n', markdown, flags=re.MULTILINE)
        # Replace lists (simple approach)
        plain = re.sub(r'^\\s*[*-+]\\s+', '', plain, flags=re.MULTILINE)
        # Remove bold/italic markers
        plain = re.sub(r'(\\*\\*|\\*|_)', '', plain)
        # Remove links but keep text
        plain = re.sub(r'\\[(.+?)\\]\\(.+?\\)', r'\\1', plain)
        # Remove code backticks
        plain = re.sub(r'`', '', plain)
        # Remove horizontal rules
        plain = re.sub(r'^[-*_]{3,}\\s*$', '', plain, flags=re.MULTILINE)
        # Basic table removal (crude)
        plain = re.sub(r'\\|.*\\|', '', plain) 
        # Clean up extra newlines
        plain = re.sub(r'\\n{3,}', '\\n\\n', plain)
        
        return plain.strip()


class JsonWriter(BaseOutputWriter):
    """Writer for JSON output format."""
    
    def write(
        self, 
        content: str, 
        output_path: Path, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Write content as JSON.
        
        Args:
            content: The content to write.
            output_path: Path to the output file.
            metadata: Optional metadata to include.
            
        Raises:
            IOError: If the file cannot be written.
        """
        # Create JSON structure
        data = {
            "content": content
        }
        
        # Include metadata if available
        if metadata:
            data["metadata"] = metadata
        
        # Write to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Failed to write JSON file {output_path}: {e}")
            raise # Re-raise the exception
        except TypeError as e: # Catch potential JSON serialization errors
            logger.error(f"Failed to serialize data to JSON for {output_path}: {e}")
            raise RuntimeError(f"JSON serialization error: {e}") from e


class CsvWriter(BaseOutputWriter):
    """Writer for CSV output format.
    
    Extracts the first table found in the Markdown content and writes it as CSV.
    If no table is found, writes the content line-by-line into a single column.
    """
    def __init__(self):
        """Initialize the CsvWriter."""
        self.parser = None
        if _markdown_it_available:
            # Basic parser is enough, we will traverse tokens
            self.parser = MarkdownIt() 
        else:
            logger.warning("markdown-it-py not found. CSV output from tables might be suboptimal using regex.")

    def write(
        self, 
        content: str, 
        output_path: Path, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Write content as CSV.
        
        Args:
            content: The content to write, assumed to be Markdown.
            output_path: Path to the output file.
            metadata: Optional metadata (currently ignored by this writer).
            
        Raises:
            IOError: If the file cannot be written.
            ValueError: If the content is not in a supported format (currently unused).
        """
        tables = []
        if self.parser:
            try:
                tables = self._extract_tables_mdit(content)
            except Exception as e:
                 logger.error(f"Error parsing tables with markdown-it for CSV output: {e}")
                 # Fallback or continue without tables
                 tables = [] # Ensure tables is empty on error
        else:
             # Fallback to regex if library not available
             tables = self._extract_tables_fallback(content)
        
        try:
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                if not tables:
                    # No tables found, write content as a single column
                    logger.debug(f"No tables found in content for {output_path}. Writing as single column CSV.")
                    writer.writerow(["Content"]) # Header for the single column
                    # Split by lines and write each non-empty line
                    for line in content.split('\\n'):
                        stripped_line = line.strip()
                        if stripped_line: # Write only non-empty lines
                            writer.writerow([stripped_line])
                else:
                    # Write the first table found
                    table = tables[0]
                    logger.debug(f"Writing first extracted table ({len(table)} rows) to {output_path}.")
                    # Write all rows from the first table
                    writer.writerows(table)
        except IOError as e:
             logger.error(f"Failed to write CSV file {output_path}: {e}")
             raise # Re-raise the exception
        except csv.Error as e:
             logger.error(f"CSV writing error for {output_path}: {e}")
             raise RuntimeError(f"CSV writing error: {e}") from e

    def _extract_tables_mdit(self, markdown: str) -> List[List[List[str]]]:
        """Extract tables using markdown-it-py token traversal."""
        if not self.parser:
            return []

        tokens = self.parser.parse(markdown)
        tables = []
        current_table: Optional[List[List[str]]] = None
        current_row: Optional[List[str]] = None
        in_header = False

        i = 0
        while i < len(tokens):
            token = tokens[i]
            # logger.debug(f"Token: {token.type} | Level: {token.level} | Tag: {token.tag} | Content: '{token.content}'")

            if token.type == 'table_open':
                current_table = []
            elif token.type == 'thead_open':
                in_header = True
            elif token.type == 'tbody_open':
                 in_header = False # Ensure we know we are out of header
            elif token.type == 'tr_open':
                 if current_table is not None:
                     current_row = []
            elif token.type in ['th_open', 'td_open']:
                # Cell content is in the next 'inline' token
                i += 1
                if i < len(tokens) and tokens[i].type == 'inline':
                    cell_content = tokens[i].content.strip()
                    if current_row is not None:
                         current_row.append(cell_content)
                # Skip the closing th/td token
                i += 1 
                continue # Continue loop after processing cell content + closing tag
            elif token.type == 'tr_close':
                 if current_table is not None and current_row is not None:
                     current_table.append(current_row)
                 current_row = None
            elif token.type == 'thead_close':
                 in_header = False
            elif token.type == 'table_close':
                 if current_table is not None:
                     tables.append(current_table)
                 current_table = None

            i += 1 # Move to the next token

        return tables

    def _extract_tables_fallback(self, markdown: str) -> List[List[List[str]]]:
        """Extract tables from markdown content using regex (Fallback)."""
        import re
        logger.debug("Using regex fallback for table extraction.")
        
        extracted_tables = []
        # Find tables in markdown (improved regex to handle pipes in content better, but still limited)
        # This regex assumes simple tables and might fail on complex ones
        table_pattern = r'^\\|(.+)\\|\\n\\|[-|\\s]+?\\|\\n((?:^\\|.+\\|\\n?)+)'
        matches = re.finditer(table_pattern, markdown, flags=re.MULTILINE)
        
        for match in matches:
            header_line = match.group(1).strip()
            rows_block = match.group(2).strip()
            
            # Parse header cells (split by '|', strip whitespace)
            header_cells = [cell.strip() for cell in header_line.split('|')]
            
            # Parse rows
            current_table_rows = []
            for row_line in rows_block.split('\\n'):
                if row_line.strip():
                    # Split by '|', strip whitespace, ignore first/last empty strings if they exist
                    row_cells = [cell.strip() for cell in row_line.split('|')[1:-1]] 
                    current_table_rows.append(row_cells)
            
            # Combine header and rows if rows were found
            if current_table_rows:
                 # Ensure header and row cell counts match roughly (simple check)
                 if len(header_cells) == len(current_table_rows[0]):
                     table_data = [header_cells] + current_table_rows
                     extracted_tables.append(table_data)
                 else:
                     logger.warning("Skipping table due to mismatched header/row columns (regex fallback).")
        
        return extracted_tables


class OutputManager:
    """Manager for output writers.
    
    Handles writing processed text to different output formats.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the output manager.
        
        Args:
            config: Configuration manager instance.
        """
        self.config = config or ConfigManager() # Keep config for default format lookup
        self.writers: Dict[str, BaseOutputWriter] = {
            # Pass config values correctly during instantiation
            "markdown": MarkdownWriter(
                include_metadata=self.config.get("output.markdown.include_metadata", True),
                metadata_position=self.config.get("output.markdown.metadata_position", "end")
            ),
            "plain_text": PlainTextWriter(), # Instantiated correctly
            "json": JsonWriter(),           # Instantiated correctly
            "csv": CsvWriter(),             # Instantiated correctly
        }
        
    def write(
        self, 
        content: str, 
        output_path: Union[str, Path], 
        format: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Write content to the output file in the specified format.
        
        Args:
            content: The content to write.
            output_path: Path to the output file.
            format: Output format. If None, it will be inferred from
                the file extension or the default from config will be used.
            metadata: Optional metadata to include.
            
        Raises:
            IOError: If the file cannot be written.
            ValueError: If the format is not supported.
        """
        if isinstance(output_path, str):
            output_path = Path(output_path)

        # Normalize format aliases first
        format_aliases = {
            "text": "plain_text",
            "txt": "plain_text",
            "md": "markdown",
        }
        if format:
            format = format_aliases.get(format.lower(), format.lower())


        # Infer format from file extension if not provided or normalized
        if format is None:
            ext = output_path.suffix.lower()[1:]  # Remove leading dot

            # Map extension to format (using normalized keys)
            ext_to_format = {
                "md": "markdown",
                "txt": "plain_text",
                "text": "plain_text", # Keep for extension mapping
                "json": "json",
                "csv": "csv",
            }

            # Use config only here to get the default format if needed
            default_format = self.config.get("output.default_format", "markdown")
            format = ext_to_format.get(ext, default_format)

        # Check if format is supported using the potentially normalized format key
        if format not in self.writers:
            raise ValueError(f"Unsupported output format: {format}")
            
        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content using the appropriate writer
        # Pass metadata to the writer
        writer = self.writers[format]
        logger.debug(f"Using writer '{writer.__class__.__name__}' for format '{format}'")
        writer.write(content, output_path, metadata) # Pass metadata here
