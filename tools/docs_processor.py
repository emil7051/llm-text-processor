#!/usr/bin/env python3
"""
Script to process documents in batch mode using TextCleaner.

This utility can be used to process multiple documents from a directory,
applying TextCleaner's processing pipeline with configurable settings.
"""

import sys
import os
from pathlib import Path
import random
import csv
from datetime import datetime
import io
import re
import argparse
from typing import List, Dict, Any, Optional, Tuple

# Import TextCleaner components 
from textcleaner.core.processor import TextProcessor
from textcleaner.config.config_manager import ConfigManager
from textcleaner.core.models import ProcessingResult
from textcleaner.utils.logging_config import get_logger

# Setup logging
logger = get_logger("docs_processor")

# Constants
DEFAULT_OUTPUT_DIR = Path("processed_files") / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
DEFAULT_MAX_FILES = 20
DEFAULT_CONFIG_TYPE = "standard"

# Define which file types to process
SUPPORTED_EXTENSIONS = ['.txt', '.html', '.md', '.pdf', '.docx', '.csv', '.xlsx', '.pptx']


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Process documents using TextCleaner in batch mode.'
    )
    
    parser.add_argument(
        'input_dir', 
        type=str,
        help='Directory containing files to process'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        default=None,
        help=f'Output directory for processed files (default: {DEFAULT_OUTPUT_DIR})'
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        default=DEFAULT_CONFIG_TYPE,
        choices=['minimal', 'standard', 'aggressive'],
        help=f'Configuration type to use (default: {DEFAULT_CONFIG_TYPE})'
    )
    
    parser.add_argument(
        '-m', '--max-files',
        type=int,
        default=DEFAULT_MAX_FILES,
        help=f'Maximum number of files to process (default: {DEFAULT_MAX_FILES})'
    )
    
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Recursively process subdirectories'
    )
    
    parser.add_argument(
        '-e', '--extensions',
        type=str,
        default=None,
        help='Comma-separated list of file extensions to process (e.g., .txt,.pdf)'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Process files in parallel using multiple threads'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=None,
        help='Number of parallel workers to use (default: automatic)'
    )
    
    return parser.parse_args()


def get_sample_files(
    directory: Path, 
    max_files: int = DEFAULT_MAX_FILES,
    recursive: bool = False,
    extensions: Optional[List[str]] = None
) -> List[Path]:
    """
    Get a sample of files from the directory with supported extensions.
    
    Args:
        directory: Directory to search for files
        max_files: Maximum number of files to return
        recursive: Whether to recursively search subdirectories
        extensions: List of file extensions to include
        
    Returns:
        List of Path objects for the files
    """
    files = []
    extensions = extensions or SUPPORTED_EXTENSIONS
    
    if recursive:
        # Recursively walk the directory
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.suffix.lower() in extensions:
                    files.append(file_path)
    else:
        # Only search the specified directory
        for file_path in directory.glob('*'):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                files.append(file_path)
    
    # Log the found files
    logger.info(f"Found {len(files)} files with supported extensions in {directory}")
    
    # Randomly select up to max_files
    if len(files) > max_files:
        files = random.sample(files, max_files)
        logger.info(f"Randomly sampled {len(files)} files for processing")
    
    return files


def create_processor(config_type: str) -> TextProcessor:
    """
    Create a TextProcessor with the specified configuration.
    
    Args:
        config_type: Configuration type ('minimal', 'standard', 'aggressive')
        
    Returns:
        Configured TextProcessor instance
    """
    # Create processor with the specified configuration
    processor = TextProcessor(config_type=config_type)
    
    logger.info(f"Created TextProcessor with {config_type} configuration")
    return processor


def process_files(
    processor: TextProcessor,
    file_paths: List[Path],
    output_dir: Path,
    use_parallel: bool = False,
    max_workers: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Process a list of files using the TextProcessor.
    
    Args:
        processor: TextProcessor instance to use
        file_paths: List of Path objects for the files to process
        output_dir: Directory to save processed files
        use_parallel: Whether to process files in parallel
        max_workers: Number of parallel workers to use
        
    Returns:
        List of dictionaries with processing results
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process the files
    if use_parallel:
        logger.info(f"Processing {len(file_paths)} files in parallel")
        
        # Define output paths
        output_paths = [output_dir / f"{path.stem}_processed.md" for path in file_paths]
        
        # Process in parallel
        processing_results = processor.process_multiple_parallel(
            list(zip(file_paths, output_paths)),
            max_workers=max_workers
        )
    else:
        logger.info(f"Processing {len(file_paths)} files sequentially")
        
        # Process sequentially
        processing_results = []
        for file_path in file_paths:
            output_path = output_dir / f"{file_path.stem}_processed.md"
            result = processor.process_file(file_path, output_path)
            processing_results.append(result)
    
    # Convert the ProcessingResult objects to dictionaries for reporting
    results = []
    for result in processing_results:
        # Calculate file sizes
        input_path = Path(result.input_path)
        output_path = result.output_path
        
        try:
            input_size = input_path.stat().st_size
            output_size = Path(output_path).stat().st_size if result.success else 0
            size_reduction = 1 - (output_size / input_size) if input_size > 0 and output_size > 0 else 0
        except (FileNotFoundError, OSError):
            input_size = 0
            output_size = 0
            size_reduction = 0
        
        # Get metrics from the result
        metrics = result.metrics or {}
        
        # Create a dictionary with result data
        result_data = {
            "filename": input_path.name,
            "file_type": input_path.suffix,
            "success": result.success,
            "error": result.error if not result.success else "",
            "input_size_bytes": input_size,
            "output_size_bytes": output_size,
            "size_reduction_percent": f"{size_reduction * 100:.2f}%",
            "token_reduction_percent": (
                f"{metrics.get('token_reduction_percent', 0):.2f}%" 
                if result.success and 'token_reduction_percent' in metrics else "N/A"
            ),
            "input_tokens": metrics.get('input_tokens', 0) if result.success else 0,
            "output_tokens": metrics.get('output_tokens', 0) if result.success else 0,
            "processing_time_seconds": (
                f"{metrics.get('processing_time_seconds', 0):.2f}" 
                if result.success and 'processing_time_seconds' in metrics else "N/A"
            ),
            "output_path": str(output_path) if result.success else ""
        }
        
        results.append(result_data)
        
        # Log the result
        log_message = f"Processed {input_path.name}: "
        if result.success:
            log_message += f"success, size reduction: {result_data['size_reduction_percent']}"
            logger.info(log_message)
        else:
            log_message += f"failed, error: {result.error}"
            logger.error(log_message)
    
    return results


def write_csv_report(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write processing results to a CSV file.
    
    Args:
        results: List of dictionaries with processing results
        output_path: Path to save the CSV file
    """
    fieldnames = [
        "filename", "file_type", "success", "error", 
        "input_size_bytes", "output_size_bytes", "size_reduction_percent",
        "token_reduction_percent", "input_tokens", "output_tokens", 
        "processing_time_seconds", "output_path"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Processing report saved to: {output_path}")


def print_summary(results: List[Dict[str, Any]], output_dir: Path) -> None:
    """
    Print a summary of the processing results.
    
    Args:
        results: List of dictionaries with processing results
        output_dir: Directory where processed files were saved
    """
    successful = sum(1 for r in results if r["success"])
    
    # Calculate average token reduction
    total_reduction = 0
    count = 0
    for r in results:
        if r["success"] and r["token_reduction_percent"] != "N/A":
            try:
                total_reduction += float(r["token_reduction_percent"].strip('%'))
                count += 1
            except (ValueError, AttributeError):
                pass
    
    avg_reduction = total_reduction / count if count > 0 else 0
    
    print(f"\nSummary:")
    print(f"  Processed {len(results)} files")
    print(f"  {successful} successful, {len(results) - successful} failed")
    print(f"  Average token reduction: {avg_reduction:.2f}%")
    print(f"  Processed files saved in: {output_dir}")
    print(f"  Report saved as: {output_dir / 'processing_results.csv'}")


def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    print("TextCleaner Docs Processor")
    print("==========================\n")
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up input and output directories
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
    
    # Verify input directory exists
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Error: Input directory '{input_dir}' does not exist or is not a directory")
        return 1
    
    # Configure extensions if specified
    extensions = None
    if args.extensions:
        extensions = [ext.strip() for ext in args.extensions.split(',')]
        # Ensure each extension starts with a dot
        extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
    
    # Get files to process
    file_paths = get_sample_files(
        input_dir, 
        max_files=args.max_files,
        recursive=args.recursive,
        extensions=extensions
    )
    
    if not file_paths:
        print(f"No supported files found in {input_dir}!")
        return 1
    
    print(f"Found {len(file_paths)} files to process")
    
    # Create processor
    processor = create_processor(args.config)
    
    # Process the files
    results = process_files(
        processor,
        file_paths,
        output_dir,
        use_parallel=args.parallel,
        max_workers=args.workers
    )
    
    # Write report
    report_path = output_dir / "processing_results.csv"
    write_csv_report(results, report_path)
    
    # Print summary
    print_summary(results, output_dir)
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 