"""Directory processing functionality for TextCleaner."""

# import time # Removed - Unused import
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Set
# import concurrent.futures # Removed - Unused import

from textcleaner.utils.logging_config import get_logger
from textcleaner.config.config_manager import ConfigManager
from textcleaner.core.models import ProcessingResult # Import from models
from textcleaner.utils.security import SecurityUtils
from textcleaner.utils.performance import performance_monitor
from textcleaner.utils.parallel import ParallelProcessor, ParallelResult
from textcleaner.utils.file_utils import (
    find_files, 
    get_default_extension, # Still needed for fallback logic within the utility
    get_format_from_extension, # Used by the utility
    resolve_output_dir, 
    determine_output_format_and_extension
)

# Forward declaration using string literal is sufficient
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from textcleaner.core.processor import TextProcessor

class DirectoryProcessor:
    """Handles processing of entire directories of files."""

    def __init__(
        self,
        config: ConfigManager,
        security_utils: SecurityUtils,
        parallel_processor: ParallelProcessor,
        single_file_processor: 'TextProcessor' # String literal hint
    ):
        self.logger = get_logger(__name__)
        self.config = config
        self.security = security_utils
        self.parallel = parallel_processor
        self.single_file_processor = single_file_processor
        # Ensure the single file processor uses the same security context
        self.single_file_processor.security = self.security

    def _prepare_directory_processing(
        self,
        input_dir: Union[str, Path],
        output_dir: Optional[Union[str, Path]],
        recursive: bool,
        file_extensions: Optional[List[str]]
    ) -> Tuple[Path, Path, List[Path]]:
        """Validate paths, setup directories, and find files for directory processing."""
        input_dir_p = Path(input_dir) if isinstance(input_dir, str) else input_dir
        is_valid, error = self.security.validate_path(input_dir_p)
        if not is_valid:
            raise ValueError(f"Input directory validation failed: {error}")
        if not input_dir_p.is_dir():
            raise ValueError(f"Input path is not a directory: {input_dir_p}")

        # Resolve, validate, and create the output directory using the utility
        output_dir_p = resolve_output_dir(output_dir, self.config, self.security)

        files_to_process = self._find_files_to_process(input_dir_p, recursive, file_extensions)

        return input_dir_p, output_dir_p, files_to_process

    def _find_files_to_process(
        self, 
        input_dir: Path, 
        recursive: bool = True,
        file_extensions: Optional[List[str]] = None
    ) -> List[Path]:
        """Find all files to process in a directory, applying filters early."""
        files_to_process = []
        extension_process_cache: Dict[str, bool] = {} # Cache for extension processability
        try:
            # Normalize filter extensions ONCE (ensure leading dot, lower case)
            normalized_filter_extensions: Optional[Set[str]] = None
            if file_extensions is not None:
                normalized_filter_extensions = { 
                    ext.lower() if ext.startswith('.') else f".{ext.lower()}" 
                    for ext in file_extensions 
                }

            for file_path in find_files(input_dir, recursive):
                file_ext_with_dot = file_path.suffix.lower()
                
                # Apply file extension filter FIRST (using dot comparison)
                if normalized_filter_extensions is not None:
                    if file_ext_with_dot not in normalized_filter_extensions:
                        continue # Skip if extension doesn't match filter
                
                # THEN check if the file processor supports/should handle it (includes security)
                # Check cache first
                should_process = extension_process_cache.get(file_ext_with_dot)
                if should_process is None:
                    # Not in cache, perform the check
                    should_process = self.single_file_processor._should_process_file(file_path)
                    # Store result in cache
                    extension_process_cache[file_ext_with_dot] = should_process
                
                if should_process:
                    files_to_process.append(file_path)
        except (FileNotFoundError, NotADirectoryError) as e:
            self.logger.error(f"Error finding files in {input_dir}: {e}")
            return []
        return files_to_process

    def _calculate_relative_output_path(
        self,
        input_file: Path,
        input_dir: Path,
        output_dir: Path,
        output_format: Optional[str]
    ) -> Path:
        """Calculate the output path for a file, preserving relative structure."""
        try:
            rel_path = input_file.relative_to(input_dir)
        except ValueError:
             self.logger.warning(f"Could not determine relative path for {input_file} within {input_dir}. Placing in root of output.")
             rel_path = Path(input_file.name)

        rel_output_dir = output_dir / rel_path.parent
        rel_output_dir.mkdir(parents=True, exist_ok=True)

        # Determine format and extension using the utility
        # We don't have an explicit output path parameter here, so pass None
        final_output_format, output_ext = determine_output_format_and_extension(
            output_format_param=output_format, 
            output_path_param=None, # Output path is being constructed
            config=self.config, 
            file_registry=self.single_file_processor.file_registry
        )

        return rel_output_dir / f"{input_file.stem}.{output_ext}"

    def process_directory(
        self,
        input_dir: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        output_format: Optional[str] = None,
        recursive: bool = True,
        file_extensions: Optional[List[str]] = None,
    ) -> List[ProcessingResult]:
        """Process all supported files in a directory sequentially."""
        self.logger.info(f"Starting sequential processing for directory: {input_dir}")
        try:
            input_dir_p, output_dir_p, files_to_process = self._prepare_directory_processing(
                input_dir, output_dir, recursive, file_extensions
            )
        except (ValueError, PermissionError, RuntimeError) as e:
            self.logger.error(f"Directory processing setup failed: {e}")
            input_path_p = Path(input_dir) if isinstance(input_dir, str) else input_dir
            return [ProcessingResult(input_path=input_path_p, success=False, error=str(e))]

        total_files = len(files_to_process)
        if total_files == 0:
            self.logger.warning(f"No files to process in {input_dir_p}")
            return []

        self.logger.info(f"Found {total_files} files to process sequentially in {input_dir_p}")
        self.logger.info(f"Output directory: {output_dir_p}")

        results = []
        successful = 0
        failed = 0

        for i, file_path in enumerate(files_to_process, 1):
            self.logger.info(f"Processing file {i}/{total_files}: {file_path.name}")
            try:
                output_file = self._calculate_relative_output_path(
                    file_path, input_dir_p, output_dir_p, output_format
                )
                # Use the single file processor
                result = self.single_file_processor.process_file(file_path, output_file, output_format)
                if result.success:
                    successful += 1
                else:
                    failed += 1
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error processing file {file_path.name}: {e}")
                results.append(ProcessingResult(
                    input_path=file_path, 
                    success=False, 
                    error=f"Unexpected error: {str(e)}"
                ))
                failed += 1

        self.logger.info(f"Sequential directory processing complete: {successful} successful, {failed} failed")
        return results

    def process_directory_parallel(
        self,
        input_dir: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        output_format: Optional[str] = None,
        recursive: bool = True,
        file_extensions: Optional[List[str]] = None,
        max_workers: Optional[int] = None
    ) -> List[ProcessingResult]:
        """Process all supported files in a directory using parallel processing."""
        with performance_monitor.performance_context("process_directory_parallel"):
            self.logger.info(f"Starting parallel processing for directory: {input_dir}")
            try:
                input_dir_p, output_dir_p, files_to_process = self._prepare_directory_processing(
                    input_dir, output_dir, recursive, file_extensions
                )
            except (ValueError, PermissionError, RuntimeError) as e:
                self.logger.error(f"Directory processing setup failed: {e}")
                input_path_p = Path(input_dir) if isinstance(input_dir, str) else input_dir
                return [ProcessingResult(input_path=input_path_p, success=False, error=str(e))]

            total_files = len(files_to_process)
            if total_files == 0:
                self.logger.warning(f"No files to process in {input_dir_p}")
                return []

            self.logger.info(f"Found {total_files} files to process in parallel (max_workers={max_workers or 'default'}) in {input_dir_p}")
            self.logger.info(f"Output directory: {output_dir_p}")

            processor = self.parallel
            # If specific max_workers are requested, create a new processor instance for this run
            # Otherwise, use the default processor passed during initialization.
            if max_workers is not None:
                self.logger.debug(f"Creating temporary ParallelProcessor with max_workers={max_workers}")
                # Ensure it's an instance of ParallelProcessor, default if not somehow passed
                if not isinstance(processor, ParallelProcessor):
                     processor = ParallelProcessor(max_workers=max_workers)
                else:
                     # Create a new instance with the specified worker count
                     processor = ParallelProcessor(max_workers=max_workers)

            # tasks_args = [] # Removed: Will pass file_path directly
            task_id_to_input_path = {} # Keep for associating results back if needed
            skipped_results = []
            # Prepare list of input files and task IDs directly
            input_files_to_process = []
            task_ids = []

            for i, file_path in enumerate(files_to_process):
                # Basic check to skip files that cannot be processed (e.g., permission issues detected earlier)
                # Although _find_files_to_process should filter most, this is a safeguard
                if not file_path.is_file(): # Simple check
                    self.logger.warning(f"Skipping non-file path during parallel task prep: {file_path}")
                    skipped_results.append(ProcessingResult(input_path=file_path, success=False, error="Path is not a file"))
                    continue
                
                task_id = f"process_{i}_{file_path.name}"
                input_files_to_process.append(file_path)
                task_ids.append(task_id)
                task_id_to_input_path[task_id] = file_path

            if not input_files_to_process:
                 self.logger.warning("No tasks could be prepared for parallel processing.")
                 return skipped_results

            # Define the task function executed by each worker
            def process_file_task(file_path: Path) -> ProcessingResult:
                try:
                    # Calculate output path inside the parallel task
                    output_path = self._calculate_relative_output_path(
                        file_path, input_dir_p, output_dir_p, output_format
                    )
                    # Process the file using the single file processor
                    return self.single_file_processor.process_file(file_path, output_path, output_format)
                except Exception as e:
                    # Catch errors during path calculation or processing within the task
                    self.logger.error(f"Error in parallel task for {file_path.name}: {e}")
                    return ProcessingResult(
                        input_path=file_path,
                        success=False,
                        error=f"Parallel task failed: {str(e)}"
                    )

            # Pass the list of input file paths directly to process_items
            parallel_results: List[ParallelResult[Path, ProcessingResult]] = processor.process_items(
                items=input_files_to_process, # Pass input file paths
                process_func=process_file_task,
                task_ids=task_ids, # Pass the generated task IDs
                use_processes=False # Keep using threads for now unless I/O bound is confirmed bottleneck
            )

            results = skipped_results
            for pr in parallel_results:
                if pr.success and isinstance(pr.result, ProcessingResult):
                    results.append(pr.result)
                else:
                    input_path = task_id_to_input_path.get(pr.task_id)
                    if input_path:
                        results.append(ProcessingResult(
                            input_path=input_path,
                            success=False,
                            error=pr.error or "Unknown parallel processing error"
                        ))
                    else:
                        self.logger.error(f"Failed parallel task {pr.task_id} for an unknown input file. Error: {pr.error}")

            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful

            # Calculate average token reduction
            total_token_reduction = 0
            reduction_count = 0
            for r in results:
                if r.success and r.metrics and "token_reduction_percent" in r.metrics:
                    try:
                        total_token_reduction += float(r.metrics["token_reduction_percent"])
                        reduction_count += 1
                    except (ValueError, TypeError):
                        pass # Ignore results with invalid metric data
            
            avg_token_reduction = total_token_reduction / reduction_count if reduction_count > 0 else 0

            # Log summary including average reduction
            self.logger.info(f"Parallel directory processing complete: {successful}/{total_files} successful, {failed} failed (including {len(skipped_results)} skipped preparation)")
            self.logger.info(f"Average token reduction across successful files: {avg_token_reduction:.2f}%")

            if self.config.get("general.save_performance_report", False):
                report_path = output_dir_p / "performance_report.json"
                performance_monitor.save_report(report_path)
                self.logger.info(f"Performance report saved to {report_path}")
            
            return results 