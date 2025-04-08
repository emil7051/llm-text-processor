"""File utility functions for the text processor."""

import os
import re
from pathlib import Path
from typing import List, Set, Tuple, Union


def sanitize_filename(filename: str) -> str:
    """Remove unsafe characters from a filename.
    
    Args:
        filename: The filename to sanitize.
        
    Returns:
        Sanitized filename.
    """
    # Replace characters that are unsafe for filenames
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


def find_files(
    directory: Union[str, Path],
    extensions: Set[str] = None,
    recursive: bool = True
) -> List[Path]:
    """Find files with specified extensions in a directory.
    
    Args:
        directory: Directory to search in.
        extensions: Set of file extensions to look for (with leading dot).
            If None, all supported extensions are used.
        recursive: Whether to search in subdirectories.
        
    Returns:
        List of paths to matching files.
        
    Raises:
        FileNotFoundError: If the directory doesn't exist.
    """
    if isinstance(directory, str):
        directory = Path(directory)
        
    if not directory.exists() or not directory.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory}")
        
    if extensions is None:
        extensions = get_supported_extensions()
        
    found_files = []
    
    if recursive:
        # Search recursively
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in extensions:
                    found_files.append(file_path)
    else:
        # Only search in top directory
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                found_files.append(file_path)
                
    return found_files


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
