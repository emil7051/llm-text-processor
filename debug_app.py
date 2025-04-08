#!/usr/bin/env python3
"""
Debug script to manually test the TextCleaner's core functionality.
"""

import sys
import tempfile
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import our modules with the correct paths
from textcleaner.config.config_manager import ConfigManager
from textcleaner.core.processor import TextProcessor
from textcleaner.core.models import ProcessingResult
from textcleaner.utils.security import TestSecurityUtils

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

def create_test_file(directory, filename, content):
    """Create a test file with the given content."""
    file_path = directory / filename
    with open(file_path, "w") as f:
        f.write(content)
    return file_path

def main():
    """Main function to test the TextCleaner functionality."""
    print("Testing TextCleaner core functionality...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"Created temp directory: {temp_path}")
        
        # Create a test text file
        text_file = create_test_file(temp_path, "sample.txt", TEXT_CONTENT)
        print(f"Created test file: {text_file}")
        
        # Create a test HTML file
        html_file = create_test_file(temp_path, "sample.html", HTML_CONTENT)
        print(f"Created test HTML file: {html_file}")
        
        # Create output directory
        output_dir = temp_path / "output"
        output_dir.mkdir()
        
        try:
            # Create a TestSecurityUtils instance for testing
            security_utils = TestSecurityUtils()
            
            # Initialize the processor with the test security utils
            print("Initializing TextProcessor...")
            processor = TextProcessor(security_utils=security_utils)
            
            # Process the text file
            print(f"\nProcessing text file: {text_file}")
            text_output = output_dir / "sample_processed.txt"
            text_result = processor.process_file(text_file, text_output)
            
            if text_result.success:
                print(f"Successfully processed text file to: {text_result.output_path}")
                print(f"Metrics: {text_result.metrics}")
                with open(text_result.output_path, "r") as f:
                    print(f"\nText Output Content (first 200 chars):\n{f.read()[:200]}...")
            else:
                print(f"Failed to process text file: {text_result.error}")
            
            # Process the HTML file
            print(f"\nProcessing HTML file: {html_file}")
            html_output = output_dir / "sample_processed.html"
            html_result = processor.process_file(html_file, html_output)
            
            if html_result.success:
                print(f"Successfully processed HTML file to: {html_result.output_path}")
                print(f"Metrics: {html_result.metrics}")
                with open(html_result.output_path, "r") as f:
                    print(f"\nHTML Output Content (first 200 chars):\n{f.read()[:200]}...")
            else:
                print(f"Failed to process HTML file: {html_result.error}")
                
        except Exception as e:
            print(f"Error during processing: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main() 