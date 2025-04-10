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

from tqdm import tqdm # Add tqdm import

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
        quiet_mode: bool = False,
        no_progress: bool = False,
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

        # Simpler logging for directory processing start
        if not quiet_mode:
            print(f"Processing {total_files} files from: {input_dir_p}")

        results = []
        successful = 0
        failed = 0
        
        # Process files without tqdm progress bar
        for i, file_path in enumerate(files_to_process):
            current_file_num = i + 1
            if not quiet_mode and not no_progress:
                progress_pct = int((current_file_num / total_files) * 100)
                print(f"Processing \"{file_path.name}\" ({current_file_num}/{total_files})")
                print(f"----------{progress_pct}%")
                
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
                    self.logger.error(f"Failed: {file_path.name} - {result.error}")
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error processing file {file_path.name}: {e}")
                results.append(ProcessingResult(
                    input_path=file_path, 
                    success=False, 
                    error=f"Unexpected error: {str(e)}"
                ))
                failed += 1

        # Calculate token reduction statistics if available
        if successful > 0 and not quiet_mode:
            # Don't print token stats here - they will be displayed by the CLI command
            # Just calculate them for internal use if needed
            total_original_tokens = sum(r.metrics.get("original_token_estimate", 0) or r.metrics.get("original_tokens", 0) for r in results if r.success)
            total_processed_tokens = sum(r.metrics.get("processed_token_estimate", 0) or r.metrics.get("processed_tokens", 0) for r in results if r.success)
            if total_original_tokens > 0:
                reduction_percent = ((total_original_tokens - total_processed_tokens) / total_original_tokens) * 100
                # Remove the print statement that duplicates the CLI output
                # print(f"\nToken reduction: {total_original_tokens:,} → {total_processed_tokens:,} ({reduction_percent:.1f}%)")

        # Log completion message
        self.logger.info(f"Sequential directory processing complete: {successful} successful, {failed} failed")
        
        return results

    def process_directory_parallel(
        self,
        input_dir: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        output_format: Optional[str] = None,
        recursive: bool = True,
        file_extensions: Optional[List[str]] = None,
        max_workers: Optional[int] = None,
        quiet_mode: bool = False,
        no_progress: bool = False,
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

            # Simpler logging for directory processing start
            if not quiet_mode:
                print(f"Processing {total_files} files from: {input_dir_p}")

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

            results = [] # Initialize results before try block
            try:
                # Prepare tasks for parallel execution
                tasks = []
                task_ids = []
                for i, file_path in enumerate(files_to_process):
                    output_path = self._calculate_relative_output_path(
                        file_path, input_dir_p, output_dir_p, output_format
                    )
                    tasks.append((file_path, output_path, output_format))
                    task_ids.append(str(file_path)) # Use file path as task ID

                # Define the function to be executed in parallel
                def process_single_task(task_data: Tuple[Path, Path, str]) -> ProcessingResult:
                    file_path, output_path, fmt = task_data
                    # Custom progress output for each file
                    if not quiet_mode and not no_progress:
                        # Get current task index
                        task_idx = tasks.index(task_data) + 1
                        progress_pct = int((task_idx / total_files) * 100)
                        print(f"Processing \"{file_path.name}\" ({task_idx}/{total_files})")
                        print(f"----------{progress_pct}%")
                    return self.single_file_processor.process_file(file_path, output_path, fmt)

                # Execute tasks in parallel using the ParallelProcessor instance
                parallel_results: List[ParallelResult[Tuple[Path, Path, str], ProcessingResult]] = processor.process_items(
                    items=tasks,
                    process_func=process_single_task,
                    task_ids=task_ids,
                    use_processes=False, # Set explicitly to False (use threads)
                    show_progress=False  # We're handling our own progress display
                )

                # Convert ParallelResult back to ProcessingResult
                results = [pr.result for pr in parallel_results if pr.success]
                # Optionally log errors from pr.error where pr.success is False
                failed_results = [pr for pr in parallel_results if not pr.success]
                for fr in failed_results:
                    self.logger.error(f"Parallel task failed for input {fr.input_item[0]}: {fr.error}")
                    # Add a failed ProcessingResult to the main results list
                    failed_input_path, failed_output_path, _ = fr.input_item
                    results.append(ProcessingResult(
                        input_path=failed_input_path,
                        output_path=failed_output_path, 
                        success=False,
                        error=fr.error or "Parallel task failed without specific error message",
                        original_token_count=0, # Or fetch if possible
                        final_token_count=0,
                        processing_time=fr.processing_time
                    )) 

            except Exception as e:
                self.logger.error(f"Parallel execution failed: {e}", exc_info=True)

            successful = len([r for r in results if r.success])
            failed = len(results) - successful
            
            # Calculate token reduction statistics if available
            if successful > 0 and not quiet_mode:
                total_original_tokens = sum(r.metrics.get("original_token_estimate", 0) or r.metrics.get("original_tokens", 0) for r in results if r.success)
                total_processed_tokens = sum(r.metrics.get("processed_token_estimate", 0) or r.metrics.get("processed_tokens", 0) for r in results if r.success)
                if total_original_tokens > 0:
                    reduction_percent = ((total_original_tokens - total_processed_tokens) / total_original_tokens) * 100
                    # Remove the print statement that duplicates the CLI output
                    # print(f"\nToken reduction: {total_original_tokens:,} → {total_processed_tokens:,} ({reduction_percent:.1f}%)")

            # Log completion message
            self.logger.info(f"Parallel directory processing complete: {successful} successful, {failed} failed")
            
            return results