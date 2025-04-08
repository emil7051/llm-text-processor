#!/usr/bin/env python
"""Sample script for batch processing files with the LLM Text Processor."""

import os
import sys
import time
from pathlib import Path

# Add the parent directory to the Python path to import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.textcleaner import TextProcessor
from src.textcleaner.utils.metrics import generate_metrics_report


def main():
    """Demonstrate batch processing of files."""
    # Path to the directory containing files to process
    input_dir = Path("../../")  # Adjust this path to your files
    
    # Path for the output files
    output_dir = Path("./processed_files")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing files in: {input_dir.resolve()}")
    print(f"Output will be saved to: {output_dir.resolve()}")
    
    # Initialize the text processor
    processor = TextProcessor()
    
    # Start timing
    start_time = time.time()
    
    # Process the directory
    results = processor.process_directory(
        input_dir,
        output_dir,
        output_format="markdown",
        # Only process these extensions
        file_extensions=[".pdf", ".docx", ".xlsx", ".pptx"]
    )
    
    # End timing
    elapsed_time = time.time() - start_time
    
    # Print summary
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    
    print(f"\nProcessing complete: {successful} successful, {failed} failed")
    print(f"Total time: {elapsed_time:.2f} seconds")
    
    # Generate a summary report
    if results:
        report_path = output_dir / "processing_report.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Processing Report\n\n")
            f.write(f"Processed {len(results)} files in {elapsed_time:.2f} seconds\n\n")
            
            # Table header
            f.write("| File | Status | Output | Size Reduction | Token Reduction |\n")
            f.write("|------|--------|--------|----------------|----------------|\n")
            
            # Add a row for each file
            for result in results:
                file_name = result.input_path.name
                status = "✅ Success" if result.success else f"❌ Failed: {result.error}"
                
                output = result.output_path.name if result.output_path else "-"
                size_red = f"{result.metrics.get('text_length_reduction_percent', 0):.2f}%" if result.success else "-"
                token_red = f"{result.metrics.get('token_reduction_percent', 0):.2f}%" if result.success else "-"
                
                f.write(f"| {file_name} | {status} | {output} | {size_red} | {token_red} |\n")
        
        print(f"Report saved to: {report_path}")
    
    # If we have successful results, show detailed metrics for one file
    if successful > 0:
        # Get the first successful result
        success_result = next(r for r in results if r.success)
        
        # Generate a detailed metrics report
        metrics_report = generate_metrics_report(success_result.metrics)
        
        # Save the report
        detail_path = output_dir / f"{success_result.input_path.stem}_metrics.md"
        with open(detail_path, "w", encoding="utf-8") as f:
            f.write(metrics_report)
            
        print(f"Detailed metrics for {success_result.input_path.name} saved to: {detail_path}")


if __name__ == "__main__":
    main()
