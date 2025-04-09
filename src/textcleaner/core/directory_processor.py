"""Directory processing functionality for TextCleaner."""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Set
import concurrent.futures

from textcleaner.utils.logging_config import get_logger
from textcleaner.config.config_manager import ConfigManager
from textcleaner.core.models import ProcessingResult # Import from models
from textcleaner.utils.security import SecurityUtils
from textcleaner.utils.performance import performance_monitor
from textcleaner.utils.parallel import ParallelProcessor, ParallelResult
from textcleaner.utils.file_utils import find_files, get_default_extension, get_format_from_extension

# Forward declaration for type hinting
if False:
    from textcleaner.core.processor import TextProcessor

class DirectoryProcessor:
    """Handles processing of entire directories of files."""

    def __init__(
        self,
        config: ConfigManager,
        security_utils: SecurityUtils,
        parallel_processor: ParallelProcessor,
        single_file_processor: 'TextProcessor' # Use forward declaration
    ):
        self.logger = get_logger(__name__)
        self.config = config
        self.security = security_utils
        self.parallel = parallel_processor
        self.single_file_processor = single_file_processor

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

        if output_dir is None:
            output_dir_p = Path(self.config.get("general.output_dir", "processed_files"))
        else:
            output_dir_p = Path(output_dir) if isinstance(output_dir, str) else output_dir

        is_valid, error = self.security.validate_output_path(output_dir_p)
        if not is_valid:
            raise PermissionError(f"Output directory validation failed: {error}")

        try:
            output_dir_p.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Failed to create output directory {output_dir_p}: {e}") from e

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
                # Pass the original file_extensions list here as _should_process_file expects it
                # (although its internal logic also needs checking/fixing)
                if self.single_file_processor._should_process_file(file_path, file_extensions):
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

        final_output_format = output_format or self.config.get("output.default_format", "markdown")
        # Use utility function for extension
        output_ext = self.config.get(
            f"general.file_extension_mapping.{final_output_format}",
            get_default_extension(final_output_format, self.single_file_processor.file_registry)
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
            if max_workers is not None:
                if not isinstance(processor, ParallelProcessor):
                     processor = ParallelProcessor(max_workers=max_workers)
                else:
                     processor = ParallelProcessor(max_workers=max_workers)

            tasks_args = []
            task_id_to_input_path = {}
            skipped_results = []
            for i, file_path in enumerate(files_to_process):
                task_id = f"process_{i}_{file_path.name}"
                try:
                    output_file = self._calculate_relative_output_path(
                        file_path, input_dir_p, output_dir_p, output_format
                    )
                    tasks_args.append((file_path, output_file))
                    task_id_to_input_path[task_id] = file_path
                except Exception as e:
                    self.logger.error(f"Error preparing task for {file_path.name}, skipping: {e}")
                    skipped_results.append(ProcessingResult(input_path=file_path, success=False, error=f"Failed task preparation: {e}"))

            if not tasks_args:
                 self.logger.warning("No tasks could be prepared for parallel processing.")
                 return skipped_results

            def process_file_task(args: Tuple[Path, Path]) -> ProcessingResult:
                file_path, output_path = args
                return self.single_file_processor.process_file(file_path, output_path, output_format)

            parallel_results: List[ParallelResult] = processor.process_items(
                items=tasks_args,
                process_func=process_file_task,
                task_ids=list(task_id_to_input_path.keys()),
                use_processes=False
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

            self.logger.info(f"Parallel directory processing complete: {successful}/{total_files} successful, {failed} failed (including {len(skipped_results)} skipped preparation)")

            if self.config.get("general.save_performance_report", False):
                report_path = output_dir_p / "performance_report.json"
                performance_monitor.save_report(report_path)
                self.logger.info(f"Performance report saved to {report_path}")
            
            return results 