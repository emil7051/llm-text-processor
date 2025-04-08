"""Command-line interface commands for the Text Cleaner."""

import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

import click

from textcleaner import TextProcessor, ProcessingResult
from textcleaner.core.factories import TextProcessorFactory
from textcleaner.config.config_factory import ConfigFactory
from textcleaner.core.file_registry import FileTypeRegistry
from textcleaner.utils.file_utils import get_supported_extensions
from textcleaner.utils.logging_config import configure_logging, get_logger
from textcleaner.utils.log_utils import ProcessingLogger


@click.group()
@click.version_option()
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
              case_sensitive=False), default='INFO', help='Set the logging level')
@click.option('--log-file', type=click.Path(), help='Path to log file (if not specified, logs to console only)')
def cli(log_level, log_file):
    """Text Cleaner Tool.
    
    A versatile tool for converting various file formats into clean,
    structured text optimized for Large Language Models (LLMs).
    """
    # Configure logging
    configure_logging(log_level=log_level, log_file=log_file)
    logger = get_logger(__name__)
    logger.info("Starting Text Cleaner CLI")


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path(), required=False)
@click.option('--config', '-c', type=click.Path(exists=True),
              help='Path to configuration file')
@click.option('--format', '-f', type=click.Choice(['markdown', 'plain_text', 'json', 'csv']),
              help='Output format')
@click.option('--config-type', '-t', type=click.Choice(['minimal', 'standard', 'aggressive']),
              default='standard', help='Configuration type to use if no config file provided')
@click.option('--recursive', '-r', is_flag=True, default=True,
              help='Process directories recursively (default: True)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def process(
    input_path: str,
    output_path: Optional[str] = None,
    config: Optional[str] = None,
    format: Optional[str] = None,
    config_type: str = 'standard',
    recursive: bool = True,
    verbose: bool = False
):
    """Process a file or directory of files.
    
    INPUT_PATH can be a file or directory.
    If INPUT_PATH is a directory, all supported files within it will be processed.
    
    OUTPUT_PATH is optional. If not provided, processed files will be saved to the
    output directory specified in the configuration (default: 'processed_files').
    """
    logger = get_logger(__name__)
    processing_logger = ProcessingLogger(__name__)
    logger.info(f"Process command initiated for: {input_path}")
    
    # Log configuration information
    if config:
        logger.info(f"Using configuration file: {config}")
    else:
        logger.info(f"Using {config_type} configuration preset")
    
    if verbose:
        logger.info("Verbose output enabled")
    
    # Initialize processor using factory
    factory = TextProcessorFactory()
    processor = factory.create_processor(config_path=config, config_type=config_type)
    
    # Get input path
    input_path_obj = Path(input_path)
    
    if input_path_obj.is_file():
        # Process a single file
        _process_single_file(processor, input_path_obj, output_path, format, verbose)
    elif input_path_obj.is_dir():
        # Process a directory
        _process_directory(processor, input_path_obj, output_path, format, recursive, verbose)
    else:
        error_msg = f"Error: {input_path} is neither a file nor a directory"
        logger.error(error_msg)
        click.echo(error_msg, err=True)
        sys.exit(1)


def _process_single_file(
    processor: TextProcessor,
    input_path: Path,
    output_path: Optional[str],
    output_format: Optional[str],
    verbose: bool
):
    """Process a single file."""
    logger = get_logger(__name__)
    
    output_path_obj = Path(output_path) if output_path else None
    
    # Check if the file extension is supported
    extensions = get_supported_extensions()
    if input_path.suffix.lower() not in extensions:
        warning_msg = f"Warning: {input_path.name} has an unsupported extension. Processing may fail."
        logger.warning(warning_msg)
        click.echo(warning_msg)
    
    # Process the file
    click.echo(f"Processing file: {input_path}")
    start_time = time.time()
    
    try:
        result = processor.process_file(input_path, output_path_obj, output_format)
        
        if result.success:
            processing_time = time.time() - start_time
            success_msg = f"Successfully processed {input_path.name} in {processing_time:.2f}s"
            
            if verbose:
                # Add metrics in verbose mode
                token_reduction = result.metrics.get("token_reduction_percent", 0)
                success_msg += f" (Token reduction: {token_reduction:.1f}%)"
                
            logger.info(success_msg)
            click.echo(success_msg)
            
            # Show output location
            output_location = f"Output saved to: {result.output_path}"
            logger.info(output_location)
            click.echo(output_location)
        else:
            error_msg = f"Failed to process {input_path.name}: {result.error}"
            logger.error(error_msg)
            click.echo(error_msg, err=True)
            
    except Exception as e:
        error_msg = f"Error processing {input_path.name}: {str(e)}"
        logger.exception(error_msg)
        click.echo(error_msg, err=True)


def _process_directory(
    processor: TextProcessor,
    input_dir: Path,
    output_dir: Optional[str],
    output_format: Optional[str],
    recursive: bool,
    verbose: bool
):
    """Process a directory of files."""
    logger = get_logger(__name__)
    
    # Set output directory
    output_dir_obj = Path(output_dir) if output_dir else None
    
    # Process directory
    click.echo(f"Processing directory: {input_dir}")
    if recursive:
        click.echo("Processing recursively...")
    
    start_time = time.time()
    
    try:
        results = processor.process_directory(
            input_dir, output_dir_obj, output_format, recursive
        )
        
        # Summarize results
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        
        processing_time = time.time() - start_time
        summary_msg = f"\nProcessed {total} files in {processing_time:.2f}s: {successful} successful, {failed} failed"
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
            
    except Exception as e:
        error_msg = f"Error processing directory {input_dir}: {str(e)}"
        logger.exception(error_msg)
        click.echo(error_msg, err=True)


@cli.command()
@click.option('--output', '-o', type=click.Path(), 
              help='Output path for the generated config file',
              default='textcleaner_config.yaml')
@click.option('--level', '-l', 
              type=click.Choice(['minimal', 'standard', 'aggressive']),
              default='standard',
              help='Cleaning level for the configuration')
@click.option('--custom-options', '-c', type=str, multiple=True,
              help='Custom configuration options in format key=value')
def generate_config(output: str, level: str, custom_options: List[str]):
    """Generate a configuration file with the specified cleaning level."""
    logger = get_logger(__name__)
    logger.info(f"Generating {level} configuration file at {output}")
    
    # Create config factory
    config_factory = ConfigFactory()
    
    # Parse any custom options
    custom_overrides = {}
    if custom_options:
        for option in custom_options:
            if '=' in option:
                key, value = option.split('=', 1)
                # Convert string values to appropriate types
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)
                custom_overrides[key] = value
        logger.debug(f"Custom overrides: {custom_overrides}")
    
    # Create config using factory
    config = config_factory.create_custom_config(level, custom_overrides or None)
    
    # Save the config
    config_factory.save_config(config, output)
    
    # Inform the user
    click.echo(f"Configuration file with {level} cleaning level saved to: {output}")
    if custom_overrides:
        click.echo(f"Applied {len(custom_overrides)} custom overrides")
    
    logger.info(f"Generated {level} configuration file at {output}")


@cli.command()
def list_formats():
    """List all supported file formats."""
    logger = get_logger(__name__)
    logger.info("Listing supported file formats")
    
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
