"""Core text processor implementation."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
# import concurrent.futures # Removed - Unused import

from textcleaner.utils.logging_config import get_logger
from textcleaner.config.config_manager import ConfigManager
from textcleaner.config.config_factory import ConfigFactory
from textcleaner.converters.base import ConverterRegistry, BaseConverter
from textcleaner.processors.processor_pipeline import ProcessorPipeline
from textcleaner.outputs.output_manager import OutputManager
from textcleaner.utils.metrics import calculate_metrics
from textcleaner.core.file_registry import FileTypeRegistry
from textcleaner.utils.security import SecurityUtils
from textcleaner.utils.performance import performance_monitor
# from textcleaner.utils.parallel import ParallelProcessor # Removed - Unused in this class (commented out below)
from textcleaner.utils.file_utils import get_default_extension, get_format_from_extension
from textcleaner.utils.file_utils import resolve_output_dir, determine_output_format_and_extension
from textcleaner.core.models import ProcessingResult # Import from models


class TextProcessor:
    """Main text processor coordinating components for single file processing.
    
    This class ties together the converter registry, processor pipeline, file type registry,
    and output manager to provide a complete text processing workflow for individual files.
    It includes safety validations and performance monitoring.
    Directory processing is handled by the DirectoryProcessor class.
    """
    
    def __init__(self, 
                config: ConfigManager,
                converter_registry: ConverterRegistry,
                processor_pipeline: ProcessorPipeline,
                file_registry: FileTypeRegistry,
                output_manager: OutputManager,
                security_utils: SecurityUtils):
        """Initialize the text processor with components for single file processing.
        
        Args:
            config: Configuration manager instance.
            converter_registry: Pre-configured converter registry.
            processor_pipeline: Pre-configured processor pipeline.
            file_registry: Pre-configured file type registry.
            output_manager: Pre-configured output manager.
            security_utils: Pre-configured security utilities.
        """
        self.logger = get_logger(__name__)
        self.logger.info("Initializing TextProcessor")
        
        self.config = config
        self.file_registry = file_registry
        self.converter_registry = converter_registry
        self.processor_pipeline = processor_pipeline
        self.output_manager = output_manager
        self.security = security_utils
        # self.parallel = parallel_processor # Removed, handled by DirectoryProcessor
        
        performance_monitor.reset()
        self.logger.info("TextProcessor initialization complete")
        
    def process_file(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        output_format: Optional[str] = None,
    ) -> ProcessingResult:
        """Process a single file after validation and path preparation."""
        start_time = time.time()
        
        with performance_monitor.performance_context("process_file"):
            try:
                validated_input_path, validated_output_path, final_output_format = \
                    self._prepare_and_validate_paths(input_path, output_path, output_format)
                
                return self._execute_processing_steps(
                    validated_input_path, 
                    validated_output_path, 
                    final_output_format, 
                    start_time
                )
    
            except (ValueError, FileNotFoundError, PermissionError, RuntimeError) as e:
                self.logger.error(f"Processing failed for {input_path}: {str(e)}")
                input_path_p = Path(input_path) if isinstance(input_path, str) else input_path 
                return ProcessingResult(
                    input_path=input_path_p,
                    success=False,
                    error=str(e),
                    metrics={"processing_time_seconds": time.time() - start_time}
                )
            except Exception as e: 
                self.logger.exception(f"Unexpected error processing file: {input_path}")
                input_path_p = Path(input_path) if isinstance(input_path, str) else input_path 
                return ProcessingResult(
                    input_path=input_path_p,
                    success=False,
                    error=f"Unexpected error: {str(e)}",
                    metrics={"processing_time_seconds": time.time() - start_time}
                )

    def _prepare_and_validate_paths(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]],
        output_format: Optional[str],
    ) -> Tuple[Path, Path, str]:
        """Normalize, validate paths, and determine final output format."""
        input_path_p = Path(input_path) if isinstance(input_path, str) else input_path
        self.logger.info(f"Preparing to process file: {input_path_p}")

        is_valid, error = self.validate_file(input_path_p)
        if not is_valid:
            raise ValueError(f"Input file validation failed: {error}")

        # Determine output path if not provided
        output_path_p: Optional[Path] = None
        if output_path is None:
             # Output dir resolution and validation is deferred if path is None
             # We only need the path later if we construct it here
             output_dir = Path(self.config.get("general.output_dir", "processed_files"))
             # Validation of this default dir happens implicitly in resolve_output_dir if used later
        else:
            output_path_p = Path(output_path) if isinstance(output_path, str) else output_path

        # Determine final format and extension using the new utility
        # Pass output_path_p (which might be None)
        final_output_format, output_ext = determine_output_format_and_extension(
            output_format_param=output_format,
            output_path_param=output_path_p, # Pass the Path object or None
            config=self.config,
            file_registry=self.file_registry
        )

        # Construct the final output path if it wasn't provided
        if output_path_p is None:
            # Resolve the actual output directory (handles creation and validation)
            output_dir_resolved = resolve_output_dir(None, self.config, self.security)
            output_path_p = output_dir_resolved / f"{input_path_p.stem}.{output_ext}"
            self.logger.debug(f"Using default output path: {output_path_p}")
        else:
            # Validate the *provided* output path and ensure parent dir exists
            is_valid, error = self.validate_output_path(output_path_p)
            if not is_valid:
                raise PermissionError(f"Output path validation failed: {error}")
            try:
                output_path_p.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                 raise RuntimeError(f"Failed to create output directory {output_path_p.parent}: {e}") from e

        # The final output path (output_path_p) is now guaranteed to be a Path object
        return input_path_p, output_path_p, final_output_format

    def _execute_processing_steps(
        self,
        input_path: Path,
        output_path: Path,
        output_format: str,
        start_time: float
    ) -> ProcessingResult:
        """Execute the core conversion, processing, and output steps."""
        with performance_monitor.performance_context("execute_processing_steps"):
            converter = self.converter_registry.find_converter(input_path)
            if converter is None:
                raise ValueError(f"No converter found for file type: {input_path.suffix}")
            
            self.logger.debug(f"Using converter: {converter.__class__.__name__}")
            try:
                extracted_content, metadata = converter.convert(input_path)
                if not extracted_content:
                    error_detail = metadata.get("conversion_error_details")
                    if error_detail:
                        raise RuntimeError(f"Conversion failed for {input_path}: {error_detail}")
                    else:
                        raise RuntimeError(f"Conversion resulted in empty content for {input_path}")
            except Exception as e:
                self.logger.error(f"Conversion step failed for {input_path} with error type {type(e).__name__}: {e}")
                raise RuntimeError(f"Conversion failed for {input_path}: {e}") from e

            self.logger.debug("Applying processing pipeline")
            try:
                processed_text = self.processor_pipeline.process(extracted_content, metadata)
            except Exception as e:
                raise RuntimeError(f"Processing pipeline failed for {input_path}: {e}") from e
            
            self.logger.debug(f"Writing output to: {output_path}")
            try:
                self.output_manager.write(processed_text, output_path, output_format)
            except Exception as e:
                raise RuntimeError(f"Failed to write output to {output_path}: {e}") from e
            
            processing_time = time.time() - start_time
            metrics = calculate_metrics(
                raw_text=extracted_content,
                processed_text=processed_text,
                processing_time=processing_time,
                config=self.config,
                input_file_stats=metadata.get("file_stats")
            )
            
            self.logger.info(f"Successfully processed {input_path.name} to {output_path.name}")
            return ProcessingResult(
                input_path=input_path,
                output_path=output_path,
                success=True,
                metrics=metrics,
                metadata=metadata
            )
    
    def _should_process_file(
        self, 
        file_path: Path, 
        file_extensions: Optional[List[str]] = None
    ) -> bool:
        """Determine if a file should be processed based on registry and converters."""
        # Primarily rely on file registry
        process_file = self.file_registry.should_process_file(file_path, file_extensions)
        
        # If specific extensions are given, respect that strictly
        if file_extensions is not None:
             return process_file
             
        # If no specific extensions requested and registry says no, check converter registry
        # This helps discover files if registry is not perfectly up-to-date
        if not process_file:
            converter = self.converter_registry.find_converter(file_path)
            if converter is not None:
                self.logger.debug(f"Processing file {file_path.name} based on converter availability (extension: {file_path.suffix})")
                # Optionally, could update FileTypeRegistry here if dynamic updates are desired
                # self.file_registry.register_extension(file_path.suffix, ["markdown", "plain_text"]) # Example
                return True
        
        return process_file
    
    def validate_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate that a file is safe to process."""
        is_valid, error = self.security.validate_path(file_path)
        if not is_valid:
            return False, error
            
        if not file_path.exists():
            return False, f"File does not exist: {file_path}"
            
        if not file_path.is_file():
            return False, f"Path is not a file: {file_path}"
            
        has_permission, error = self.security.check_file_permissions(file_path)
        if not has_permission:
            return False, error
            
        # Use the internal check method which also consults converters if needed
        if not self._should_process_file(file_path):
            return False, f"Unsupported file type or no converter found: {file_path.suffix}"
            
        return True, None
        
    def validate_output_path(self, output_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate that an output path is safe to write to."""
        return self.security.validate_output_path(output_path)
