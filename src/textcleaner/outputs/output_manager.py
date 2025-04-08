"""Output management for processed text."""

import json
import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from textcleaner.config.config_manager import ConfigManager


class BaseOutputWriter(ABC):
    """Base class for all output format writers."""
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the output writer.
        
        Args:
            config: Configuration manager instance.
        """
        self.config = config or ConfigManager()
        
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
        # Check if we should include metadata
        include_metadata = self.config.get("output.include_metadata", True)
        
        final_content = content
        
        # Add metadata section if requested and available
        if include_metadata and metadata:
            metadata_section = "## Document Metadata\n\n"
            
            # Add basic metadata
            if "title" in metadata:
                metadata_section += f"- Title: {metadata['title']}\n"
            if "author" in metadata:
                metadata_section += f"- Author: {metadata['author']}\n"
            
            # Add file stats
            if "file_stats" in metadata:
                stats = metadata["file_stats"]
                if "file_size_kb" in stats:
                    metadata_section += f"- File Size: {stats['file_size_kb']} KB\n"
                    
            # Add document-specific metadata
            if "page_count" in metadata:
                metadata_section += f"- Pages: {metadata['page_count']}\n"
            elif "slide_count" in metadata:
                metadata_section += f"- Slides: {metadata['slide_count']}\n"
            elif "sheet_count" in metadata:
                metadata_section += f"- Sheets: {metadata['sheet_count']}\n"
                
            # Add conversion stats if available
            if "conversion_stats" in metadata:
                stats = metadata["conversion_stats"]
                if "token_reduction_percent" in stats:
                    metadata_section += f"- Token Reduction: {stats['token_reduction_percent']}%\n"
            
            # Append metadata to content or prepend based on config
            if self.config.get("output.metadata_position", "end") == "end":
                final_content = content + "\n\n" + metadata_section
            else:
                final_content = metadata_section + "\n\n" + content
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)


class PlainTextWriter(BaseOutputWriter):
    """Writer for plain text output format."""
    
    def write(
        self, 
        content: str, 
        output_path: Path, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Write content as plain text.
        
        Args:
            content: The content to write.
            output_path: Path to the output file.
            metadata: Optional metadata to include.
            
        Raises:
            IOError: If the file cannot be written.
        """
        # For plain text, we need to convert markdown to plain text
        plain_content = self._markdown_to_plain(content)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(plain_content)
    
    def _markdown_to_plain(self, markdown: str) -> str:
        """Convert markdown to plain text.
        
        Args:
            markdown: Markdown content.
            
        Returns:
            Plain text version.
        """
        import re
        
        # Replace headings
        plain = re.sub(r'^#{1,6}\s+(.+)$', r'\1\n', markdown, flags=re.MULTILINE)
        
        # Replace bullet points
        plain = re.sub(r'^\s*[*-]\s+(.+)$', r'  - \1', plain, flags=re.MULTILINE)
        
        # Replace tables with a simpler representation
        table_pattern = r'\|(.+)\|\n\|[-|]+\|\n((?:\|.+\|\n)+)'
        
        def table_to_plain(match):
            header = match.group(1).strip()
            rows = match.group(2).strip()
            
            header_cols = [col.strip() for col in header.split('|')]
            result = f"{' | '.join(header_cols)}\n"
            result += "-" * len(result) + "\n"
            
            for row in rows.split('\n'):
                if '|' in row:
                    cols = [col.strip() for col in row.split('|')[1:-1]]
                    result += f"{' | '.join(cols)}\n"
            
            return result
        
        plain = re.sub(table_pattern, table_to_plain, plain)
        
        # Remove other markdown syntax
        plain = re.sub(r'\*\*(.+?)\*\*', r'\1', plain)  # Bold
        plain = re.sub(r'\*(.+?)\*', r'\1', plain)      # Italic
        plain = re.sub(r'`(.+?)`', r'\1', plain)        # Code
        plain = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', plain)  # Links
        
        return plain


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
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class CsvWriter(BaseOutputWriter):
    """Writer for CSV output format.
    
    This is primarily useful for tabular data.
    """
    
    def write(
        self, 
        content: str, 
        output_path: Path, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Write content as CSV.
        
        Args:
            content: The content to write, should be tabular data.
            output_path: Path to the output file.
            metadata: Optional metadata to include.
            
        Raises:
            IOError: If the file cannot be written.
            ValueError: If the content is not in a supported format.
        """
        # Extract tables from markdown
        tables = self._extract_tables(content)
        
        if not tables:
            # No tables found, write content as a single column
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Content"])
                
                # Split by lines and write each non-empty line
                for line in content.split('\n'):
                    if line.strip():
                        writer.writerow([line])
        else:
            # Write the first table found
            table = tables[0]
            
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # Write rows
                for row in table:
                    writer.writerow(row)
    
    def _extract_tables(self, markdown: str) -> List[List[List[str]]]:
        """Extract tables from markdown content.
        
        Args:
            markdown: Markdown content.
            
        Returns:
            List of tables, where each table is a list of rows,
            and each row is a list of cell values.
        """
        import re
        
        tables = []
        
        # Find tables in markdown
        table_pattern = r'\|(.+)\|\n\|[-|]+\|\n((?:\|.+\|\n)+)'
        matches = re.finditer(table_pattern, markdown)
        
        for match in matches:
            header = match.group(1).strip()
            rows_text = match.group(2).strip()
            
            # Parse header
            header_cells = [cell.strip() for cell in header.split('|')]
            
            # Parse rows
            rows = []
            for row_text in rows_text.split('\n'):
                if '|' in row_text:
                    cells = [cell.strip() for cell in row_text.split('|')[1:-1]]
                    rows.append(cells)
            
            # Combine header and rows
            table = [header_cells] + rows
            tables.append(table)
        
        return tables


class OutputManager:
    """Manager for output writers.
    
    Handles writing processed text to different output formats.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the output manager.
        
        Args:
            config: Configuration manager instance.
        """
        self.config = config or ConfigManager()
        self.writers = {
            "markdown": MarkdownWriter(config),
            "plain_text": PlainTextWriter(config),
            "json": JsonWriter(config),
            "csv": CsvWriter(config),
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
            
        # Infer format from file extension if not provided
        if format is None:
            ext = output_path.suffix.lower()[1:]  # Remove leading dot
            
            # Map extension to format
            ext_to_format = {
                "md": "markdown",
                "txt": "plain_text",
                "json": "json",
                "csv": "csv",
            }
            
            format = ext_to_format.get(ext, self.config.get("output.default_format", "markdown"))
        
        # Check if format is supported
        if format not in self.writers:
            raise ValueError(f"Unsupported output format: {format}")
            
        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content using the appropriate writer
        self.writers[format].write(content, output_path, metadata)
