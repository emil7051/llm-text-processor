#!/usr/bin/env python3
"""
Script to rename package references within a Python project.

This utility can be used to rename package imports and references throughout
a codebase, which is useful when refactoring or renaming a package.
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Tuple, Optional


def process_file(file_path: Path, source_pkg: str, target_pkg: str) -> int:
    """
    Process a file to update package references.
    
    Args:
        file_path: Path to the file to process
        source_pkg: Original package name
        target_pkg: New package name
        
    Returns:
        Number of references updated
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Skip binary files
        return 0
    
    # Count occurrences before replacement
    original_references = content.count(source_pkg)
    
    if original_references == 0:
        return 0
    
    # Replace import statements
    content = re.sub(
        rf'from {source_pkg}([\.\s])', 
        f'from {target_pkg}\\1', 
        content
    )
    
    # Replace import statements at the beginning of lines
    content = re.sub(
        rf'^import {source_pkg}(\s|\.|$)', 
        f'import {target_pkg}\\1', 
        content, 
        flags=re.MULTILINE
    )
    
    # Replace logging names
    content = content.replace(
        f'"{source_pkg}"', 
        f'"{target_pkg}"'
    )
    
    # Replace other references to the package
    content = content.replace(source_pkg, target_pkg)
    
    # Write updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return original_references


def process_directory(
    directory: Path, 
    source_pkg: str, 
    target_pkg: str,
    extensions: Optional[List[str]] = None,
    verbose: bool = False
) -> Tuple[int, int]:
    """
    Process all files in a directory and its subdirectories.
    
    Args:
        directory: Path to the directory to process
        source_pkg: Original package name
        target_pkg: New package name
        extensions: List of file extensions to process, or None for defaults
        verbose: Whether to print details for each file
        
    Returns:
        Tuple of (files_processed, total_references)
    """
    if extensions is None:
        extensions = ['.py', '.md', '.rst', '.txt', '.yaml', '.toml']
    
    files_processed = 0
    total_references = 0
    
    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = Path(root) / filename
            
            # Skip files with extensions we don't want to process
            if not any(str(file_path).endswith(ext) for ext in extensions):
                continue
            
            # Process the file
            references = process_file(file_path, source_pkg, target_pkg)
            if references > 0:
                files_processed += 1
                total_references += references
                if verbose:
                    print(f"Updated {references} references in {file_path}")
    
    return files_processed, total_references


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Rename package references in a Python project'
    )
    
    parser.add_argument(
        'source',
        type=str,
        help='Original package name'
    )
    
    parser.add_argument(
        'target',
        type=str,
        help='New package name'
    )
    
    parser.add_argument(
        '-d', '--directory',
        type=str,
        default='.',
        help='Directory to process (default: current directory)'
    )
    
    parser.add_argument(
        '-e', '--extensions',
        type=str,
        default=None,
        help='Comma-separated list of file extensions to process (default: .py,.md,.rst,.txt,.yaml,.toml)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print details for each file processed'
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    args = parse_arguments()
    
    source_pkg = args.source
    target_pkg = args.target
    directory = Path(args.directory)
    verbose = args.verbose
    
    # Parse extensions if provided
    extensions = None
    if args.extensions:
        extensions = [ext.strip() for ext in args.extensions.split(',')]
        # Ensure each extension starts with a dot
        extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
    
    print(f"Renaming package references from '{source_pkg}' to '{target_pkg}'")
    print(f"Processing directory: {directory}")
    
    if not directory.exists():
        print(f"Error: Directory not found: {directory}")
        return 1
    
    try:
        files_processed, total_references = process_directory(
            directory, source_pkg, target_pkg, extensions, verbose
        )
        
        print(f"\nCompleted!")
        print(f"Updated {total_references} references in {files_processed} files")
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 