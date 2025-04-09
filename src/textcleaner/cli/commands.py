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
    effective_log_level = 'WARNING' # Default if not verbose or quiet
    if quiet:
        effective_log_level = 'ERROR' # Suppress INFO/WARNING on console
    elif verbose == 1:
        effective_log_level = 'INFO'
    elif verbose >= 2:
        effective_log_level = 'DEBUG'
        
    # Explicit log level overrides verbosity
    if log_level:
        effective_log_level = log_level
        
    # Configure logging
    configure_logging(log_level=effective_log_level, log_file=log_file, quiet=quiet)
    logger = get_logger(__name__)
    logger.info(f"Starting Text Cleaner CLI v{__version__}")
    logger.debug(f"Effective log level set to: {effective_log_level}")
    logger.debug(f"Quiet mode: {quiet}")
    logger.debug(f"Log file: {log_file}")


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
    processing_logger = ProcessingLogger(__name__)
    logger.info(f"Process command initiated for: {input_path}")
    
    # Retrieve verbosity and quiet status from context
    ctx = click.get_current_context()
    verbose_count = ctx.parent.params.get('verbose', 0)
    quiet_mode = ctx.parent.params.get('quiet', False)
    
    # Log configuration information
    if config:
        logger.info(f"Using configuration file: {config}")
    else:
        logger.info(f"Using {config_type} configuration preset")
    
    if preset:
        logger.info(f"Using LLM preset: {preset}")
        if not quiet_mode:
            preset_desc = get_preset_description(preset)
            click.echo(f"Using {preset} preset: {preset_desc}")
    
    if verbose_count > 0 and not quiet_mode:
        click.echo(f"Verbose level: {verbose_count}")
    
    # Initialize processor using factory
    factory = TextProcessorFactory()
    
    # Apply preset if specified
    custom_overrides = {}
    if preset:
        try:
            custom_overrides = get_preset(preset)
            if not quiet_mode:
                token_limit = custom_overrides.get("token_limit", "unlimited")
                if token_limit:
                    click.echo(f"Target token limit: {token_limit:,}")
        except ValueError as e:
            logger.error(f"Error loading preset: {e}")
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    
    processor = factory.create_processor(
        config_path=config, 
        config_type=config_type,
        custom_overrides=custom_overrides
    )
    
    # Get input path and validate
    try:
        input_path_obj = validate_path(input_path, must_exist=True)
    except ValueError as e:
        error_msg = f"Error validating path: {e}"
        logger.error(error_msg)
        click.echo(error_msg, err=True)
        sys.exit(1)
    
    # Process output path if provided
    output_path_obj = None
    if output_path:
        try:
            output_path_obj = Path(output_path)
            # Ensure directory exists for output
            if not output_path_obj.exists() and output_path_obj.suffix == '':
                output_path_obj.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            error_msg = f"Error with output path {output_path}: {str(e)}"
            logger.error(error_msg)
            click.echo(error_msg, err=True)
            sys.exit(1)
    
    # Instantiate components needed by DirectoryProcessor if processing a directory
    directory_processor = None
    if input_path_obj.is_dir():
        # These are needed by DirectoryProcessor but are also part of TextProcessor
        # We can either pass the already created processor or instantiate them again
        # Passing the processor instance seems cleaner if DirectoryProcessor accepts it
        security_utils = SecurityUtils() # Re-instantiate or get from factory?
        parallel_processor = ParallelProcessor() # Instantiate here
        directory_processor = DirectoryProcessor(
            config=processor.config, # Get config from the created processor
            security_utils=security_utils,
            parallel_processor=parallel_processor,
            single_file_processor=processor # Pass the main processor
        )

    if input_path_obj.is_file():
        # Process a single file using the main TextProcessor
        _process_single_file(
            processor, 
            input_path_obj, 
            output_path_obj, 
            format, 
            verbose_count,
            quiet_mode
        )
    elif input_path_obj.is_dir():
        # Process a directory using DirectoryProcessor
        # Decide parallel vs sequential based on config or a new CLI flag?
        # For now, let's assume parallel if possible, maybe add flag later.
        # TODO: Add flag or config for parallel directory processing
        use_parallel = True # Or get from config/flag

        if directory_processor is None:
            # This case should not happen due to the instantiation logic above
            # Log an error and exit or fall back to a default instantiation?
            logger.error("DirectoryProcessor was not instantiated correctly.")
            click.echo("Internal error: Could not initialize directory processor.", err=True)
            sys.exit(1)

        if use_parallel:
             directory_processor.process_directory_parallel(
                 input_dir=input_path_obj,
                 output_dir=output_path_obj,
                 output_format=format,
                 recursive=recursive,
                 # Pass file_extensions if a CLI option is added for it
                 # file_extensions=None, 
                 # Pass max_workers if a CLI option is added for it
                 # max_workers=None 
             )
        else:
             directory_processor.process_directory(
                 input_dir=input_path_obj,
                 output_dir=output_path_obj,
                 output_format=format,
                 recursive=recursive,
                 # Pass file_extensions if a CLI option is added for it
                 # file_extensions=None 
             )
        # _process_directory function is now removed, logic moved to DirectoryProcessor
    else:
        error_msg = f"Error: {input_path} is neither a file nor a directory"
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
    
    output_path_obj = output_path if output_path else None
    
    # Check if the file extension is supported
    extensions = get_supported_extensions()
    if input_path.suffix.lower() not in extensions:
        warning_msg = f"Warning: {input_path.name} has an unsupported extension. Processing may fail."
        logger.warning(warning_msg)
        if not quiet_mode:
            click.echo(warning_msg)
    
    # Process the file
    if not quiet_mode:
        click.echo(f"Processing file: {input_path}")
    start_time = time.time()
    
    try:
        result = processor.process_file(input_path, output_path_obj, output_format)
        processing_time = time.time() - start_time
        
        if result.success:
            success_msg = f"Successfully processed {input_path.name} in {processing_time:.2f}s"
            
            if verbose_count > 0:
                # Add metrics in verbose mode
                token_reduction = result.metrics.get("token_reduction_percent", 0)
                success_msg += f" (Token reduction: {token_reduction:.1f}%)"
                
            if not quiet_mode:
                click.echo(success_msg)
            
            # Show output location
            if result.output_path:
                output_location = f"Output saved to: {result.output_path}"
                logger.info(output_location)
                if not quiet_mode:
                    click.echo(output_location)
            else:
                logger.warning("No output path returned in the result")
                
            # Log detailed metrics if verbosity is high enough (e.g., -vv)
            if verbose_count >= 2:
                _log_detailed_metrics(result, logger)
                
            # Always show token statistics unless quiet mode
            if not quiet_mode:
                _display_token_statistics(
                    result.metrics, 
                    processing_time, 
                    output_format=output_format
                )
        else:
            error_msg = f"Failed to process {input_path.name}: {result.error}"
            logger.error(error_msg)
            click.echo(error_msg, err=True)
            
    except Exception as e:
        error_msg = f"Error processing {input_path.name}: {str(e)}"
        logger.exception(error_msg)
        click.echo(error_msg, err=True)
    except RuntimeError as e:
        # Catch runtime errors specifically raised by TextProcessor
        error_msg = f"Processing error for {input_path.name}: {str(e)}"
        logger.error(error_msg)
        click.echo(error_msg, err=True)
    except (IOError, OSError) as e:
        # Catch file system related errors
        error_msg = f"File system error processing {input_path.name}: {str(e)}"
        logger.error(error_msg)
        click.echo(error_msg, err=True)
    except Exception as e:
        # Catch any other unexpected error
        error_msg = f"Unexpected error processing {input_path.name}: {str(e)}"
        logger.exception(error_msg)
        click.echo(error_msg, err=True)


def _log_detailed_metrics(result: ProcessingResult, logger):
    """Log detailed metrics for processed file."""
    metrics = result.metrics
    # Ensure input_path is available and has a name attribute
    input_name = result.input_path.name if hasattr(result.input_path, 'name') else str(result.input_path)
    logger.debug(f"File: {input_name}")
    logger.debug(f"Original size (bytes): {metrics.get('original_size_bytes', 'N/A')}")
    logger.debug(f"Processed size (bytes): {metrics.get('processed_size_bytes', 'N/A')}")
    logger.debug(f"Size reduction: {metrics.get('size_reduction_percent', 0):.1f}%")
    logger.debug(f"Removed whitespace: {metrics.get('whitespace_removed', 0)} chars")
    logger.debug(f"Removed duplicates: {metrics.get('duplicates_removed', 0)} lines")
    logger.debug(f"Processing stages: {', '.join(metrics.get('processing_stages', []))}")


def _display_token_statistics(
    metrics: Dict[str, Any], 
    processing_time: float,
    output_format: Optional[str] = None
) -> None:
    """Display token statistics in a consistent format."""
    original_tokens = metrics.get("original_token_estimate", 0)
    processed_tokens = metrics.get("processed_token_estimate", 0)
    token_reduction = metrics.get("token_reduction_percent", 0)
    
    # Format output based on requested format
    if output_format == "json":
        stats = {
            "original_tokens": original_tokens,
            "processed_tokens": processed_tokens,
            "token_reduction_percent": token_reduction,
            "processing_time_seconds": processing_time,
            **{k: v for k, v in metrics.items() if k not in [
                "original_token_estimate", "processed_token_estimate", "token_reduction_percent"
            ]}
        }
        click.echo(json.dumps(stats, indent=2))
    else:
        click.echo(f"\nToken Statistics:")
        click.echo(f"Original tokens: {TOKEN_STAT_FORMAT.format(original_tokens)}")
        click.echo(f"Processed tokens: {TOKEN_STAT_FORMAT.format(processed_tokens)}")
        click.echo(f"Token reduction: {token_reduction:.2f}%")
        click.echo(f"Processing time: {processing_time:.2f}s")


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
              help='Custom configuration options in format key=value')
def generate_config(
    output: str, 
    level: str, 
    preset: Optional[str],
    custom_options: List[str]
):
    """Generate a configuration file with the specified cleaning level.
    
    Available presets:
      --preset=gpt4     Optimized for GPT-4 with 8K token context
      --preset=claude   Optimized for Claude with 100K token context
      --preset=llama    Aggressive optimization for 4K token models
      --preset=chatgpt  Optimized for ChatGPT with 4K token context
      --preset=rag      Designed for RAG/embedding vector database ingestion
      --preset=minimal  Very light processing, preserves most content
    
    Examples:
      tc generate-config --level aggressive
      tc generate-config --preset claude --output claude_config.yaml
      tc generate-config -c token_limit=5000 -c remove_urls=true
    """
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
    
    # Apply preset if specified
    if preset:
        try:
            preset_config = get_preset(preset)
            custom_overrides.update(preset_config)
            preset_desc = get_preset_description(preset)
            click.echo(f"Applied {preset} preset: {preset_desc}")
        except ValueError as e:
            logger.error(f"Error loading preset: {e}")
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    
    # Create config using factory
    config = config_factory.create_custom_config(level, custom_overrides or None)
    
    # Ensure output directory exists
    output_path = Path(output)
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the config
    config_factory.save_config(config, str(output_path))
    
    # Inform the user
    click.echo(f"Configuration file with {level} cleaning level saved to: {output}")
    if custom_overrides:
        click.echo(f"Applied {len(custom_overrides)} custom settings")
    
    logger.info(f"Generated {level} configuration file at {output}")


@cli.command(name="list-presets")
@click.option('--format', '-f', type=click.Choice(['table', 'json']),
              default='table', help='Output format for the list')
def list_presets(format: str):
    """List all available LLM presets and their descriptions.
    
    Examples:
      tc list-presets
      tc list-presets --format json
    """
    logger = get_logger(__name__)
    logger.info("Listing available LLM presets")
    
    presets = {}
    for preset_name in LLM_PRESETS:
        presets[preset_name] = get_preset_description(preset_name)
    
    if format == 'json':
        click.echo(json.dumps(presets, indent=2))
    else:
        click.echo("Available LLM Presets:")
        click.echo("")
        
        # Find the longest preset name for alignment
        max_len = max(len(name) for name in presets.keys())
        
        for name, description in sorted(presets.items()):
            click.echo(f"  {name.ljust(max_len)}  {description}")
        
        click.echo("\nUse these presets with the --preset option:")
        click.echo("  tc process my_file.pdf --preset claude")
        click.echo("  tc generate-config --preset gpt4 --output gpt4_config.yaml")


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
