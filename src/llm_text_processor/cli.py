"""Command-line interface for the LLM Text Processor."""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Optional

import click

from llm_text_processor import TextProcessor
from llm_text_processor.config.config_manager import ConfigManager
from llm_text_processor.utils.file_utils import get_supported_extensions
from llm_text_processor.utils.logging_config import configure_logging, get_logger


@click.group()
@click.version_option()
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
              case_sensitive=False), default='INFO', help='Set the logging level')
@click.option('--log-file', type=click.Path(), help='Path to log file (if not specified, logs to console only)')
def cli(log_level, log_file):
    """LLM Text Preprocessing Tool.
    
    A versatile script for converting various file formats into clean,
    structured text optimized for Large Language Models (LLMs).
    """
    # Configure logging
    configure_logging(log_level=log_level, log_file=log_file)
    
    # Get logger for CLI
    logger = get_logger(__name__)
    logger.info("Starting LLM Text Processor CLI")


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path(), required=False)
@click.option('--config', '-c', type=click.Path(exists=True),
              help='Path to configuration file')
@click.option('--format', '-f', type=click.Choice(['markdown', 'plain_text', 'json', 'csv']),
              help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def process(
    input_path: str,
    output_path: Optional[str] = None,
    config: Optional[str] = None,
    format: Optional[str] = None,
    verbose: bool = False
):
    """Process a file or directory of files.
    
    INPUT_PATH can be a file or directory.
    If INPUT_PATH is a directory, all supported files within it will be processed.
    
    OUTPUT_PATH is optional. If not provided, processed files will be saved to the
    output directory specified in the configuration (default: 'processed_files').
    """
    # Get logger
    logger = get_logger(__name__)
    logger.info(f"Process command initiated for: {input_path}")
    
    # Initialize processor
    logger.debug(f"Initializing TextProcessor with config: {config}")
    processor = TextProcessor(config_path=config)
    
    # Get input path
    input_path_obj = Path(input_path)
    
    if input_path_obj.is_file():
        # Process a single file
        logger.info(f"Processing single file: {input_path_obj}")
        _process_single_file(processor, input_path_obj, output_path, format, verbose)
    elif input_path_obj.is_dir():
        # Process a directory
        logger.info(f"Processing directory: {input_path_obj}")
        _process_directory(processor, input_path_obj, output_path, format, verbose)
    else:
        error_msg = f"Error: {input_path} is neither a file nor a directory"
        logger.error(error_msg)
        click.echo(error_msg, err=True)
        sys.exit(1)


def _process_single_file(
    processor: TextProcessor,
    input_path: Path,
    output_path: Optional[str],
    format: Optional[str],
    verbose: bool
):
    """Process a single file."""
    # Get logger
    logger = get_logger(__name__)
    
    output_path_obj = Path(output_path) if output_path else None
    logger.debug(f"Output path: {output_path_obj if output_path_obj else 'default'}, Format: {format}")
    
    # Check if the file extension is supported
    extensions = get_supported_extensions()
    if input_path.suffix.lower() not in extensions:
        warning_msg = f"Warning: {input_path.name} has an unsupported extension. Processing may fail."
        logger.warning(warning_msg)
        click.echo(warning_msg)
    
    # Process the file
    click.echo(f"Processing file: {input_path}")
    logger.info(f"Starting processing for file: {input_path}")
    start_time = time.time()
    
    result = processor.process_file(input_path, output_path_obj, format)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.debug(f"Processing completed in {elapsed_time:.2f} seconds")
    
    if result.success:
        success_msg = f"Success: Processed to {result.output_path} ({elapsed_time:.2f}s)"
        logger.info(success_msg)
        click.echo(success_msg)
        
        if verbose:
            logger.debug("Verbose output requested, showing metrics")
            if "token_reduction_percent" in result.metrics:
                metric_msg = f"  - Token reduction: {result.metrics['token_reduction_percent']:.2f}%"
                logger.debug(metric_msg)
                click.echo(metric_msg)
            if "text_length_reduction_percent" in result.metrics:
                metric_msg = f"  - Size reduction: {result.metrics['text_length_reduction_percent']:.2f}%"
                logger.debug(metric_msg)
                click.echo(metric_msg)
    else:
        error_msg = f"Error: {result.error}"
        logger.error(error_msg)
        click.echo(error_msg, err=True)


def _process_directory(
    processor: TextProcessor,
    input_dir: Path,
    output_dir: Optional[str],
    format: Optional[str],
    verbose: bool
):
    """Process a directory of files."""
    # Get logger
    logger = get_logger(__name__)
    
    output_dir_obj = Path(output_dir) if output_dir else None
    logger.debug(f"Output directory: {output_dir_obj if output_dir_obj else 'default'}, Format: {format}")
    
    # Process the directory
    click.echo(f"Processing directory: {input_dir}")
    click.echo("This may take some time depending on the number and size of files...")
    
    logger.info(f"Starting processing for directory: {input_dir}")
    start_time = time.time()
    
    results = processor.process_directory(input_dir, output_dir_obj, format)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.debug(f"Directory processing completed in {elapsed_time:.2f} seconds")
    
    # Count successful and failed files
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    
    # Print summary
    summary_msg = f"\nProcessing complete: {successful} successful, {failed} failed ({elapsed_time:.2f}s)"
    logger.info(summary_msg)
    click.echo(summary_msg)
    
    if failed > 0:
        logger.warning(f"{failed} files failed processing")
        if verbose:
            click.echo("\nFailed files:")
            for result in results:
                if not result.success:
                    error_msg = f"  - {result.input_path.name}: {result.error}"
                    logger.debug(error_msg)
                    click.echo(error_msg)
    
    if successful > 0:
        output_dir_name = output_dir_obj if output_dir_obj else processor.config.get("general.output_dir", "processed_files")
        output_msg = f"\nProcessed files are in: {output_dir_name}"
        logger.info(output_msg)
        click.echo(output_msg)


@cli.command()
@click.option('--output', '-o', type=click.Path(), 
              help='Output path for the generated config file',
              default='llm_processor_config.yaml')
@click.option('--level', '-l', 
              type=click.Choice(['minimal', 'standard', 'aggressive']),
              default='standard',
              help='Cleaning level for the configuration')
def generate_config(output: str, level: str):
    """Generate a configuration file with the specified cleaning level."""
    # Create default config
    config = ConfigManager()
    
    # Adjust config based on cleaning level
    config.config["processing"]["cleaning_level"] = level
    
    if level == "minimal":
        # Minimal cleaning preserves most structure
        config.config["structure"]["preserve_headings"] = True
        config.config["structure"]["preserve_lists"] = True
        config.config["structure"]["preserve_tables"] = True
        config.config["structure"]["preserve_links"] = True
        
        config.config["cleaning"]["remove_headers_footers"] = False
        config.config["cleaning"]["remove_watermarks"] = False
        config.config["cleaning"]["clean_whitespace"] = True
        
        config.config["optimization"]["abbreviate_common_terms"] = False
        config.config["optimization"]["simplify_citations"] = False
        config.config["optimization"]["simplify_references"] = False
        
    elif level == "aggressive":
        # Aggressive cleaning maximizes token efficiency
        config.config["structure"]["preserve_headings"] = True
        config.config["structure"]["preserve_lists"] = True
        config.config["structure"]["preserve_tables"] = False
        config.config["structure"]["preserve_links"] = False
        
        config.config["cleaning"]["remove_headers_footers"] = True
        config.config["cleaning"]["remove_watermarks"] = True
        config.config["cleaning"]["remove_boilerplate"] = True
        config.config["cleaning"]["remove_duplicate_content"] = True
        
        config.config["optimization"]["abbreviate_common_terms"] = True
        config.config["optimization"]["simplify_citations"] = True
        config.config["optimization"]["simplify_references"] = True
        config.config["optimization"]["simplify_urls"] = True
    
    # Save the config
    config.save_to_file(output)
    click.echo(f"Configuration file with {level} cleaning level saved to: {output}")


@cli.command()
def list_formats():
    """List all supported file formats."""
    extensions = sorted(get_supported_extensions())
    
    # Group extensions by type
    groups = {
        "Documents": [".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md"],
        "Spreadsheets": [".xls", ".xlsx", ".ods", ".csv"],
        "Presentations": [".ppt", ".pptx", ".odp"],
        "Web/Data": [".html", ".htm", ".xml", ".json"],
    }
    
    click.echo("Supported File Formats:")
    
    for group_name, group_exts in groups.items():
        click.echo(f"\n{group_name}:")
        for ext in group_exts:
            if ext in extensions:
                click.echo(f"  - {ext}")
                extensions.remove(ext)
    
    # Print any remaining extensions
    if extensions:
        click.echo("\nOther:")
        for ext in extensions:
            click.echo(f"  - {ext}")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
