"""Command-line interface commands for the Text Cleaner."""

import os
import sys
import time
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

import click
from tqdm import tqdm

from textcleaner import TextProcessor, ProcessingResult, __version__
from textcleaner.core.factories import TextProcessorFactory
from textcleaner.config.config_factory import ConfigFactory
from textcleaner.config.presets import get_preset_names, get_preset_description, get_preset
from textcleaner.core.file_registry import FileTypeRegistry
from textcleaner.utils.file_utils import get_supported_extensions
from textcleaner.utils.logging_config import configure_logging, get_logger
from textcleaner.utils.log_utils import ProcessingLogger
from textcleaner.utils.security import validate_path, sanitize_filename, SecurityUtils
from textcleaner.core.directory_processor import DirectoryProcessor
from textcleaner.utils.parallel import ParallelProcessor

# Constants
DEFAULT_CONFIG_TYPE = "standard"
TOKEN_STAT_FORMAT = "{:,}"
OUTPUT_FORMATS = ['markdown', 'plain_text', 'json', 'csv']
# Use the presets from the config module
LLM_PRESETS = get_preset_names()

# Remove global security validator - will be obtained from factory
# security_validator = SecurityUtils()


@click.group()
@click.version_option(version=__version__)
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
              case_sensitive=False), help='Set the logging level explicitly (overrides verbosity flags)')
@click.option('--log-file', type=click.Path(), help='Path to log file (if not specified, logs to console only)')
@click.option('--verbose', '-v', count=True, help='Increase verbosity level (-v for INFO, -vv for DEBUG)')
@click.option('--quiet', '-q', is_flag=True, help='Suppress console output (logs still written if --log-file specified)')
def cli(log_level, log_file, verbose, quiet):
    """Text Cleaner Tool.
    
    A versatile tool for converting various file formats into clean,
    structured text optimized for Large Language Models (LLMs).
    """
    # Determine effective log level
    if log_level: # Explicit level overrides everything
        effective_log_level = log_level.upper()
    elif quiet:
        effective_log_level = 'ERROR'
    elif verbose == 1:
        effective_log_level = 'INFO'
    elif verbose >= 2:
        effective_log_level = 'DEBUG'
    else: # Default if no flags
        effective_log_level = 'WARNING'

    # Configure logging
    configure_logging(log_level=effective_log_level, log_file=log_file)
    logger = get_logger(__name__)
    logger.info(f"Starting Text Cleaner CLI v{__version__}")
    logger.debug(f"Effective log level set to: {effective_log_level}")
    logger.debug(f"Quiet mode: {quiet}")
    logger.debug(f"Log file: {log_file}")

# Get factory instance early for shared components
_factory = TextProcessorFactory()

def _validate_and_prepare_paths(input_path: str, output_path: Optional[str]) -> tuple[Path, Optional[Path]]:
    """Validates input path and prepares output path object."""
    logger = get_logger(__name__)
    # Get security utils from the factory
    security_utils = _factory._get_security_utils() # Access private method for now
    
    is_valid, error = security_utils.validate_path(Path(input_path)) 
    if not is_valid:
        # Log specific error details
        error_msg = f"Invalid input path '{input_path}': {error}"
        logger.error(error_msg)
        click.echo(error_msg, err=True)
        sys.exit(1)
    # If valid, convert to Path object
    input_path_obj = Path(input_path)

    output_path_obj = None
    if output_path:
        # Validate output path using the security instance
        is_valid, error = security_utils.validate_output_path(Path(output_path))
        if not is_valid:
            error_msg = f"Invalid output path '{output_path}': {error}"
            logger.error(error_msg)
            click.echo(error_msg, err=True)
            sys.exit(1)
        output_path_obj = Path(output_path)
        
        # Ensure directory exists for output if it doesn't look like a file path
        if not output_path_obj.exists() and output_path_obj.suffix == '':
            logger.debug(f"Creating output directory: {output_path_obj}")
            try:
                output_path_obj.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                 error_msg = f"Error creating output directory '{output_path_obj}': {str(e)}"
                 logger.error(error_msg)
                 click.echo(error_msg, err=True)
                 sys.exit(1)
            
    return input_path_obj, output_path_obj


# Helper function for processor initialization
def _initialize_processor(
    config: Optional[str],
    config_type: str,
    preset: Optional[str],
    quiet_mode: bool
) -> TextProcessor:
    """Initializes the TextProcessor based on configuration and presets."""
    logger = get_logger(__name__)
    
    # Log configuration information
    if config:
        logger.info(f"Using configuration file: {config}")
    else:
        logger.info(f"Using {config_type} configuration preset")

    # Apply preset if specified
    custom_overrides = {}
    if preset:
        logger.info(f"Using LLM preset: {preset}")
        if not quiet_mode:
            try:
                preset_desc = get_preset_description(preset)
                click.echo(f"Using {preset} preset: {preset_desc}")
                custom_overrides = get_preset(preset)
                token_limit = custom_overrides.get("token_limit", "unlimited")
                if token_limit:
                    click.echo(f"Target token limit: {token_limit:,}")
            except ValueError as e:
                logger.error(f"Error loading preset: {e}")
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)
    
    # Initialize processor using factory
    # factory = TextProcessorFactory() # Use the global factory instance
    try:
        processor = _factory.create_processor(
            config_path=config, 
            config_type=config_type,
            custom_overrides=custom_overrides
        )
        return processor
    except Exception as e:
        error_msg = f"Failed to initialize TextProcessor: {e}"
        logger.exception(error_msg) # Log with traceback
        click.echo(f"Error: {error_msg}", err=True)
        sys.exit(1)


def _process_directory(
    processor: TextProcessor,
    input_dir: Path,
    output_dir: Optional[Path],
    output_format: Optional[str],
    recursive: bool,
    # TODO: Expose these as CLI options if needed
    use_parallel: bool = True, 
    max_workers: Optional[int] = None,
    file_extensions: Optional[List[str]] = None
):
    """Processes all supported files within a directory."""
    logger = get_logger(__name__)
    logger.info(f"Processing directory: {input_dir}")

    # Instantiate components needed for directory processing
    # These might be better managed by a factory or dependency injection in a larger app
    # security_utils = SecurityUtils() # Get from factory
    parallel_processor = _factory.create_parallel_processor(max_workers=max_workers) 
    
    # Use factory to create the DirectoryProcessor
    directory_processor = _factory.create_directory_processor(
        config_manager=processor.config, # Pass config from the file processor
        # security_utils=security_utils, # Handled by factory
        parallel_processor=parallel_processor,
        single_file_processor=processor # Reuse the already configured processor
    )

    try:
        if use_parallel:
             logger.debug(f"Starting parallel processing for {input_dir}")
             directory_processor.process_directory_parallel(
                 input_dir=input_dir,
                 output_dir=output_dir,
                 output_format=output_format,
                 recursive=recursive,
                 file_extensions=file_extensions, 
                 # max_workers is handled by ParallelProcessor instance now
             )
        else:
             logger.debug(f"Starting sequential processing for {input_dir}")
             directory_processor.process_directory(
                 input_dir=input_dir,
                 output_dir=output_dir,
                 output_format=output_format,
                 recursive=recursive,
                 file_extensions=file_extensions 
             )
        logger.info(f"Finished processing directory: {input_dir}")
    except Exception as e:
        # Catch potential errors during directory processing
        error_msg = f"Error processing directory {input_dir}: {str(e)}"
        logger.exception(error_msg) # Log with traceback
        click.echo(f"Error: {error_msg}", err=True)
        # Decide if we should exit or continue if possible
        # For now, exiting on directory-level errors
        sys.exit(1) 


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path(), required=False)
@click.option('--config', '-c', type=click.Path(exists=True),
              help='Path to configuration file')
@click.option('--format', '-f', type=click.Choice(OUTPUT_FORMATS),
              help='Output format (markdown is best for LLMs, plain_text for simplicity)')
@click.option('--config-type', '-t', type=click.Choice(['minimal', 'standard', 'aggressive']),
              default=DEFAULT_CONFIG_TYPE, 
              help=f'Configuration type to use if no config file provided (default: {DEFAULT_CONFIG_TYPE})')
@click.option('--preset', '-p', type=click.Choice(LLM_PRESETS),
              help='Use a predefined LLM preset (overrides --config-type)')
@click.option('--recursive', '-r', is_flag=True, default=True,
              help='Process directories recursively (default: True)')
@click.option('--no-progress', is_flag=True, help='Disable progress bar')
def process(
    input_path: str,
    output_path: Optional[str] = None,
    config: Optional[str] = None,
    format: Optional[str] = None,
    config_type: str = DEFAULT_CONFIG_TYPE,
    preset: Optional[str] = None,
    recursive: bool = True,
    no_progress: bool = False
):
    """Process a file or directory of files.
    
    INPUT_PATH can be a file or directory.
    If INPUT_PATH is a directory, all supported files within it will be processed.
    
    OUTPUT_PATH is optional. If not provided, processed files will be saved to the
    output directory specified in the configuration (default: 'processed_files').
    
    LLM Presets:
      --preset=gpt4     Optimized for GPT-4 with 8K token context
      --preset=claude   Optimized for Claude with 100K token context
      --preset=llama    Aggressive optimization for 4K token models
      --preset=chatgpt  Optimized for ChatGPT with 4K token context
      --preset=rag      Designed for RAG/embedding vector database ingestion
      --preset=minimal  Very light processing, preserves most content
    
    Examples:
      tc process document.pdf
      tc process documents/ --format markdown
      tc process large_file.txt --preset claude
    """
    logger = get_logger(__name__)
    logger.info(f"Process command initiated for: {input_path}")
    
    # Retrieve verbosity and quiet status from context
    ctx = click.get_current_context()
    verbose_count = ctx.parent.params.get('verbose', 0)
    quiet_mode = ctx.parent.params.get('quiet', False)
    
    # Log verbosity if needed
    if verbose_count > 0 and not quiet_mode:
        click.echo(f"Verbose level: {verbose_count}")
        
    # Validate paths and prepare output path object
    input_path_obj, output_path_obj = _validate_and_prepare_paths(input_path, output_path)
    
    # Initialize the processor
    processor = _initialize_processor(
        config=config,
        config_type=config_type,
        preset=preset,
        quiet_mode=quiet_mode
    )

    # Decide how to process based on input type
    if input_path_obj.is_file():
        _process_single_file(
            processor=processor,
            input_path=input_path_obj,
            output_path=output_path_obj,
            output_format=format,
            verbose_count=verbose_count,
            quiet_mode=quiet_mode
        )
    elif input_path_obj.is_dir():
        # TODO: Add CLI option for parallel vs sequential?
        use_parallel_processing = True # Default to parallel for now
        _process_directory(
            processor=processor,
            input_dir=input_path_obj,
            output_dir=output_path_obj,
            output_format=format,
            recursive=recursive,
            use_parallel=use_parallel_processing
            # Pass other relevant params like max_workers if added as CLI options
        )
    else:
        # This case should technically be caught by validate_path, but safety first
        error_msg = f"Error: Input path '{input_path}' is neither a file nor a directory."
        logger.error(error_msg)
        click.echo(error_msg, err=True)
        sys.exit(1)


def _process_single_file(
    processor: TextProcessor,
    input_path: Path,
    output_path: Optional[Path],
    output_format: Optional[str],
    verbose_count: int,
    quiet_mode: bool
):
    """Process a single file."""
    logger = get_logger(__name__)
    
    # output_path_obj = output_path if output_path else None # Redundant, output_path is already Optional[Path]
    
    # Check if the file extension is supported
    extensions = get_supported_extensions()
    if input_path.suffix.lower() not in extensions:
        warning_msg = f"Warning: '{input_path.name}' has an unsupported extension ('{input_path.suffix}'). Processing may fail or yield unexpected results."
        logger.warning(warning_msg)
        if not quiet_mode:
            click.echo(warning_msg)
    
    # Process the file
    if not quiet_mode:
        click.echo(f"Processing file: {input_path}")
    start_time = time.time()
    
    try:
        result = processor.process_file(input_path, output_path, output_format)
        processing_time = time.time() - start_time
        
        if result.success:
            # Base success message (always shown unless quiet)
            base_success_msg = f"Successfully processed '{input_path.name}' in {processing_time:.2f}s"
            
            if not quiet_mode:
                # Default output includes token reduction % if available
                token_reduction = result.metrics.get("token_reduction_percent")
                if token_reduction is not None:
                    success_msg = f"{base_success_msg} (Token reduction: {token_reduction:.1f}%)"
                else:
                    success_msg = base_success_msg
                click.echo(success_msg)
            else:
                # Log basic success even in quiet mode
                logger.info(base_success_msg)

            # Output path message (always shown unless quiet, always logged)
            if result.output_path:
                output_location = f"Output saved to: {result.output_path}"
                logger.info(output_location)
                if not quiet_mode:
                    click.echo(output_location)
            else:
                logger.warning(f"No output path returned for {input_path.name}")
                
            # Verbose output (-v) - Add size reduction and stages
            if verbose_count == 1 and not quiet_mode:
                size_reduction = result.metrics.get("size_reduction_percent")
                stages = result.metrics.get("processing_stages", [])
                if size_reduction is not None:
                    click.echo(f"  Size reduction:   {size_reduction:.1f}%")
                if stages:
                     click.echo(f"  Processing steps: {', '.join(stages)}")

            # Debug output (-vv) - Log detailed metrics
            # Note: _log_detailed_metrics already uses logger.debug
            if verbose_count >= 2:
                _log_detailed_metrics(result, logger)
                
            # Always display token stats unless quiet
            if not quiet_mode:
                _display_token_statistics(
                    result.metrics, 
                    processing_time, 
                    output_format=output_format,
                    verbose=(verbose_count > 0) # Pass verbosity to potentially show more stats
                )
        else:
            # Handle specific processing failures reported by TextProcessor
            error_msg = f"Failed to process '{input_path.name}': {result.error}"
            logger.error(error_msg)
            click.echo(error_msg, err=True)
            
    except (IOError, OSError) as e:
        error_msg = f"File system error processing '{input_path.name}': {str(e)}"
        logger.error(error_msg) # Log only the error message for FS errors
        click.echo(error_msg, err=True)
    except RuntimeError as e:
        # Catch specific runtime errors (e.g., from TextProcessor internal logic)
        error_msg = f"Processing error for '{input_path.name}': {str(e)}"
        logger.error(error_msg) # Log only the error message
        click.echo(error_msg, err=True)
    except Exception as e:
        # Catch any other unexpected error during processing
        error_msg = f"Unexpected error processing '{input_path.name}': {str(e)}"
        logger.exception(error_msg) # Log with traceback for unexpected errors
        click.echo(error_msg, err=True)


def _log_detailed_metrics(result: ProcessingResult, logger):
    """Log detailed metrics for processed file."""
    metrics = result.metrics
    # Ensure input_path is available and has a name attribute
    input_name = result.input_path.name if hasattr(result.input_path, 'name') else str(result.input_path)
    logger.debug(f"--- Detailed Metrics for {input_name} ---") # Header for clarity
    logger.debug(f"Original size (bytes): {metrics.get('original_size_bytes', 'N/A')}")
    logger.debug(f"Processed size (bytes): {metrics.get('processed_size_bytes', 'N/A')}")
    logger.debug(f"Size reduction: {metrics.get('size_reduction_percent', 'N/A'):.1f}%") # Ensure float format
    logger.debug(f"Removed whitespace: {metrics.get('whitespace_removed', 'N/A')} chars")
    logger.debug(f"Removed duplicates: {metrics.get('duplicates_removed', 'N/A')} lines")
    logger.debug(f"Processing stages: {', '.join(metrics.get('processing_stages', ['N/A']))}") # Handle empty list
    logger.debug(f"Original Tokens: {metrics.get('original_token_estimate', 'N/A')}")
    logger.debug(f"Processed Tokens: {metrics.get('processed_token_estimate', 'N/A')}")
    logger.debug(f"Token Reduction: {metrics.get('token_reduction_percent', 'N/A'):.1f}%") # Ensure float format
    logger.debug("--- End Detailed Metrics ---")


def _display_token_statistics(
    metrics: Dict[str, Any], 
    processing_time: float,
    output_format: Optional[str] = None,
    verbose: bool = False # Added verbose flag
) -> None:
    """Display token statistics in a consistent format."""
    original_tokens = metrics.get("original_token_estimate")
    processed_tokens = metrics.get("processed_token_estimate")
    token_reduction = metrics.get("token_reduction_percent")
    size_reduction = metrics.get("size_reduction_percent") # Get size reduction
    
    # Format output based on requested format
    if output_format == "json":
        stats = {
            "processing_time_seconds": round(processing_time, 2), # Round for consistency
        }
        # Include available metrics consistently
        if original_tokens is not None: stats["original_tokens"] = original_tokens
        if processed_tokens is not None: stats["processed_tokens"] = processed_tokens
        if token_reduction is not None: stats["token_reduction_percent"] = round(token_reduction, 2)
        if size_reduction is not None: stats["size_reduction_percent"] = round(size_reduction, 2)
        
        # Add other metrics present in the dictionary, excluding those already handled
        handled_keys = {
            "original_token_estimate", "processed_token_estimate", 
            "token_reduction_percent", "size_reduction_percent"
        }
        stats.update({k: v for k, v in metrics.items() if k not in handled_keys})
        
        click.echo(json.dumps(stats, indent=2))
    else:
        click.echo(f"\nProcessing Summary:")
        if original_tokens is not None:
            click.echo(f"  Original tokens:  {original_tokens:,}")
        if processed_tokens is not None:
            click.echo(f"  Processed tokens: {processed_tokens:,}")
        if token_reduction is not None:
            click.echo(f"  Token reduction:  {token_reduction:.1f}%")
        # Show size reduction in non-JSON verbose mode as well
        if verbose and size_reduction is not None:
             click.echo(f"  Size reduction:   {size_reduction:.1f}%")
            
        click.echo(f"  Processing time:  {processing_time:.2f}s")


def _parse_custom_options(custom_options: List[str]) -> Dict[str, Any]:
    """Parses custom options from key=value strings into a dictionary."""
    logger = get_logger(__name__)
    parsed_options = {}
    for option in custom_options:
        try:
            key, value = option.split('=', 1)
            # Attempt to convert value to appropriate type (int, float, bool, str)
            # This is a basic attempt; more complex structures might need YAML parsing
            if value.lower() == 'true':
                parsed_value = True
            elif value.lower() == 'false':
                parsed_value = False
            else:
                try:
                    parsed_value = int(value)
                except ValueError:
                    try:
                        parsed_value = float(value)
                    except ValueError:
                        parsed_value = value # Keep as string if not number or bool
            
            # Handle nested keys (e.g., chunking.chunk_size)
            keys = key.strip().split('.')
            d = parsed_options
            for k in keys[:-1]:
                d = d.setdefault(k, {})
            d[keys[-1]] = parsed_value
            logger.debug(f"Parsed custom option: {key} = {parsed_value} (type: {type(parsed_value)})")
        except ValueError:
            warning_msg = f"Skipping invalid custom option format: '{option}'. Use key=value."
            logger.warning(warning_msg)
            click.echo(f"Warning: {warning_msg}")
        except Exception as e:
            warning_msg = f"Error parsing custom option '{option}': {e}"
            logger.warning(warning_msg)
            click.echo(f"Warning: {warning_msg}")
            
    return parsed_options


@cli.command()
@click.option('--output', '-o', type=click.Path(), 
              help='Output path for the generated config file',
              default='textcleaner_config.yaml')
@click.option('--level', '-l', 
              type=click.Choice(['minimal', 'standard', 'aggressive']),
              default='standard',
              help='Cleaning level for the configuration')
@click.option('--preset', '-p', type=click.Choice(LLM_PRESETS),
              help='Use a predefined LLM configuration preset')
@click.option('--custom-options', '-c', type=str, multiple=True,
              help='Custom configuration options in format key=value (e.g., chunking.chunk_size=1000)')
def generate_config(
    output: str,
    level: str,
    preset: Optional[str],
    custom_options: List[str]
):
    """Generate a configuration file with the specified cleaning level.
    
    Examples:
      tc generate-config -o my_config.yaml --level aggressive
      tc generate-config --preset gpt4
      tc generate-config -c chunking.chunk_size=500 -c metadata.enabled=false
    """
    logger = get_logger(__name__)
    factory = ConfigFactory()
    
    # Parse custom options
    parsed_custom_options = _parse_custom_options(custom_options)
    
    try:
        # If a preset is given, use it as the base, otherwise use the level
        if preset:
            logger.info(f"Generating config based on preset: {preset}")
            config_dict = factory.generate_config_from_preset(preset, overrides=parsed_custom_options)
            if not parsed_custom_options:
                 click.echo(f"Generated configuration based on '{preset}' preset.")
            else:
                click.echo(f"Generated configuration based on '{preset}' preset with custom overrides.")
        else:
            logger.info(f"Generating config based on level: {level}")
            config_dict = factory.generate_config(level, overrides=parsed_custom_options)
            if not parsed_custom_options:
                click.echo(f"Generated '{level}' configuration.")
            else:
                 click.echo(f"Generated '{level}' configuration with custom overrides.")

        # Save the configuration
        output_path = Path(output)
        factory.save_config(config_dict, output_path)
        logger.info(f"Configuration saved to: {output_path}")
        click.echo(f"Configuration file saved to: {output_path}")
        
    except ValueError as e:
        error_msg = f"Error generating configuration: {e}"
        logger.error(error_msg)
        click.echo(f"Error: {error_msg}", err=True)
        sys.exit(1)
    except IOError as e:
        error_msg = f"Error saving configuration file to '{output}': {e}"
        logger.error(error_msg)
        click.echo(f"Error: {error_msg}", err=True)
        sys.exit(1)
    except Exception as e:
        error_msg = f"An unexpected error occurred during config generation: {e}"
        logger.exception(error_msg)
        click.echo(f"Error: {error_msg}", err=True)
        sys.exit(1)


@cli.command(name="list-presets")
@click.option('--format', '-f', type=click.Choice(['table', 'json']),
              default='table', help='Output format for the list')
def list_presets(format: str):
    """List available LLM presets and their descriptions.
    
    Examples:
      tc list-presets
      tc list-presets --format json
    """
    presets_data = [
        {
            "name": name,
            "description": get_preset_description(name),
            # Consider adding key details like token limit here if useful
            # "token_limit": get_preset(name).get("token_limit", "N/A") 
        }
        for name in get_preset_names()
    ]

    if format == 'json':
        click.echo(json.dumps(presets_data, indent=2))
    else: # Default to table
        # Simple table formatting using f-strings
        max_name_len = max(len(p['name']) for p in presets_data) if presets_data else 10
        click.echo(f"Available LLM Presets:")
        click.echo(f"{'Name':<{max_name_len}}   Description")
        click.echo(f"{'-'*max_name_len}   {'-'*30}")
        for preset in presets_data:
            click.echo(f"{preset['name']:<{max_name_len}}   {preset['description']}")


@cli.command()
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'plain']),
              default='table', help='Output format for the list')
def list_formats(format: str):
    """List all supported file formats.
    
    Examples:
      tc list-formats
      tc list-formats --format json
    """
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
    
    # Filter extensions by what's actually supported
    filtered_groups = {}
    ungrouped = []
    
    for group_name, group_exts in groups.items():
        filtered_exts = [ext for ext in group_exts if ext in extensions]
        if filtered_exts:
            filtered_groups[group_name] = filtered_exts
            for ext in filtered_exts:
                if ext in extensions:
                    extensions.remove(ext)
    
    # Any remaining extensions
    if extensions:
        ungrouped = extensions
    
    if format == 'json':
        # Output as JSON
        result = {
            "grouped": filtered_groups,
            "other": ungrouped
        }
        click.echo(json.dumps(result, indent=2))
    elif format == 'plain':
        # Simple plain text output
        click.echo("Supported file formats:")
        for ext in sorted(get_supported_extensions()):
            click.echo(ext)
    else:
        # Default table format
        click.echo("Supported File Formats:")
        
        for group_name, group_exts in filtered_groups.items():
            click.echo(f"\n{group_name}:")
            for ext in group_exts:
                click.echo(f"  - {ext}")
        
        # Print any remaining extensions
        if ungrouped:
            click.echo("\nOther:")
            for ext in ungrouped:
                click.echo(f"  - {ext}")


@cli.command(name="version")
def show_version():
    """Show detailed version information."""
    import platform
    import sys
    
    click.echo(f"TextCleaner version: {__version__}")
    click.echo(f"Python version: {platform.python_version()}")
    click.echo(f"Platform: {platform.platform()}")
    
    # Try to get dependency versions
    try:
        import pypdf
        click.echo(f"PyPDF version: {pypdf.__version__}")
    except (ImportError, AttributeError):
        pass
    
    try:
        import nltk
        click.echo(f"NLTK version: {nltk.__version__}")
    except (ImportError, AttributeError):
        pass


# Entry point function
def main():
    """Entry point for the CLI."""
    cli()

if __name__ == "__main__":
    main()
