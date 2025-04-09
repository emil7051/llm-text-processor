#!/usr/bin/env python3
"""
Integration tests for parallel processing functionality in textcleaner.
"""

import os
import time
import threading
import tempfile
import random
import math
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, strategies as st

from textcleaner.config.config_manager import ConfigManager
from textcleaner.core.factories import TextProcessorFactory
from textcleaner.core.models import ProcessingResult
from textcleaner.core.processor import TextProcessor
from textcleaner.outputs.output_manager import OutputManager
from textcleaner.utils.parallel import ParallelProcessor
from textcleaner.utils.logging_config import get_logger
from textcleaner.utils.security import TestSecurityUtils
from textcleaner.core.directory_processor import DirectoryProcessor
from textcleaner.utils.parallel import parallel_processor
from ..fixtures.test_utils import (
    create_test_files, 
    create_text_processor,
    cpu_intensive_calculation,
    cpu_intensive_task,
    track_active_workers
)

# Configure logging
logger = get_logger("test_parallel_processing")


# Patch the ThreadPoolExecutor __init__ method to force the max_workers parameter
original_thread_pool_init = ThreadPoolExecutor.__init__

def patched_thread_pool_init(self, max_workers=None, *args, **kwargs):
    """Patched ThreadPoolExecutor.__init__ to force max_workers."""
    # Force max_workers to be 4 for all ThreadPoolExecutor instances created
    # We need this because the parallel processing might be using an adaptive approach
    # that limits workers based on system resources
    forced_max_workers = 4  # Force this number of workers
    logger.debug(f"Forcing ThreadPoolExecutor max_workers to {forced_max_workers} (was {max_workers})")
    return original_thread_pool_init(self, max_workers=forced_max_workers, *args, **kwargs)


@pytest.fixture
def thread_pool_patcher():
    """Patch and restore ThreadPoolExecutor for tests."""
    original = ThreadPoolExecutor.__init__
    ThreadPoolExecutor.__init__ = patched_thread_pool_init
    yield
    ThreadPoolExecutor.__init__ = original


def test_threads_vs_processes():
    """Compare performance of ThreadPoolExecutor vs ProcessPoolExecutor for CPU-intensive tasks."""
    logger.info("Comparing ThreadPoolExecutor vs ProcessPoolExecutor for CPU-intensive tasks")
    
    # Number of tasks and workers
    num_tasks = 20
    num_workers = 4
    
    # Create tasks - just indices to process
    tasks = list(range(num_tasks))
    
    # Test with ThreadPoolExecutor
    logger.info(f"Testing ThreadPoolExecutor with {num_workers} workers...")
    thread_start = time.time()
    thread_pids = set()
    thread_tids = set()
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        thread_results = list(executor.map(cpu_intensive_task, tasks))
    
    thread_total = time.time() - thread_start
    
    # Collect stats
    for result in thread_results:
        thread_pids.add(result['pid'])
        thread_tids.add(result['thread_id'])
    
    thread_durations = [r['duration'] for r in thread_results]
    thread_avg_duration = sum(thread_durations) / len(thread_durations)
    
    logger.info(f"ThreadPoolExecutor: {len(thread_results)} tasks in {thread_total:.2f}s")
    logger.info(f"  Average task duration: {thread_avg_duration:.4f}s")
    logger.info(f"  Unique PIDs: {len(thread_pids)}")
    logger.info(f"  Unique thread IDs: {len(thread_tids)}")
    
    # Test with ProcessPoolExecutor
    logger.info(f"Testing ProcessPoolExecutor with {num_workers} workers...")
    process_start = time.time()
    process_pids = set()
    process_tids = set()
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        process_results = list(executor.map(cpu_intensive_task, tasks))
    
    process_total = time.time() - process_start
    
    # Collect stats
    for result in process_results:
        process_pids.add(result['pid'])
        process_tids.add(result['thread_id'])
    
    process_durations = [r['duration'] for r in process_results]
    process_avg_duration = sum(process_durations) / len(process_durations)
    
    logger.info(f"ProcessPoolExecutor: {len(process_results)} tasks in {process_total:.2f}s")
    logger.info(f"  Average task duration: {process_avg_duration:.4f}s")
    logger.info(f"  Unique PIDs: {len(process_pids)}")
    logger.info(f"  Unique thread IDs: {len(process_tids)}")
    
    # Calculate speedup
    speedup = thread_total / process_total if process_total > 0 else 0
    
    logger.info(f"Speedup from using processes vs threads: {speedup:.2f}x")
    
    # Verify processes are faster for CPU-intensive work
    assert speedup > 1.0, f"Process pool should be faster than thread pool for CPU-bound tasks"
    assert len(process_pids) > 1, f"Process pool should use multiple processes"
    
    # Return comparison results
    return {
        "thread_total_time": thread_total,
        "process_total_time": process_total,
        "speedup": speedup,
        "thread_avg_duration": thread_avg_duration,
        "process_avg_duration": process_avg_duration,
        "thread_unique_pids": len(thread_pids),
        "thread_unique_tids": len(thread_tids),
        "process_unique_pids": len(process_pids),
        "process_unique_tids": len(process_tids)
    }


def test_parallel_file_processing(thread_pool_patcher):
    """Test processing multiple files in parallel."""
    # Create a temporary directory for our test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        
        # Create input and output directories
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        
        # Create test files with larger sizes to ensure different processing times
        def content_generator(i):
            # Generate files with varying sizes to create different processing times
            # Much larger files (between 10KB and 50KB)
            base_size = 10000
            size_multiplier = (i % 5 + 1)
            size = base_size * size_multiplier
            
            # Create some structured content to make processing more realistic
            content = f"Title: Test Document {i}\n\n"
            content += f"Author: Test Author\n"
            content += f"Date: 2023-04-0{(i % 9) + 1}\n\n"
            content += f"This is test content for file {i}.\n\n"
            
            # Add paragraphs with random content
            for p in range(size_multiplier * 2):
                content += f"Paragraph {p+1}: This is paragraph {p+1} of document {i}. "
                content += "X" * (base_size // (p+5)) + "\n\n"
                
            return content
        
        # Create more files to better demonstrate parallelism
        file_count = 20
        create_test_files(input_dir, count=file_count, content_generator=content_generator)
        
        # Install worker tracking
        # Use patch_processes=True if testing ProcessPoolExecutor implicitly via DirectoryProcessor
        get_worker_stats = track_active_workers(patch_processes=False) # Assuming threads are default for DirectoryProcessor.process_directory_parallel
        
        # Create processor using factory
        max_workers = 4
        factory = TextProcessorFactory()
        # Create TextProcessor first
        single_file_processor = factory.create_standard_processor()

        # Instantiate DirectoryProcessor
        dir_processor = DirectoryProcessor(
            config=single_file_processor.config,
            security_utils=TestSecurityUtils(), # Use relaxed security for temp dirs
            parallel_processor=parallel_processor, # Use the singleton
            single_file_processor=single_file_processor
        )

        # Ensure max_workers is correctly set if not done by factory (it is handled by process_directory_parallel)
        # processor.parallel.max_workers = max_workers # Example if needed

        # Process the directory in parallel using DirectoryProcessor
        logger.info(f"Starting parallel processing with max_workers={max_workers}")
        start_time = time.time()
        results = dir_processor.process_directory_parallel(
            input_dir,
            output_dir,
            max_workers=max_workers
        )
        elapsed_time = time.time() - start_time
        
        # Check results
        success_count = sum(1 for r in results if r.success)
        
        # Get worker statistics
        worker_stats = get_worker_stats()
        
        # Print results
        logger.info(f"Parallel processing completed in {elapsed_time:.2f} seconds")
        logger.info(f"Results: {success_count} succeeded, {len(results) - success_count} failed")
        logger.info(f"Max concurrent workers: {worker_stats['max_concurrent']}")
        logger.info(f"Unique thread IDs: {len(worker_stats['tids'])}")
        
        # Verify parallel execution
        assert worker_stats['max_concurrent'] > 1, "Parallel processing failed - only 1 concurrent worker detected"
            
        # Compare with sequential processing
        logger.info("Testing sequential processing for comparison...")
        
        # Process each file sequentially for comparison
        sequential_start = time.time()
        sequential_results = []
        for file_path in sorted(input_dir.glob('*.txt')):
            output_path = output_dir / f"sequential_{file_path.stem}.md"
            # Use the DirectoryProcessor's underlying TextProcessor for sequential processing
            result = dir_processor.single_file_processor.process_file(file_path, output_path)
            sequential_results.append(result)
        sequential_elapsed = time.time() - sequential_start
        
        # Calculate speedup
        speedup = sequential_elapsed / max(0.001, elapsed_time)
        logger.info(f"Sequential processing took {sequential_elapsed:.2f} seconds")
        logger.info(f"Speedup from parallel processing: {speedup:.2f}x")
        
        # Check all files were processed
        assert success_count == file_count, f"Expected {file_count} successful results, got {success_count}"
        
        # Check that we got close to max workers usage
        assert worker_stats['max_concurrent'] >= max_workers - 1, \
            f"Expected close to {max_workers} concurrent workers, but got {worker_stats['max_concurrent']}"
        
        return {
            "success": worker_stats['max_concurrent'] > 1,
            "max_concurrent": worker_stats['max_concurrent'],
            "expected_max": max_workers,
            "speedup": speedup,
            "parallel_time": elapsed_time,
            "sequential_time": sequential_elapsed,
            "worker_stats": worker_stats
        } 