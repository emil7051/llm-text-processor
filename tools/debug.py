#!/usr/bin/env python3
"""
Debug utility for manually testing TextCleaner's core functionality.

This script allows you to process sample files or predefined test content
to verify TextCleaner's functionality during development.
"""

import sys
import tempfile
import argparse
from pathlib import Path
import os
from typing import Optional, Dict, Any, List, Tuple

from textcleaner.config.config_manager import ConfigManager
from textcleaner.core.processor import TextProcessor
from textcleaner.core.models import ProcessingResult
from textcleaner.utils.security import TestSecurityUtils
from textcleaner.utils.logging_config import get_logger

# Configure logging
logger = get_logger("debug")

# Constants for test content
TEXT_CONTENT = """# Sample Text Document
        
This is a sample text document that will be used to test the TextCleaner.

## Section 1

* Item 1
* Item 2
* Item 3

## Section 2

This section contains some text that should be preserved.
"""

HTML_CONTENT = """<!DOCTYPE html>
<html>
<head>
    <title>Sample HTML Document</title>
    <meta name="author" content="Test Author">
</head>
<body>
    <h1>Sample HTML Document</h1>
    <p>This is a paragraph with <b>bold</b> and <i>italic</i> text.</p>
    <ul>
        <li>List item 1</li>
        <li>List item 2</li>
    </ul>
    <script>console.log('This should be removed');</script>
</body>
</html>
"""

# Add more sample content types as needed
MARKDOWN_CONTENT = """# Markdown Document

This is a *sample* markdown document with **formatting**.

## Section 1

1. Ordered item 1
2. Ordered item 2

## Section 2

[This is a link](https://example.com)

```
def sample_code():
    return "This is a code block"
```
"""

# Map of test content types to their content
TEST_CONTENTS = {
    "text": TEXT_CONTENT,
    "html": HTML_CONTENT,
    "markdown": MARKDOWN_CONTENT
}


def create_test_file(directory: Path, filename: str, content: str) -> Path:
    """
    Create a test file with the given content.
    
    Args:
        directory: Directory to create the file in
        filename: Name of the file to create
        content: Content to write to the file
        
    Returns:
        Path object pointing to the created file
    """
    file_path = directory / filename
    with open(file_path, "w") as f:
        f.write(content)
    return file_path


def process_file(
    processor: TextProcessor, 
    input_path: Path, 
    output_path: Path,
    verbose: bool = True
) -> ProcessingResult:
    """
    Process a single file and optionally print details.
    
    Args:
        processor: TextProcessor instance
        input_path: Path to the input file
        output_path: Path for the output file
        verbose: Whether to print processing details
        
    Returns:
        ProcessingResult from the processor
    """
    if verbose:
        print(f"\nProcessing file: {input_path}")
    
    # Process the file
    result = processor.process_file(input_path, output_path)
    
    if verbose:
        if result.success:
            print(f"✓ Successfully processed to: {result.output_path}")
            
            # Print metrics if available
            if result.metrics:
                print("Metrics:")
                for key, value in result.metrics.items():
                    print(f"  - {key}: {value}")
            
            # Show a sample of the output
            try:
                with open(result.output_path, "r") as f:
                    content = f.read()
                    print(f"\nOutput Content (first 200 chars):\n{content[:200]}...")
            except Exception as e:
                print(f"Error reading output file: {e}")
        else:
            print(f"✗ Failed to process: {result.error}")
    
    return result


def test_with_sample_content(
    content_type: str = "text",
    config_type: str = "standard",
    output_dir: Optional[Path] = None,
    verbose: bool = True
) -> Tuple[ProcessingResult, Path]:
    """
    Test TextCleaner with sample content.
    
    Args:
        content_type: Type of content to test with (text, html, markdown)
        config_type: Configuration type to use
        output_dir: Directory to save output (uses temp dir if None)
        verbose: Whether to print processing details
        
    Returns:
        Tuple of (ProcessingResult, temp_directory) - temp_directory will be 
        a Path if using a temporary directory, None if output_dir was provided
    """
    # Get the content based on type
    content = TEST_CONTENTS.get(content_type, TEXT_CONTENT)
    
    # Create a temporary directory if needed
    if output_dir is None:
        temp_dir_obj = tempfile.TemporaryDirectory()
        temp_dir = Path(temp_dir_obj.name)
        if verbose:
            print(f"Created temp directory: {temp_dir}")
    else:
        temp_dir_obj = None
        temp_dir = output_dir
        os.makedirs(temp_dir, exist_ok=True)
        
    try:
        # Create output directory
        test_output_dir = temp_dir / "output"
        test_output_dir.mkdir(exist_ok=True)
        
        # Create the test file
        file_ext = ".txt" if content_type == "text" else f".{content_type}"
        test_file = create_test_file(temp_dir, f"sample{file_ext}", content)
        
        if verbose:
            print(f"Created test file: {test_file}")
        
        # Create a security utils instance for testing
        security_utils = TestSecurityUtils()
        
        # Initialize the processor with the test security utils
        if verbose:
            print(f"Initializing TextProcessor with {config_type} configuration...")
        processor = TextProcessor(config_type=config_type, security_utils=security_utils)
        
        # Process the file
        output_path = test_output_dir / f"sample_processed{file_ext}"
        result = process_file(processor, test_file, output_path, verbose)
        
        return result, temp_dir_obj
    
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        if temp_dir_obj:
            temp_dir_obj.cleanup()
        raise


def test_with_custom_file(
    file_path: Path,
    config_type: str = "standard", 
    output_dir: Optional[Path] = None,
    verbose: bool = True
) -> ProcessingResult:
    """
    Test TextCleaner with a custom file.
    
    Args:
        file_path: Path to the file to process
        config_type: Configuration type to use
        output_dir: Directory to save output (uses same directory if None)
        verbose: Whether to print processing details
        
    Returns:
        ProcessingResult from the processor
    """
    # Create output directory if provided
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = file_path.parent
    
    # Create a security utils instance for testing
    security_utils = TestSecurityUtils()
    
    # Initialize the processor with the test security utils
    if verbose:
        print(f"Initializing TextProcessor with {config_type} configuration...")
    processor = TextProcessor(config_type=config_type, security_utils=security_utils)
    
    # Process the file
    output_path = output_dir / f"{file_path.stem}_processed{file_path.suffix}"
    return process_file(processor, file_path, output_path, verbose)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Debug utility for TextCleaner'
    )
    
    parser.add_argument(
        '-t', '--type',
        choices=list(TEST_CONTENTS.keys()),
        default='text',
        help='Type of sample content to test with'
    )
    
    parser.add_argument(
        '-c', '--config',
        choices=['minimal', 'standard', 'aggressive'],
        default='standard',
        help='Configuration type to use'
    )
    
    parser.add_argument(
        '-f', '--file',
        type=str,
        help='Path to a custom file to process instead of sample content'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        help='Directory to save output files'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Run in quiet mode (less output)'
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main function to test the TextCleaner functionality.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    print("TextCleaner Debug Utility")
    print("========================\n")
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up output directory if specified
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    try:
        # Process either a custom file or sample content
        if args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File not found: {file_path}")
                return 1
                
            result = test_with_custom_file(
                file_path=file_path,
                config_type=args.config,
                output_dir=output_dir,
                verbose=not args.quiet
            )
            
            # Return code based on success
            return 0 if result.success else 1
        else:
            # Test with sample content
            result, temp_dir = test_with_sample_content(
                content_type=args.type,
                config_type=args.config,
                output_dir=output_dir,
                verbose=not args.quiet
            )
            
            # Clean up temporary directory if we created one
            if temp_dir and not args.quiet:
                print(f"Note: Temporary files will be deleted when the program exits")
            
            # Return code based on success
            return 0 if result.success else 1
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())