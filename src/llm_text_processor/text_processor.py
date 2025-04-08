"""Core text processor implementation."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from llm_text_processor.config.config_manager import ConfigManager
from llm_text_processor.converters.base import ConverterRegistry
from llm_text_processor.processors.processor_pipeline import ProcessorPipeline
from llm_text_processor.outputs.output_manager import OutputManager
from llm_text_processor.utils.metrics import calculate_metrics


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
            

class TextProcessor:
    """Main text processor coordinating all components.
    
    This class ties together the converter, processor pipeline, and output
    writer to provide a complete text processing workflow.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the text processor.
        
        Args:
            config_path: Optional path to a configuration file.
        """
        # Initialize configuration
        self.config = ConfigManager(config_path)
        
        # Initialize components
        self.converter_registry = self._setup_converters()
        self.processor_pipeline = self._setup_processor_pipeline()
        self.output_manager = self._setup_output_manager()
        
    def _setup_converters(self) -> ConverterRegistry:
        """Set up the converter registry with all available converters.
        
        Returns:
            Configured converter registry.
        """
        from llm_text_processor.converters import register_converters
        
        # Use our centralized registry initialization
        registry = register_converters()
        
        # Set the configuration for all converters
        registry.set_config(self.config)
        
        return registry
        
    def _setup_processor_pipeline(self) -> ProcessorPipeline:
        """Set up the processor pipeline with appropriate processors.
        
        Returns:
            Configured processor pipeline.
        """
        return ProcessorPipeline(self.config)
        
    def _setup_output_manager(self) -> OutputManager:
        """Set up the output manager.
        
        Returns:
            Configured output manager.
        """
        return OutputManager(self.config)
    
    def process_file(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        output_format: Optional[str] = None,
    ) -> ProcessingResult:
        """Process a single file.
        
        Args:
            input_path: Path to the input file.
            output_path: Path for the output file. If None, it will be
                generated based on the input path.
            output_format: Output format override (markdown, txt, json, csv).
                If None, the default from config is used.
                
        Returns:
            ProcessingResult with information about the processing.
            
        Raises:
            FileNotFoundError: If the input file doesn't exist.
            ValueError: If the file format is unsupported.
        """
        start_time = time.time()
        
        # Convert to Path objects
        if isinstance(input_path, str):
            input_path = Path(input_path)
        if isinstance(output_path, str):
            output_path = Path(output_path)
            
        # Check if input file exists
        if not input_path.exists():
            return ProcessingResult(
                input_path=input_path,
                success=False,
                error=f"Input file not found: {input_path}"
            )
            
        try:
            # Determine output path if not provided
            if output_path is None:
                output_format = output_format or self.config.get("output.default_format", "markdown")
                output_ext = self.config.get(
                    f"general.file_extension_mapping.{output_format}",
                    self._get_default_extension(output_format)
                )
                
                # Get output directory
                output_dir = Path(self.config.get("general.output_dir", "processed_files"))
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Create output path
                if self.config.get("general.preserve_original_filename", True):
                    output_path = output_dir / f"{input_path.stem}.{output_ext}"
                else:
                    # Use a sanitized version of the filename
                    from llm_text_processor.utils.file_utils import sanitize_filename
                    output_path = output_dir / f"{sanitize_filename(input_path.stem)}.{output_ext}"
            
            # Check if output file already exists and we should not overwrite
            if (
                output_path.exists() and 
                not self.config.get("general.overwrite_existing", False)
            ):
                return ProcessingResult(
                    input_path=input_path,
                    success=False,
                    error=f"Output file already exists: {output_path}"
                )
            
            # Step 1: Convert the file to raw text
            raw_text, metadata = self.converter_registry.convert_file(input_path)
            
            # Step 2: Process the raw text
            processed_text = self.processor_pipeline.process(raw_text, metadata)
            
            # Step 3: Write the processed text to the output file
            self.output_manager.write(
                processed_text,
                output_path,
                format=output_format,
                metadata=metadata
            )
            
            # Calculate metrics
            end_time = time.time()
            processing_time = end_time - start_time
            
            metrics = calculate_metrics(
                raw_text=raw_text,
                processed_text=processed_text,
                processing_time=processing_time,
                input_file_stats=metadata.get("file_stats", {})
            )
            
            return ProcessingResult(
                input_path=input_path,
                output_path=output_path,
                success=True,
                metrics=metrics,
                metadata=metadata
            )
            
        except Exception as e:
            # Calculate partial metrics
            end_time = time.time()
            processing_time = end_time - start_time
            
            return ProcessingResult(
                input_path=input_path,
                success=False,
                error=str(e),
                metrics={"processing_time_seconds": processing_time}
            )
    
    def process_directory(
        self,
        input_dir: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        output_format: Optional[str] = None,
        recursive: bool = True,
        file_extensions: Optional[List[str]] = None,
    ) -> List[ProcessingResult]:
        """Process all supported files in a directory.
        
        Args:
            input_dir: Path to the input directory.
            output_dir: Path to the output directory. If None, uses config.
            output_format: Output format override.
            recursive: Whether to process files in subdirectories.
            file_extensions: Optional list of file extensions to process.
                If None, all supported extensions are processed.
                
        Returns:
            List of ProcessingResult objects for each processed file.
            
        Raises:
            FileNotFoundError: If the input directory doesn't exist.
            ValueError: If the output directory cannot be created.
        """
        # Convert to Path objects
        if isinstance(input_dir, str):
            input_dir = Path(input_dir)
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)
            
        # Check if input directory exists
        if not input_dir.exists() or not input_dir.is_dir():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
            
        # Determine output directory
        if output_dir is None:
            output_dir = Path(self.config.get("general.output_dir", "processed_files"))
            
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all files to process
        files_to_process = []
        if recursive:
            # Walk directory tree
            for dirpath, _, filenames in os.walk(input_dir):
                for filename in filenames:
                    file_path = Path(dirpath) / filename
                    
                    # Check if this file should be processed
                    if self._should_process_file(file_path, file_extensions):
                        files_to_process.append(file_path)
        else:
            # Just top-level files
            for file_path in input_dir.iterdir():
                if file_path.is_file() and self._should_process_file(file_path, file_extensions):
                    files_to_process.append(file_path)
        
        # Process each file
        results = []
        for file_path in files_to_process:
            # Calculate relative path from input_dir to file
            rel_path = file_path.relative_to(input_dir)
            
            # Create output path with the same relative structure
            rel_output_dir = output_dir / rel_path.parent
            rel_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine output file name
            output_format = output_format or self.config.get("output.default_format", "markdown")
            output_ext = self.config.get(
                f"general.file_extension_mapping.{output_format}",
                self._get_default_extension(output_format)
            )
            
            output_file = rel_output_dir / f"{file_path.stem}.{output_ext}"
            
            # Process the file
            result = self.process_file(file_path, output_file, output_format)
            results.append(result)
            
        return results
    
    def _should_process_file(
        self, 
        file_path: Path, 
        file_extensions: Optional[List[str]] = None
    ) -> bool:
        """Determine if a file should be processed.
        
        Args:
            file_path: Path to the file.
            file_extensions: Optional list of file extensions to process.
            
        Returns:
            True if the file should be processed, False otherwise.
        """
        # Get file extension (without the dot)
        ext = file_path.suffix.lower()
        
        # If specific extensions were provided, check against those
        if file_extensions:
            return ext in file_extensions
            
        # Otherwise, check if we have a converter that can handle this file
        return self.converter_registry.find_converter(file_path) is not None
    
    def _get_default_extension(self, format_name: str) -> str:
        """Get the default file extension for a format.
        
        Args:
            format_name: Format name.
            
        Returns:
            Default file extension for the format.
        """
        format_to_ext = {
            "markdown": "md",
            "plain_text": "txt",
            "json": "json",
            "csv": "csv",
        }
        return format_to_ext.get(format_name, "txt")
