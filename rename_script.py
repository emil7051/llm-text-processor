#!/usr/bin/env python3
"""
Script to rename package references from llm_text_processor to textcleaner.
"""

import os
import re
from pathlib import Path

# Define source and target package names
SOURCE_PKG = "llm_text_processor"
TARGET_PKG = "textcleaner"


def process_py_file(file_path):
    """Process a Python file to update imports and other references."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count occurrences before replacement
    original_references = content.count(SOURCE_PKG)
    
    if original_references == 0:
        return 0
    
    # Replace import statements
    content = re.sub(
        rf'from {SOURCE_PKG}([\.\s])', 
        f'from {TARGET_PKG}\\1', 
        content
    )
    
    # Replace import statements at the beginning of lines
    content = re.sub(
        rf'^import {SOURCE_PKG}(\s|\.|$)', 
        f'import {TARGET_PKG}\\1', 
        content, 
        flags=re.MULTILINE
    )
    
    # Replace logging names
    content = content.replace(
        f'"{SOURCE_PKG}"', 
        f'"{TARGET_PKG}"'
    )
    
    # Replace other references to the package
    content = content.replace(SOURCE_PKG, TARGET_PKG)
    
    # Write updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return original_references


def process_directory(directory, extensions=None):
    """
    Process all files in a directory and its subdirectories.
    
    Args:
        directory: Path to the directory to process
        extensions: List of file extensions to process, or None for all
    
    Returns:
        Tuple of (files_processed, total_references)
    """
    if extensions is None:
        extensions = ['.py', '.md', '.rst', '.txt', '.yaml', '.toml']
    
    files_processed = 0
    total_references = 0
    
    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            
            # Skip files with extensions we don't want to process
            if not any(file_path.endswith(ext) for ext in extensions):
                continue
            
            # Process the file
            references = process_py_file(file_path)
            if references > 0:
                files_processed += 1
                total_references += references
                print(f"Updated {references} references in {file_path}")
    
    return files_processed, total_references


def main():
    """Main entry point."""
    print(f"Renaming package references from '{SOURCE_PKG}' to '{TARGET_PKG}'")
    
    # Process the src directory
    src_dir = Path("src")
    if not src_dir.exists():
        print(f"Error: {src_dir} directory not found!")
        return 1
    
    files_processed, total_references = process_directory(src_dir)
    print(f"\nCompleted! Updated {total_references} references in {files_processed} files")
    
    return 0


if __name__ == "__main__":
    exit(main())
