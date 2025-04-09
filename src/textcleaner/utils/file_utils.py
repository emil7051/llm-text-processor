"""File utility functions for the text processor."""

# import os # Removed unused import
import re
from pathlib import Path
from typing import List, Set, Tuple, Union, Optional, Generator, TYPE_CHECKING

# Use TYPE_CHECKING for imports needed only for type hints
if TYPE_CHECKING:
    from textcleaner.core.file_registry import FileTypeRegistry

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
