"""
Streaming utilities for processing large files efficiently
"""

# import io # Unused
# import os # Unused
from typing import Generator, BinaryIO, Optional, Callable, Any, Dict, Union, TextIO
from pathlib import Path
import tempfile

from textcleaner.utils.logging_config import get_logger
from textcleaner.utils.performance import performance_monitor


class StreamProcessor:
    """Utility for processing large files in a memory-efficient way using streaming."""
    
    def __init__(self, chunk_size: int = 1024 * 1024):  # Default 1MB chunks
        """Initialize the stream processor.
        
        Args:
            chunk_size: Size of chunks to process at once, in bytes
        """
        self.logger = get_logger(__name__)
        self.chunk_size = chunk_size
    
    def stream_file(self, file_path: Union[str, Path]) -> Generator[bytes, None, None]:
        """Stream a file in chunks to reduce memory usage.
        
        Args:
            file_path: Path to the file to stream
            
        Yields:
            Chunks of bytes from the file
        """
        file_path = Path(file_path)
        self.logger.debug(f"Streaming file {file_path} in {self.chunk_size} byte chunks")
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                yield chunk
    
    def stream_process_text(
        self, 
        file_path: Union[str, Path],
        process_func: Callable[[str], str],
        encoding: str = 'utf-8'
    ) -> Generator[str, None, None]:
        """Stream and process a text file.
        
        Args:
            file_path: Path to the file to process
            process_func: Function to apply to each text chunk
            encoding: File encoding
            
        Yields:
            Processed text chunks
        """
        for binary_chunk in self.stream_file(file_path):
            try:
                text_chunk = binary_chunk.decode(encoding)
                processed_chunk = process_func(text_chunk)
                yield processed_chunk
            except UnicodeDecodeError as e:
                self.logger.error(f"Unicode decode error: {e}")
                # Yield an error marker that can be filtered out later
                yield f"<!-- ERROR: Unicode decode error at position {e.start} -->"
    
    def stream_to_file(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        process_func: Callable[[bytes], bytes] = None,
        buffer_size: int = 1024 * 1024  # 1MB
    ) -> bool:
        """Stream process a file and write to output.
        
        Args:
            input_path: Source file path
            output_path: Destination file path
            process_func: Optional function to transform bytes
            buffer_size: Write buffer size
            
        Returns:
            True if successful, False otherwise
        """
        with performance_monitor.performance_context("stream_to_file"):
            try:
                input_path = Path(input_path)
                output_path = Path(output_path)
                
                # Ensure output directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Process the file
                with open(output_path, 'wb', buffering=buffer_size) as out_file:
                    for chunk in self.stream_file(input_path):
                        if process_func:
                            chunk = process_func(chunk)
                        out_file.write(chunk)
                
                self.logger.info(f"Successfully streamed and processed {input_path} to {output_path}")
                return True
            except Exception as e:
                self.logger.error(f"Error during streaming process: {e}")
                return False
    
    def process_large_text_file(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        process_func: Callable[[str], str],
        encoding: str = 'utf-8',
        output_encoding: str = None
    ) -> bool:
        """Process a large text file with line-by-line processing.
        
        Args:
            input_path: Source file path
            output_path: Destination file path
            process_func: Function to process each line or chunk
            encoding: Input file encoding
            output_encoding: Output file encoding (defaults to input encoding)
            
        Returns:
            True if successful, False otherwise
        """
        if output_encoding is None:
            output_encoding = encoding
            
        try:
            input_path = Path(input_path)
            output_path = Path(output_path)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with performance_monitor.performance_context("process_large_text_file"):
                with open(input_path, 'r', encoding=encoding) as in_file, \
                     open(output_path, 'w', encoding=output_encoding) as out_file:
                    
                    # Process line by line to minimize memory usage
                    for line in in_file:
                        processed_line = process_func(line)
                        out_file.write(processed_line)
            
            self.logger.info(f"Successfully processed large text file {input_path} to {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error during large text file processing: {e}")
            return False
    
    def create_temp_stream_writer(self) -> tuple[Path, BinaryIO]:
        """Create a temporary file for streaming output.
        
        Returns:
            Tuple of (file path, file object)
        """
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        return Path(temp_file.name), temp_file


# Removed unused singleton instance
# stream_processor = StreamProcessor()
