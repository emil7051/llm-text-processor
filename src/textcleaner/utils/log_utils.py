"""Logging utilities for the LLM Text Processor."""

import time
from typing import Any, Dict, Optional

from textcleaner.utils.logging_config import get_logger


class ProcessingLogger:
    """Enhanced logging for text processing operations."""
    
    def __init__(self, module_name: str):
        """Initialize the processing logger.
        
        Args:
            module_name: Name of the module using this logger
        """
        self.logger = get_logger(module_name)
    
    def log_processing_start(self, file_name: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Log the start of a file processing operation.
        
        Args:
            file_name: Name of the file being processed
            params: Optional parameters to log
        """
        self.logger.info(f"Starting processing of file: {file_name}")
        if params:
            param_str = ", ".join(f"{k}={v}" for k, v in params.items())
            self.logger.debug(f"Processing parameters: {param_str}")
    
    def log_extraction_results(self, file_name: str, text_length: int, metadata: Dict[str, Any]) -> None:
        """Log the results of content extraction.
        
        Args:
            file_name: Name of the file that was processed
            text_length: Length of the extracted text in characters
            metadata: Metadata extracted from the file
        """
        self.logger.info(f"Extracted {text_length} characters from {file_name}")
        if metadata:
            self.logger.debug(f"Extracted metadata fields: {', '.join(metadata.keys())}")
    
    def log_processing_results(self, 
                             original_length: int, 
                             processed_length: int, 
                             metrics: Dict[str, Any]) -> None:
        """Log the results of text processing.
        
        Args:
            original_length: Length of the original text in characters
            processed_length: Length of the processed text in characters
            metrics: Processing metrics
        """
        char_reduction = original_length - processed_length
        if original_length > 0:
            reduction_pct = (char_reduction / original_length) * 100
            self.logger.info(f"Text reduced by {reduction_pct:.1f}% ({char_reduction} characters)")
        
        token_reduction = metrics.get("token_reduction_percent", 0)
        if token_reduction:
            self.logger.info(f"Token reduction: {token_reduction:.1f}%")
    
    def log_processing_complete(self, 
                             file_name: str, 
                             success: bool, 
                             processing_time: float, 
                             error: Optional[str] = None) -> None:
        """Log the completion of a file processing operation.
        
        Args:
            file_name: Name of the file that was processed
            success: Whether the processing was successful
            processing_time: Processing time in seconds
            error: Optional error message
        """
        if success:
            self.logger.info(f"Successfully processed {file_name} in {processing_time:.2f}s")
        else:
            self.logger.error(f"Failed to process {file_name} after {processing_time:.2f}s: {error}")
    
    def log_directory_results(self, total: int, successful: int, failed: int, time_taken: float) -> None:
        """Log the results of a directory processing operation.
        
        Args:
            total: Total number of files processed
            successful: Number of successfully processed files
            failed: Number of failed files
            time_taken: Total processing time in seconds
        """
        self.logger.info(f"Directory processing complete: {successful}/{total} files processed successfully in {time_taken:.2f}s")
        if failed > 0:
            self.logger.warning(f"{failed} files failed processing")


# Create a singleton instance for common logging patterns
processing_logger = ProcessingLogger(__name__)
