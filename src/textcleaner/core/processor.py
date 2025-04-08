"""Core text processor implementation."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
import concurrent.futures

from textcleaner.utils.logging_config import get_logger
from textcleaner.config.config_manager import ConfigManager
from textcleaner.config.config_factory import ConfigFactory
from textcleaner.converters.base import ConverterRegistry
from textcleaner.processors.processor_pipeline import ProcessorPipeline
from textcleaner.outputs.output_manager import OutputManager
from textcleaner.utils.metrics import calculate_metrics
from textcleaner.core.file_registry import FileTypeRegistry
from textcleaner.utils.security import SecurityUtils, security_utils
from textcleaner.utils.performance import performance_monitor
from textcleaner.utils.parallel import ParallelProcessor, ParallelResult


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
    
    This class ties together the converter registry, processor pipeline, file type registry,
    and output manager to provide a complete text processing workflow.
    
    The processor includes safety validations, parallel processing capabilities,
    and performance monitoring to ensure efficient and secure text processing.
    """
    
    def __init__(self, 
                config_path: Optional[str] = None,
                config_type: str = "standard",
                converter_registry: Optional[ConverterRegistry] = None,
                processor_pipeline: Optional[ProcessorPipeline] = None,
                file_registry: Optional[FileTypeRegistry] = None,
                output_manager: Optional[OutputManager] = None,
                security_utils: Optional[SecurityUtils] = None,
                parallel_processor: Optional[ParallelProcessor] = None):
        """Initialize the text processor.
        
        Args:
            config_path: Optional path to a configuration file.
            config_type: Type of configuration to use if no file is provided.
            converter_registry: Optional pre-configured converter registry.
            processor_pipeline: Optional pre-configured processor pipeline.
            file_registry: Optional pre-configured file type registry.
            output_manager: Optional pre-configured output manager.
            security_utils: Optional pre-configured security utilities.
            parallel_processor: Optional pre-configured parallel processor.
        """
        # Set up logging
        self.logger = get_logger(__name__)
        self.logger.info("Initializing TextProcessor")
        
        # Initialize configuration using the factory
        config_factory = ConfigFactory()
        self.config = config_factory.create_config(config_path, config_type)
        
        if config_path:
            self.logger.info(f"Using custom configuration from: {config_path}")
        else:
            self.logger.info(f"Using default {config_type} configuration")
        
        # Initialize components, using injected ones if provided
        self.file_registry = file_registry or FileTypeRegistry()
        self.converter_registry = converter_registry or self._setup_converters()
        self.processor_pipeline = processor_pipeline or self._setup_processor_pipeline()
        self.output_manager = output_manager or self._setup_output_manager()
        self.security = security_utils or SecurityUtils()
        self.parallel = parallel_processor or ParallelProcessor()
        
        # Initialize performance monitoring
        performance_monitor.reset()
        
        self.logger.info("TextProcessor initialization complete with security and parallel processing capabilities")
        
    def _setup_converters(self) -> ConverterRegistry:
        """Set up the converter registry with all available converters."""
        from textcleaner.converters import register_converters
        
        registry = register_converters()
        registry.set_config(self.config)
        
        return registry
        
    def _setup_processor_pipeline(self) -> ProcessorPipeline:
        """Set up the processor pipeline with appropriate processors."""
        return ProcessorPipeline(self.config)
        
    def _setup_output_manager(self) -> OutputManager:
        """Set up the output manager."""
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
            output_format: Format for the output file. If None, it will be
                determined based on the configuration.
                
        Returns:
            ProcessingResult object with the results of the processing.
            
        Raises:
            ValueError: If the file format is unsupported.
        """
        # Use performance monitoring context
        with performance_monitor.performance_context("process_file"):
            # Normalize paths
            input_path = Path(input_path) if isinstance(input_path, str) else input_path
            self.logger.info(f"Processing file: {input_path}")
            
            # Validate input file is safe to process
            is_valid, error = self.validate_file(input_path)
            if not is_valid:
                self.logger.error(f"File validation failed: {error}")
                return ProcessingResult(input_path, None, False, error)
            
            # Set default output path if not provided
            if output_path is None:
                output_dir = Path(self.config.get("general.output_dir", "processed_files"))
                output_dir.mkdir(exist_ok=True)
                
                # Set default output format
                output_format = output_format or self.config.get("output.default_format", "markdown")
                
                # Get file extension
                output_ext = self.config.get(
                    f"general.file_extension_mapping.{output_format}",
                    self._get_default_extension(output_format)
                )
                
                output_path = output_dir / f"{input_path.stem}.{output_ext}"
                self.logger.debug(f"Using default output path: {output_path}")
            else:
                output_path = Path(output_path) if isinstance(output_path, str) else output_path
                
            # Validate output path is safe to write to
            is_valid, error = self.validate_output_path(output_path)
            if not is_valid:
                self.logger.error(f"Output path validation failed: {error}")
                return ProcessingResult(input_path, None, False, error)
                
            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Start timing
            start_time = time.time()
        
        try:
            # Step 1: Find a converter for this file
            converter = self.converter_registry.find_converter(input_path)
            if converter is None:
                error_msg = f"No converter found for file type: {input_path.suffix}"
                self.logger.error(error_msg)
                return ProcessingResult(input_path, None, False, error_msg)
            
            # Step 2: Convert the document to text
            self.logger.debug(f"Using converter: {converter.__class__.__name__}")
            extracted_content, metadata = converter.convert(input_path)
            
            # Step 3: Apply processing pipeline
            self.logger.debug("Applying processing pipeline")
            processed_text = self.processor_pipeline.process(extracted_content, metadata)
            
            # Step 4: Write to output
            self.logger.debug(f"Writing output to: {output_path}")
            self.output_manager.write(processed_text, output_path, output_format)
            
            # Calculate metrics
            processing_time = time.time() - start_time
            metrics = calculate_metrics(
                raw_text=extracted_content,
                processed_text=processed_text,
                processing_time=processing_time
            )
            
            self.logger.info(f"Successfully processed {input_path.name}")
            return ProcessingResult(
                input_path=input_path,
                output_path=output_path,
                success=True,
                metrics=metrics,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.exception(f"Error processing file: {input_path}")
            return ProcessingResult(
                input_path=input_path,
                success=False,
                error=str(e),
                metrics={"processing_time_seconds": time.time() - start_time}
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
            recursive: Whether to recursively process subdirectories.
            file_extensions: List of file extensions to process. If None,
                processes all supported extensions.
                
        Returns:
            List of ProcessingResult objects for each file.
        """
        # Normalize paths
        input_dir = Path(input_dir) if isinstance(input_dir, str) else input_dir
        
        # Set default output dir if not provided
        if output_dir is None:
            output_dir = Path(self.config.get("general.output_dir", "processed_files"))
        else:
            output_dir = Path(output_dir) if isinstance(output_dir, str) else output_dir
            
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Processing directory: {input_dir}")
        self.logger.info(f"Output directory: {output_dir}")
        
        # Find files to process
        files_to_process = self._find_files_to_process(input_dir, recursive, file_extensions)
        total_files = len(files_to_process)
        self.logger.info(f"Found {total_files} files to process")
        
        # Process each file
        results = []
        successful = 0
        failed = 0
        
        for i, file_path in enumerate(files_to_process, 1):
            self.logger.info(f"Processing file {i}/{total_files}: {file_path.name}")
            
            # Calculate relative path from input_dir to file
            rel_path = file_path.relative_to(input_dir)
            
            # Create output path with the same relative structure
            rel_output_dir = output_dir / rel_path.parent
            rel_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine output file name
            output_fmt = output_format or self.config.get("output.default_format", "markdown")
            output_ext = self.config.get(
                f"general.file_extension_mapping.{output_fmt}",
                self._get_default_extension(output_fmt)
            )
            
            output_file = rel_output_dir / f"{file_path.stem}.{output_ext}"
            
            # Process the file
            result = self.process_file(file_path, output_file, output_format)
            
            if result.success:
                successful += 1
            else:
                failed += 1
                
            results.append(result)
            
        self.logger.info(f"Directory processing complete: {successful} successful, {failed} failed")
        return results
    
    def _find_files_to_process(
        self, 
        input_dir: Path, 
        recursive: bool = True,
        file_extensions: Optional[List[str]] = None
    ) -> List[Path]:
        """Find all files to process in a directory.
        
        Args:
            input_dir: Directory to search.
            recursive: Whether to recursively search subdirectories.
            file_extensions: List of file extensions to include.
            
        Returns:
            List of file paths to process.
        """
        files_to_process = []
        
        if recursive:
            # Walk directory tree
            for dirpath, _, filenames in os.walk(input_dir):
                for filename in filenames:
                    file_path = Path(dirpath) / filename
                    if self._should_process_file(file_path, file_extensions):
                        files_to_process.append(file_path)
        else:
            # Just top-level files
            for file_path in input_dir.iterdir():
                if file_path.is_file() and self._should_process_file(file_path, file_extensions):
                    files_to_process.append(file_path)
        
        return files_to_process
    
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
        # Use the file registry to determine if we should process this file
        process_file = self.file_registry.should_process_file(file_path, file_extensions)
        
        # Double-check with converter registry if file registry says no and no specific extensions were requested
        if not process_file and not file_extensions:
            # If we have a converter for this file, we should process it regardless
            process_file = self.converter_registry.find_converter(file_path) is not None
            
            if process_file:
                # Update the file registry with this information for future reference
                self.logger.debug(f"Discovered new processable extension: {file_path.suffix}")
                self.file_registry.register_extension(file_path.suffix, ["markdown", "plain_text"])
        
        return process_file
    
    def _get_default_extension(self, format_name: str) -> str:
        """Get the default file extension for a format."""
        return self.file_registry.get_default_extension(format_name)
    def process_directory_parallel(
        self,
        input_dir: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        output_format: Optional[str] = None,
        recursive: bool = True,
        file_extensions: Optional[List[str]] = None,
        max_workers: Optional[int] = None
    ) -> List[ProcessingResult]:
        """Process all supported files in a directory using parallel processing.
        
        Args:
            input_dir: Path to the input directory.
            output_dir: Path to the output directory. If None, uses config.
            output_format: Output format override.
            recursive: Whether to recursively process subdirectories.
            file_extensions: Optional list of file extensions to include.
            max_workers: Maximum number of parallel workers to use.
            
        Returns:
            List of ProcessingResult objects for each file.
        """
        with performance_monitor.performance_context("process_directory_parallel"):
            # Convert to Path objects
            input_dir = Path(input_dir) if isinstance(input_dir, str) else input_dir
            
            # Validate input directory exists and is secure
            is_valid, error = self.security.validate_path(input_dir)
            if not is_valid:
                self.logger.error(f"Cannot process directory: {error}")
                return [ProcessingResult(
                    input_path=input_dir, 
                    success=False, 
                    error=error)]
            
            # Validate input directory is actually a directory
            if not input_dir.is_dir():
                error = f"Input path is not a directory: {input_dir}"
                self.logger.error(error)
                return [ProcessingResult(
                    input_path=input_dir, 
                    success=False, 
                    error=error)]
            
            # Set output directory
            if output_dir is None:
                output_dir = Path(self.config.get("general.output_dir", "processed_files"))
            else:
                output_dir = Path(output_dir) if isinstance(output_dir, str) else output_dir
            
            # Validate output directory is secure
            is_valid, error = self.security.validate_output_path(output_dir)
            if not is_valid:
                self.logger.error(f"Cannot write to output directory: {error}")
                return [ProcessingResult(
                    input_path=input_dir, 
                    success=False, 
                    error=error)]
            
            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Find files to process
            files_to_process = self._find_files_to_process(input_dir, recursive, file_extensions)
            total_files = len(files_to_process)
            
            if total_files == 0:
                self.logger.warning(f"No files to process in {input_dir}")
                return []
                
            self.logger.info(f"Found {total_files} files to process in parallel")
            
            # Set up parallel processor if a custom worker count was provided
            processor = self.parallel
            if max_workers is not None:
                processor = ParallelProcessor(max_workers=max_workers)
                
            # Create task IDs for each file
            task_ids = [f"process_{i}_{file_path.name}" for i, file_path in enumerate(files_to_process)]
            
            # Create output paths for each file
            output_paths = []
            for file_path in files_to_process:
                # Calculate relative path from input_dir to file
                rel_path = file_path.relative_to(input_dir)
                
                # Create output path with the same relative structure
                rel_output_dir = output_dir / rel_path.parent
                
                # Determine output file name
                output_fmt = output_format or self.config.get("output.default_format", "markdown")
                output_ext = self.config.get(
                    f"general.file_extension_mapping.{output_fmt}",
                    self._get_default_extension(output_fmt)
                )
                
                output_file = rel_output_dir / f"{file_path.stem}.{output_ext}"
                output_paths.append(output_file)
            
            # Create a closure that captures the necessary variables
            def process_file_task(args):
                file_path, output_path = args
                return self.process_file(file_path, output_path, output_format)
            
            # Process files in parallel
            parallel_results = processor.process_items(
                items=list(zip(files_to_process, output_paths)),
                process_func=process_file_task,
                task_ids=task_ids,
                use_processes=False  # Use threads for I/O-bound operations
            )
            
            # Convert parallel results to ProcessingResult objects
            results = []
            for pr in parallel_results:
                if pr.success and isinstance(pr.result, ProcessingResult):
                    results.append(pr.result)
                else:
                    # Create a failure result if something went wrong
                    input_path = next((f for f, o in zip(files_to_process, output_paths) 
                                         if pr.metadata and pr.metadata.get("item") == str((f, o))),
                                       None) or files_to_process[0]
                    
                    results.append(ProcessingResult(
                        input_path=input_path,
                        success=False,
                        error=pr.error or "Unknown parallel processing error"
                    ))
            
            # Log summary
            successful = sum(1 for r in results if r.success)
            failed = total_files - successful
            
            self.logger.info(f"Parallel directory processing complete: {successful}/{total_files} successful, {failed} failed")
            
            # Save performance report if enabled
            if self.config.get("general.save_performance_report", False):
                report_path = output_dir / "performance_report.json"
                performance_monitor.save_report(report_path)
                self.logger.info(f"Performance report saved to {report_path}")
            
            return results
            
    def validate_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate that a file is safe to process.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if path is valid and secure
        is_valid, error = self.security.validate_path(file_path)
        if not is_valid:
            return False, error
            
        # Check if file exists
        if not file_path.exists():
            return False, f"File does not exist: {file_path}"
            
        # Check if is a file (not a directory)
        if not file_path.is_file():
            return False, f"Path is not a file: {file_path}"
            
        # Check if we have read permissions
        has_permission, error = self.security.check_file_permissions(file_path)
        if not has_permission:
            return False, error
            
        # Check if file is supported
        if not self._should_process_file(file_path):
            return False, f"Unsupported file type: {file_path.suffix}"
            
        return True, None
        
    def validate_output_path(self, output_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate that an output path is safe to write to.
        
        Args:
            output_path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.security.validate_output_path(output_path)
