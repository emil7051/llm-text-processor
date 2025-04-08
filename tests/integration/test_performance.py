"""
Performance monitoring tests for the LLM Text Processor
"""

import pytest
import time
from pathlib import Path
import json

from textcleaner.core.factories import TextProcessorFactory
from textcleaner.utils.performance import performance_monitor


@pytest.fixture
def reset_performance_monitor():
    """Reset the performance monitor before and after each test"""
    performance_monitor.reset()
    yield
    performance_monitor.reset()


@pytest.fixture
def sample_large_text_file(temp_directory):
    """Create a larger sample text file for performance testing"""
    file_path = temp_directory / "large_sample.txt"
    
    # Create a file with repeated content to simulate a larger document
    with open(file_path, "w") as f:
        # Header
        f.write("DOCUMENT TITLE: PERFORMANCE TEST\n")
        f.write("===============================\n\n")
        f.write("Author: Test User\n")
        f.write("Date: 2023-01-01\n\n")
        
        # Generate repeated sections to make the file larger
        for i in range(20):
            f.write(f"SECTION {i}: TEST CONTENT\n")
            f.write("-----------------------\n\n")
            
            # Paragraphs
            for j in range(5):
                f.write(f"This is paragraph {j} of section {i}. It contains test content for performance evaluation. ")
                f.write(f"The text processor should be able to efficiently process this content. ")
                f.write(f"We are using repeated content to ensure the file is large enough for meaningful metrics. ")
                f.write(f"This text will be repeated multiple times to simulate a larger document. ")
                f.write(f"Some parts of this text are deliberately redundant to test optimization capabilities. ")
                f.write(f"Some parts of this text are deliberately redundant to test optimization capabilities. ")
                f.write("\n\n")
                
            # Lists
            f.write("Key points:\n")
            for j in range(3):
                f.write(f"- Item {j+1}: This is an important point in section {i}\n")
            f.write("\n\n")
    
    return file_path


def test_performance_monitoring_integration(sample_large_text_file, temp_directory, reset_performance_monitor):
    """Test that performance monitoring integrates with text processing"""
    output_file = temp_directory / "performance_output.md"
    
    # Create processor
    factory = TextProcessorFactory()
    processor = factory.create_processor(config_type="aggressive")
    
    # Process the file
    result = processor.process_file(sample_large_text_file, output_file)
    
    # Verify successful processing
    assert result.success
    assert result.output_path.exists()
    
    # Generate and save performance report
    report_path = temp_directory / "performance_report.json"
    performance_monitor.save_report(report_path)
    
    # Verify report exists
    assert report_path.exists()
    
    # Validate report structure
    with open(report_path) as f:
        report = json.load(f)
    
    # Check report structure
    assert report["enabled"] is True
    assert "total_runtime_seconds" in report
    assert "operations" in report
    
    # Verify specific operations were recorded
    operation_names = [op["name"] for op in report["operations"]]
    assert "process_file" in operation_names
    
    # Verify process_file operation has expected metrics
    process_op = next(op for op in report["operations"] if op["name"] == "process_file")
    assert "average_seconds" in process_op
    assert "count" in process_op
    assert process_op["count"] == 1  # We processed one file


def test_parallel_vs_sequential_performance(temp_directory, reset_performance_monitor):
    """Compare performance of parallel vs sequential processing"""
    # Create multiple test files
    input_dir = temp_directory / "perf_input"
    input_dir.mkdir()
    
    # Number of test files
    num_files = 5
    
    # Create test files
    for i in range(num_files):
        file_path = input_dir / f"test_file_{i}.txt"
        with open(file_path, "w") as f:
            f.write(f"Test file {i} for performance comparison.\n\n")
            # Add some content to make the file substantive
            for j in range(100):
                f.write(f"Line {j} of test content for file {i}. This is a performance test.\n")
    
    # Create output directories
    seq_output = temp_directory / "perf_seq_output"
    par_output = temp_directory / "perf_par_output"
    
    # Create processor
    factory = TextProcessorFactory()
    processor = factory.create_processor()
    
    # Time sequential processing
    performance_monitor.reset()
    start_time = time.time()
    seq_results = processor.process_directory(input_dir, seq_output)
    seq_time = time.time() - start_time
    
    # Save sequential performance report
    seq_report_path = temp_directory / "sequential_performance.json"
    performance_monitor.save_report(seq_report_path)
    
    # Time parallel processing
    performance_monitor.reset()
    start_time = time.time()
    par_results = processor.process_directory_parallel(input_dir, par_output)
    par_time = time.time() - start_time
    
    # Save parallel performance report
    par_report_path = temp_directory / "parallel_performance.json"
    performance_monitor.save_report(par_report_path)
    
    # Verify all files were processed
    assert len(seq_results) == num_files
    assert len(par_results) == num_files
    
    # Check that all processing was successful
    assert all(r.success for r in seq_results)
    assert all(r.success for r in par_results)
    
    # Print performance comparison
    print(f"\nPerformance comparison:")
    print(f"Sequential processing: {seq_time:.2f}s")
    print(f"Parallel processing:   {par_time:.2f}s")
    print(f"Speedup:               {seq_time/par_time:.2f}x")
    
    # On multi-core systems, parallel should be faster
    # This assertion might fail on single-core systems or very small files
    # We'll make this a soft assertion
    if par_time > seq_time:
        print("WARNING: Parallel processing was slower than sequential")
        print("This may happen on single-core systems or with very small files")
    
    # Verify reports exist
    assert seq_report_path.exists()
    assert par_report_path.exists()


def test_performance_context_manager():
    """Test the performance context manager"""
    # Reset the monitor
    performance_monitor.reset()
    
    # Time an operation using the context manager
    with performance_monitor.performance_context("test_operation"):
        # Simulate some work
        time.sleep(0.1)
    
    # Verify the operation was recorded
    report = performance_monitor.generate_report()
    operations = {op["name"]: op for op in report["operations"]}
    
    assert "test_operation" in operations
    assert operations["test_operation"]["count"] == 1
    assert operations["test_operation"]["average_seconds"] >= 0.1
    
    # Time multiple operations
    for i in range(3):
        with performance_monitor.performance_context("repeated_operation"):
            # Simulate varying work
            time.sleep(0.05 * (i + 1))
    
    # Verify the operations were recorded
    report = performance_monitor.generate_report()
    operations = {op["name"]: op for op in report["operations"]}
    
    assert "repeated_operation" in operations
    assert operations["repeated_operation"]["count"] == 3
    
    # Check statistics
    op_stats = operations["repeated_operation"]
    assert "min_seconds" in op_stats
    assert "max_seconds" in op_stats
    assert "average_seconds" in op_stats
    
    # Min should be around 0.05s, max around 0.15s
    assert 0.03 <= op_stats["min_seconds"] <= 0.07, f"Min time was {op_stats['min_seconds']}"
    assert 0.13 <= op_stats["max_seconds"] <= 0.17, f"Max time was {op_stats['max_seconds']}"
