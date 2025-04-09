"""
Performance monitoring tests for the LLM Text Processor
"""

import pytest
import time
from pathlib import Path
import json
import shutil

from textcleaner.core.factories import TextProcessorFactory
from textcleaner.utils.performance import performance_monitor
from textcleaner.utils.security import TestSecurityUtils
from textcleaner.core.processor import TextProcessor
from textcleaner.core.directory_processor import DirectoryProcessor
from textcleaner.utils.parallel import parallel_processor
from textcleaner.utils.logging_config import get_logger

logger = get_logger("test_performance")

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


@pytest.fixture
def create_test_docs(temp_directory):
    input_dir = temp_directory / "perf_input"
    input_dir.mkdir()
    # Create some sample files
    for i in range(5): # Example: create 5 files
        file_path = input_dir / f"doc_{i}.txt"
        with open(file_path, "w") as f:
            f.write(f"Content for doc {i}. " * 100)
    return input_dir


def test_performance_monitoring_integration(sample_large_text_file, temp_directory, reset_performance_monitor):
    """Test that performance monitoring integrates with text processing"""
    output_file = temp_directory / "performance_output.md"
    
    # Create processor
    factory = TextProcessorFactory()
    processor = factory.create_processor(config_type="aggressive")
    processor.security = TestSecurityUtils()
    
    # Process the file
    result = processor.process_file(sample_large_text_file, output_file)
    
    # Verify successful processing
    assert result.success, f"Processing failed: {result.error}"
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


def test_parallel_vs_sequential_performance(create_test_docs, temp_directory):
    """Compare performance of parallel vs. sequential processing."""
    input_dir = create_test_docs
    
    # Create TextProcessorFactory
    factory = TextProcessorFactory()
    
    # Create DirectoryProcessor for sequential processing
    sequential_dir = temp_directory / "sequential_output"
    sequential_dir.mkdir()
    single_file_processor_seq = factory.create_standard_processor()
    processor_seq = DirectoryProcessor(
        config=single_file_processor_seq.config,
        security_utils=TestSecurityUtils(),
        parallel_processor=parallel_processor,
        single_file_processor=single_file_processor_seq
    )
    
    logger.info("Starting sequential processing...")
    start_seq = time.time()
    processor_seq.process_directory(input_dir, sequential_dir)
    time_seq = time.time() - start_seq
    logger.info(f"Sequential processing took {time_seq:.2f} seconds.")
    
    # Create DirectoryProcessor for parallel processing
    parallel_dir = temp_directory / "parallel_output"
    parallel_dir.mkdir()
    single_file_processor_par = factory.create_standard_processor()
    processor_par = DirectoryProcessor(
        config=single_file_processor_par.config,
        security_utils=TestSecurityUtils(),
        parallel_processor=parallel_processor,
        single_file_processor=single_file_processor_par
    )
    
    logger.info("Starting parallel processing...")
    start_par = time.time()
    processor_par.process_directory_parallel(input_dir, parallel_dir, max_workers=4)
    time_par = time.time() - start_par
    logger.info(f"Parallel processing took {time_par:.2f} seconds.")
    
    # Compare
    assert time_par < time_seq or time_seq < 0.1, \
        f"Parallel ({time_par:.2f}s) should be faster than sequential ({time_seq:.2f}s), unless sequential is very fast."
    if time_par > 0:
        logger.info(f"Speedup factor: {time_seq / time_par:.2f}x")
    else:
        logger.info("Parallel processing was too fast to calculate speedup.")
    
    # Clean up output directories
    shutil.rmtree(sequential_dir)
    shutil.rmtree(parallel_dir)


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
