#!/usr/bin/env python3
"""
Common utilities for textcleaner tests.
"""

import os
import time
import threading
import tempfile
import random
import math
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from textcleaner.core.processor import TextProcessor
from textcleaner.utils.parallel import ParallelProcessor, ParallelResult
from textcleaner.utils.logging_config import get_logger
from textcleaner.config.config_manager import ConfigManager
from textcleaner.utils.file_utils import get_supported_extensions
from textcleaner.utils.security import TestingSecurityUtils
from textcleaner.utils.log_utils import ProcessingLogger

# Configure logging
logger = get_logger("test_utils")


def create_test_files(directory, count=10, content_generator=None):
    """Create test text files in the specified directory."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    
    created_files = []
    
    for i in range(count):
        file_path = directory / f"test_file_{i}.txt"
        
        # Generate content with file index to make each file unique
        if content_generator:
            content = content_generator(i)
        else:
            content = f"Test file {i}\nLine 1\nLine 2\nThis is test content for file {i}.\n"
            
        with open(file_path, "w") as f:
            f.write(content)
        
        created_files.append(file_path)
    
    logger.info(f"Created {len(created_files)} test files in {directory}")
    return created_files


def create_text_processor(max_workers=None):
    """Create a configured TextProcessor instance."""
    # Create with TestSecurityUtils for testing in temp directories
    security = TestingSecurityUtils()
    
    # Create with default configuration and test security utils
    processor = TextProcessor(
        config_type="standard",
        security_utils=security
    )
    
    # Override parallel processor if max_workers specified
    if max_workers is not None:
        processor.parallel = ParallelProcessor(max_workers=max_workers)
    
    return processor


def cpu_intensive_calculation(iterations=1000000):
    """A CPU-intensive function to simulate real processing work."""
    result = 0
    for i in range(iterations):
        result += math.sin(random.random() * math.pi) * math.sin(random.random() * math.pi)
    return result


# This function needs to be at module level for ProcessPoolExecutor to work
def cpu_intensive_task(n):
    """Function to perform CPU-intensive work, must be top-level for pickling."""
    # Do CPU-intensive calculation that will be affected by GIL
    start_time = time.time()
    result = cpu_intensive_calculation(1000000)  # 1M iterations
    duration = time.time() - start_time
    return {
        'task_id': n,
        'result': result,
        'duration': duration,
        'pid': os.getpid(),
        'thread_id': threading.get_ident()
    }


# Global dictionary to hold worker tracking state (necessary for multiprocessing)
# This allows state to be shared/updated by the top-level function
worker_tracking_state = {
    'active_workers': 0,
    'max_concurrent_workers': 0,
    'worker_pid_set': set(),
    'worker_tid_set': set(),
    'worker_lock': threading.Lock(), # Note: Lock might not be effective across processes
    'worker_timestamps': []
}

# Top-level function for pickling compatibility
def _instrumented_execute_top_level(func, item, task_id, original_index=None):
    """Top-level instrumented execute function for pickling."""
    global worker_tracking_state

    state = worker_tracking_state
    worker_lock = state['worker_lock']
    start_time = time.time()
    worker_id = f"{os.getpid()}-{threading.get_ident()}"
    result_value = None
    error_value = None
    success_flag = False

    # --- Start Tracking ---    
    with worker_lock: 
        state['active_workers'] += 1
        state['max_concurrent_workers'] = max(state['max_concurrent_workers'], state['active_workers'])
        state['worker_pid_set'].add(os.getpid())
        state['worker_tid_set'].add(threading.get_ident())
        
        state['worker_timestamps'].append({
            'event': 'start',
            'time': start_time,
            'worker_id': worker_id,
            'task_id': task_id,
            'active_count': state['active_workers']
        })
        logger.debug(f"Worker started: {worker_id} "
                     f"(active={state['active_workers']}, max={state['max_concurrent_workers']})")

    # --- Execute Original Function --- 
    try:
        # Simulating CPU work (same as before)
        file_pair = item
        if isinstance(file_pair, tuple) and len(file_pair) == 2:
            input_file = file_pair[0]
            if isinstance(input_file, Path) and input_file.is_file():
                try:
                    file_number = int(input_file.stem.split('_')[-1])
                    iterations = 500000 + (file_number % 5) * 500000
                    cpu_intensive_calculation(iterations)
                except (ValueError, IndexError):
                    cpu_intensive_calculation(1000000)
        
        # Call the target function
        result_value = func(item)
        success_flag = True
    except Exception as e:
        error_value = str(e)
        logger.error(f"Error in instrumented task {task_id}: {e}")
    finally:
        # --- End Tracking --- 
        end_time = time.time()
        with worker_lock: 
            state['active_workers'] -= 1
            state['worker_timestamps'].append({
                'event': 'end',
                'time': end_time,
                'worker_id': worker_id,
                'task_id': task_id,
                'active_count': state['active_workers'],
                'duration': end_time - start_time
            })
            logger.debug(f"Worker finished: {worker_id} "
                         f"(active={state['active_workers']})")

    # --- Return ParallelResult --- 
    # Mimic the structure expected by ParallelProcessor
    return ParallelResult(
        task_id=task_id,
        result=result_value,
        success=success_flag,
        input_item=item,
        error=error_value,
        processing_time=(end_time - start_time),
        metadata={'original_index': original_index}, # Include original index
        start_time=start_time,
        end_time=end_time,
        worker_id=worker_id # Store worker_id if needed
    )

def track_active_workers(patch_processes=False): # Added parameter
    """Global worker tracking for monitoring parallel execution."""
    global worker_tracking_state
    # Reset state at the beginning of tracking
    worker_tracking_state = {
        'active_workers': 0,
        'max_concurrent_workers': 0,
        'worker_pid_set': set(),
        'worker_tid_set': set(),
        'worker_lock': threading.Lock(), 
        'worker_timestamps': []
    }
    
    # Store the original method before patching
    original_execute_method = ParallelProcessor._execute_task_with_tracking
    
    # Apply the patch ONLY if patch_processes is True (or implicitly for threads)
    # Note: This assumes the method being patched is suitable for both threads/processes
    # If multiprocessing is used, the top-level function is needed.
    if patch_processes:
        # For processes, patch with the top-level function
        ParallelProcessor._execute_task_with_tracking = staticmethod(_instrumented_execute_top_level)
        logger.info("Patching ParallelProcessor for process tracking (using top-level function).")
    else:
        # For threads (default), we can potentially use a nested function if needed,
        # but let's stick to the top-level one for consistency for now.
        # This part might need refinement depending on thread vs process behavior.
        ParallelProcessor._execute_task_with_tracking = staticmethod(_instrumented_execute_top_level)
        logger.info("Patching ParallelProcessor for thread tracking (using top-level function).")

    # Return a function that provides the worker statistics using the global state
    def get_stats():
        global worker_tracking_state
        # Restore the original method when stats are retrieved (optional)
        # ParallelProcessor._execute_task_with_tracking = original_execute_method
        return {
            "max_concurrent": worker_tracking_state['max_concurrent_workers'],
            "unique_pids": len(worker_tracking_state['worker_pid_set']),
            "unique_threads": len(worker_tracking_state['worker_tid_set']),
            "pids": list(worker_tracking_state['worker_pid_set']),
            "tids": list(worker_tracking_state['worker_tid_set']),
            "worker_timeline": worker_tracking_state['worker_timestamps']
        }
    return get_stats 