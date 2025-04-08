"""Models for the text processor core functionality."""

from pathlib import Path
from typing import Any, Dict, Optional


class ProcessingResult:
    """Result of a text processing operation."""
    
    def __init__(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        success: bool = True,
        error: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the processing result.
        
        Args:
            input_path: Path to the input file.
            output_path: Path to the output file (if successful).
            success: Whether the processing was successful.
            error: Error message (if unsuccessful).
            metrics: Processing metrics.
            metadata: Metadata extracted from the file.
        """
        self.input_path = input_path
        self.output_path = output_path
        self.success = success
        self.error = error
        self.metrics = metrics or {}
        self.metadata = metadata or {}
        self.processing_time = self.metrics.get("processing_time_seconds", 0)
    
    def __str__(self) -> str:
        """Return a string representation of the result."""
        if self.success:
            return f"Successfully processed '{self.input_path.name}' to '{self.output_path.name}' in {self.processing_time:.2f}s"
        else:
            return f"Failed to process '{self.input_path.name}': {self.error}" 