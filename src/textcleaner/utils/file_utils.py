"""File utility functions for the text processor."""

# import os # Removed unused import
import re
from pathlib import Path
from typing import List, Set, Tuple, Union, Optional, Generator, TYPE_CHECKING

# Use TYPE_CHECKING for imports needed only for type hints
if TYPE_CHECKING:
    from textcleaner.core.file_registry import FileTypeRegistry
    # Add ConfigManager and SecurityUtils imports under TYPE_CHECKING
    from textcleaner.config.config_manager import ConfigManager
    from textcleaner.utils.security import SecurityUtils

def sanitize_filename(filename: str) -> str:
    """Remove unsafe characters from a filename.
    
    Args:
        filename: The filename to sanitize.
        
    Returns:
        Sanitized filename.
    """
    # First replace control characters (like \n, \t) with underscores
    filename = re.sub(r'[\x00-\x1F\x7F]', '_', filename)
    
    # Replace other characters that are unsafe for filenames
    return re.sub(r'[^\w\s.-]', '_', filename)


def get_supported_extensions() -> Set[str]:
    """Get a set of all supported file extensions.
    
    Returns:
        Set of supported file extensions (with leading dot).
    """
    # These should be kept in sync with the converters
    return {
        # PDF
        ".pdf",
        # Microsoft Office
        ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        # OpenDocument
        ".odt", ".ods", ".odp",
        # Plain text
        ".txt", ".md", ".csv",
        # Web formats
        ".html", ".htm", ".xml", ".json",
    }


def find_files(directory: Path, recursive: bool = True) -> Generator[Path, None, None]:
    """Yields files found in a directory, optionally recursively.

    Args:
        directory: The directory path to search.
        recursive: If True, searches subdirectories recursively.

    Yields:
        Path objects for each file found.

    Raises:
        FileNotFoundError: If the directory does not exist.
        NotADirectoryError: If the path is not a directory.
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")

    if recursive:
        for item in directory.rglob("*"):
            if item.is_file():
                yield item
    else:
        for item in directory.glob("*"):
            if item.is_file():
                yield item


def ensure_dir_exists(directory: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path.
        
    Returns:
        Path object for the directory.
        
    Raises:
        PermissionError: If the directory cannot be created due to permissions.
    """
    if isinstance(directory, str):
        directory = Path(directory)
        
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_relative_path(
    file_path: Path,
    base_dir: Path
) -> Path:
    """Get the relative path from a base directory.
    
    Args:
        file_path: Absolute path to a file.
        base_dir: Base directory to make the path relative to.
        
    Returns:
        Relative path.
        
    Raises:
        ValueError: If the file is not within the base directory.
    """
    try:
        return file_path.relative_to(base_dir)
    except ValueError:
        raise ValueError(f"File {file_path} is not within base directory {base_dir}")


def split_path_by_extension(path: Union[str, Path]) -> Tuple[Path, str]:
    """Split a path into the path without extension and the extension.
    
    Args:
        path: Path to split.
        
    Returns:
        Tuple of (path_without_extension, extension).
    """
    if isinstance(path, str):
        path = Path(path)
        
    return path.with_suffix(''), path.suffix.lower()


def get_default_extension(format_name: str, file_registry: 'FileTypeRegistry') -> str:
    """Get the default file extension for a format using the file registry.
    
    Args:
        format_name: The name of the output format (e.g., 'markdown', 'plain_text').
        file_registry: The FileTypeRegistry instance to consult.
        
    Returns:
        The default extension for the format (e.g., 'md', 'txt').
        
    Raises:
        ValueError: If the file_registry is not provided or invalid.
        KeyError: If the format_name is not found in the registry.
    """
    # Import moved to top under TYPE_CHECKING
    # from textcleaner.core.file_registry import FileTypeRegistry 
    # Remove fallback logic - assume registry is always passed correctly
    # if not isinstance(file_registry, FileTypeRegistry):
    #      # Fallback or raise error if registry not provided correctly
    #      # Simple fallback for common cases:
    #      mapping = {"markdown": "md", "plain_text": "txt", "json": "json", "csv": "csv"}
    #      return mapping.get(format_name, format_name) # Default to format name itself
        
    # Add check for valid registry instance
    if file_registry is None or not hasattr(file_registry, 'get_default_extension'):
        raise ValueError("Invalid or missing FileTypeRegistry instance provided.")
        
    try:
        return file_registry.get_default_extension(format_name)
    except KeyError:
        # Re-raise KeyError if format not found, letting caller handle it
        raise KeyError(f"Format '{format_name}' not found in the file registry.") 
        

def get_format_from_extension(extension: str) -> str:
    """Attempt to guess format name from file extension."""
    ext_lower = extension.lower().lstrip('.')
    mapping = {
        "md": "markdown",
        "txt": "plain_text",
        "json": "json",
        "csv": "csv",
        "html": "html",
        "htm": "html",
        "xml": "xml",
        "pdf": "pdf",
        "docx": "docx",
        "doc": "doc",
        "xlsx": "xlsx",
        "xls": "xls",
        "pptx": "pptx",
        "ppt": "ppt"
        # Add other known mappings as needed
    }
    # Fallback to the extension itself if not found
    return mapping.get(ext_lower, ext_lower)


def resolve_output_dir(
    output_dir_param: Optional[Union[str, Path]], 
    config: 'ConfigManager', 
    security: 'SecurityUtils'
) -> Path:
    """Resolve, validate, and ensure existence of the output directory."""
    if output_dir_param is None:
        output_dir_p = Path(config.get("general.output_dir", "processed_files"))
    else:
        output_dir_p = Path(output_dir_param) if isinstance(output_dir_param, str) else output_dir_param

    is_valid, error = security.validate_output_path(output_dir_p)
    if not is_valid:
        # Use PermissionError consistent with DirectoryProcessor's original handling
        raise PermissionError(f"Output directory validation failed: {error}")

    try:
        # ensure_dir_exists handles the mkdir call
        ensure_dir_exists(output_dir_p) 
    except OSError as e:
        # Use RuntimeError consistent with DirectoryProcessor's original handling
        raise RuntimeError(f"Failed to create output directory {output_dir_p}: {e}") from e

    return output_dir_p


def determine_output_format_and_extension(
    output_format_param: Optional[str],
    output_path_param: Optional[Path],
    config: 'ConfigManager',
    file_registry: 'FileTypeRegistry'
) -> Tuple[str, str]:
    """Determine the final output format and extension based on parameters and config."""
    guessed_format = None
    if output_path_param:
        guessed_format = get_format_from_extension(output_path_param.suffix)

    # Priority: Explicit format > Guessed from output path > Config default
    final_output_format = output_format_param or guessed_format or config.get("output.default_format", "markdown")

    # Priority for extension: Config mapping > Default from registry
    output_ext = config.get(f"general.file_extension_mapping.{final_output_format}", None)
    if output_ext is None:
        try:
            # get_default_extension expects format name, returns extension without dot
            output_ext = get_default_extension(final_output_format, file_registry) 
        except KeyError:
            # Fallback if format somehow isn't in registry (shouldn't happen in normal flow)
            output_ext = final_output_format 
        except ValueError as e:
            # Handle case where file_registry might be invalid (though unlikely here)
            raise ValueError(f"Error getting default extension: {e}") from e


    return final_output_format, output_ext
