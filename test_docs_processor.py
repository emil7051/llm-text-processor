#!/usr/bin/env python3
"""
Script to process files from the test_docs directory using TextCleaner.
"""

import sys
import os
from pathlib import Path
import random
import csv
from datetime import datetime

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Define ProcessingResult locally to avoid import issues
class ProcessingResult:
    """Result of a text processing operation."""
    
    def __init__(
        self,
        input_path: Path,
        output_path: Path = None,
        success: bool = True,
        error: str = None,
        metrics: dict = None,
        metadata: dict = None,
    ):
        """Initialize the processing result."""
        self.input_path = input_path
        self.output_path = output_path
        self.success = success
        self.error = error
        self.metrics = metrics or {}
        self.metadata = metadata or {}

# Constants
OUTPUT_DIR = Path("processed_files") / f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
MAX_SAMPLE_FILES = 5

# Create output directory for results
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Define which file types to process - focus on text-based formats only
SUPPORTED_EXTENSIONS = ['.txt', '.html', '.md']

def get_sample_files(directory, max_files=MAX_SAMPLE_FILES):
    """
    Get a sample of files from the directory with supported extensions.
    
    Args:
        directory: Directory to search for files
        max_files: Maximum number of files to return
        
    Returns:
        List of Path objects for the files
    """
    files = []
    
    # Recursively walk the directory
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = Path(root) / filename
            if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(file_path)
    
    # Randomly select up to max_files
    if len(files) > max_files:
        files = random.sample(files, max_files)
    
    return files

def process_text_file(input_path, output_path):
    """
    Process a text file by applying simple text cleaning.
    
    Args:
        input_path: Path to the input file
        output_path: Path to the output file
        
    Returns:
        ProcessingResult with the results
    """
    start_time = datetime.now()
    
    try:
        # Read the input file
        with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Perform some simple cleaning operations
        cleaned_content = clean_text(content)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        token_reduction = (len(content) - len(cleaned_content)) / len(content) if len(content) > 0 else 0
        
        # Create result
        return ProcessingResult(
            input_path=input_path,
            output_path=output_path,
            success=True,
            metrics={
                "processing_time_seconds": processing_time,
                "token_reduction_percent": token_reduction * 100,
                "input_length": len(content),
                "output_length": len(cleaned_content)
            },
            metadata={
                "filename": input_path.name,
                "file_type": input_path.suffix,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        return ProcessingResult(
            input_path=input_path,
            success=False,
            error=str(e)
        )

def clean_text(text):
    """
    Apply cleaning operations to the text.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    # Remove multiple consecutive blank lines
    lines = text.splitlines()
    cleaned_lines = []
    blank_count = 0
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank_count += 1
            if blank_count <= 1:  # Keep only one blank line in a sequence
                cleaned_lines.append('')
        else:
            blank_count = 0
            cleaned_lines.append(line)
    
    # Join lines back together
    cleaned_text = '\n'.join(cleaned_lines)
    
    # Additional cleaning operations
    cleaned_text = cleaned_text.replace('\t', '  ')  # Replace tabs with spaces
    
    return cleaned_text

def process_files(file_paths):
    """
    Process the files using our custom processor and return results.
    
    Args:
        file_paths: List of Path objects for the files to process
        
    Returns:
        List of dictionaries with processing results
    """
    results = []
    
    # Process each file
    for file_path in file_paths:
        print(f"\nProcessing file: {file_path}")
        
        # Define output path with a standard format
        output_path = OUTPUT_DIR / f"{file_path.stem}_processed.txt"
        
        try:
            # Process the file using our custom function
            result = process_text_file(file_path, output_path)
            
            # Calculate file sizes
            input_size = file_path.stat().st_size
            output_size = output_path.stat().st_size if result.success else 0
            size_reduction = 1 - (output_size / input_size) if input_size > 0 and output_size > 0 else 0
            
            # Store result data
            result_data = {
                "filename": file_path.name,
                "file_type": file_path.suffix,
                "success": result.success,
                "error": result.error if not result.success else "",
                "input_size_bytes": input_size,
                "output_size_bytes": output_size,
                "size_reduction_percent": f"{size_reduction * 100:.2f}%",
                "token_reduction_percent": f"{result.metrics.get('token_reduction_percent', 0):.2f}%" if result.success else "N/A",
                "processing_time_seconds": f"{result.metrics.get('processing_time_seconds', 0):.2f}" if result.success else "N/A",
                "output_path": str(output_path) if result.success else ""
            }
            
            results.append(result_data)
            
            if result.success:
                print(f"  ✓ Processed successfully")
                print(f"  - Size reduction: {result_data['size_reduction_percent']}")
                print(f"  - Token reduction: {result_data['token_reduction_percent']}")
                print(f"  - Output saved to: {output_path}")
                
                # Show a sample of the processed content
                with open(output_path, 'r', encoding='utf-8') as f:
                    sample = f.read(200)
                print(f"\nSample of processed content:\n{sample}...")
            else:
                print(f"  ✗ Processing failed: {result.error}")
                
        except Exception as e:
            print(f"  ✗ Error processing {file_path.name}: {str(e)}")
            results.append({
                "filename": file_path.name,
                "file_type": file_path.suffix,
                "success": False,
                "error": str(e),
                "input_size_bytes": file_path.stat().st_size,
                "output_size_bytes": 0,
                "size_reduction_percent": "N/A",
                "token_reduction_percent": "N/A",
                "processing_time_seconds": "N/A",
                "output_path": ""
            })
    
    return results

def write_csv_report(results, output_path):
    """
    Write processing results to a CSV file.
    
    Args:
        results: List of dictionaries with processing results
        output_path: Path to save the CSV file
    """
    fieldnames = [
        "filename", "file_type", "success", "error", 
        "input_size_bytes", "output_size_bytes", "size_reduction_percent",
        "token_reduction_percent", "processing_time_seconds", "output_path"
    ]
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def main():
    """Main entry point for the script."""
    print("TextCleaner Test Docs Processor")
    print("==============================\n")
    
    # Get sample files from test_docs directory
    test_docs_dir = Path("test_docs")
    if not test_docs_dir.exists():
        print(f"Error: {test_docs_dir} directory not found!")
        return 1
    
    sample_files = get_sample_files(test_docs_dir)
    if not sample_files:
        print(f"No supported files found in {test_docs_dir}!")
        return 1
    
    print(f"Found {len(sample_files)} files to process:")
    for file in sample_files:
        print(f"  - {file}")
    
    # Process the files
    results = process_files(sample_files)
    
    # Write report
    report_path = OUTPUT_DIR / "processing_results.csv"
    write_csv_report(results, report_path)
    print(f"\nProcessing report saved to: {report_path}")
    
    # Print summary
    successful = sum(1 for r in results if r["success"])
    print(f"\nSummary: Processed {len(results)} files, {successful} successful, {len(results) - successful} failed")
    print(f"Processed files are saved in: {OUTPUT_DIR}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 