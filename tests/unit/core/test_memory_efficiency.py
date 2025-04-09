"""
Memory efficiency tests for the LLM Text Processor
"""

import os
import sys
import tempfile
import time
import gc
from pathlib import Path
import resource
import pytest

from textcleaner.core.factories import TextProcessorFactory
from textcleaner.utils.performance import performance_monitor


def get_memory_usage():
    """Get the current memory usage in MB"""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


@pytest.fixture
def large_text_file():
    """Create a large text file for memory testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        # Write a 10MB text file
        chunk_size = 1024 * 10  # 10KB chunks
        chunk = "This is a test line for memory efficiency testing.\n" * 200
        
        # Write ~10MB of data in chunks
        for _ in range(100):
            f.write(chunk)
        
        file_path = f.name
    
    yield Path(file_path)
    
    # Cleanup
    try:
        os.unlink(file_path)
    except:
        pass


@pytest.mark.memory
def test_memory_usage_consistency(large_text_file, temp_directory):
    """Test that memory usage remains relatively consistent during processing"""
    # Create output path
    output_path = temp_directory / "memory_test_output.md"
    
    # Create processor with standard configuration
    factory = TextProcessorFactory()
    processor = factory.create_processor()
    
    # Force garbage collection before test
    gc.collect()
    
    # Measure baseline memory
    baseline_memory = get_memory_usage()
    
    # Process file
    processor.process_file(large_text_file, output_path)
    
    # Force garbage collection again
    gc.collect()
    
    # Measure memory after processing
    end_memory = get_memory_usage()
    
    # Calculate memory increase
    memory_increase = end_memory - baseline_memory
    
    # Log memory usage information
    print(f"Baseline memory: {baseline_memory:.2f} MB")
    print(f"End memory: {end_memory:.2f} MB")
    print(f"Memory increase: {memory_increase:.2f} MB")
    
    # Check that memory increase is reasonable
    # Memory increase should be proportional to the file size but not excessive
    # This test needs tuning based on actual implementation
    file_size_mb = os.path.getsize(large_text_file) / (1024 * 1024)
    
    # The memory increase should be less than 5x the file size
    # This is a very generous limit that should be tightened based on actual performance
    assert memory_increase < (file_size_mb * 5), f"Memory usage increased by {memory_increase:.2f} MB for a {file_size_mb:.2f} MB file"


@pytest.mark.memory
def test_multiple_file_processing_memory(temp_directory):
    """Test memory behavior when processing multiple files in sequence"""
    # Create multiple files for testing
    file_paths = []
    for i in range(5):
        file_path = temp_directory / f"mem_test_{i}.txt"
        with open(file_path, "w") as f:
            # Each file is ~1MB
            chunk = "This is a test line for memory efficiency testing.\n" * 200
            for _ in range(10):
                f.write(chunk)
        file_paths.append(file_path)
    
    # Create output directory
    output_dir = temp_directory / "memory_test_output"
    output_dir.mkdir()
    
    # Create processor
    factory = TextProcessorFactory()
    processor = factory.create_processor()
    
    # Force garbage collection
    gc.collect()
    
    # Measure starting memory
    start_memory = get_memory_usage()
    
    # Process each file in sequence
    for i, file_path in enumerate(file_paths):
        output_path = output_dir / f"output_{i}.md"
        processor.process_file(file_path, output_path)
        
        # For every other file, force garbage collection to check memory reclamation
        if i % 2 == 0:
            gc.collect()
    
    # Force final garbage collection
    gc.collect()
    
    # Measure end memory
    end_memory = get_memory_usage()
    
    # Calculate total memory increase
    memory_increase = end_memory - start_memory
    
    # Log memory usage information
    print(f"Start memory: {start_memory:.2f} MB")
    print(f"End memory after processing 5 files: {end_memory:.2f} MB")
    print(f"Total memory increase: {memory_increase:.2f} MB")
    
    # Check memory growth behavior
    # Memory should not grow linearly with the number of files processed
    # This indicates proper cleanup between file processing
    total_size_mb = sum(os.path.getsize(f) for f in file_paths) / (1024 * 1024)
    
    # The memory increase should be less than 2x the largest file size
    # since memory should be reclaimed between files
    largest_file_size = max(os.path.getsize(f) for f in file_paths) / (1024 * 1024)
    
    assert memory_increase < (largest_file_size * 2), \
        f"Memory grew excessively when processing multiple files. Increase: {memory_increase:.2f} MB"
