"""
Tests for the parallel processing utility
"""

import pytest
import time
import random
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

from textcleaner.utils.parallel import ParallelProcessor, ParallelResult


def slow_function(item: int) -> int:
    """A deliberately slow function to test parallel processing"""
    # Sleep for a random amount of time to simulate varying processing times
    time.sleep(0.01 + random.random() * 0.02)
    return item * 2


def failing_function(item: int) -> int:
    """A function that fails for certain inputs"""
    if item % 5 == 0:
        raise ValueError(f"Simulated failure for item {item}")
    return item * 2


@pytest.fixture
def parallel_processor():
    """Create a ParallelProcessor instance for testing"""
    return ParallelProcessor()


def test_process_items_threads(parallel_processor):
    """Test processing items with threads"""
    # Create test items
    items = list(range(10))
    
    # Process items with threads
    results = parallel_processor.process_items(
        items=items,
        process_func=slow_function,
        use_processes=False
    )
    
    # Verify results
    assert len(results) == len(items)
    assert all(task.success for task in results)
    
    # Sort results by task_id to match original order
    sorted_results = sorted(results, key=lambda r: int(r.task_id.split('_')[1]))
    assert [task.result for task in sorted_results] == [item * 2 for item in items]


def test_process_items_processes(parallel_processor):
    """Test processing items with processes"""
    # Create test items
    items = list(range(10))
    
    # Process items with processes
    results = parallel_processor.process_items(
        items=items,
        process_func=slow_function,
        use_processes=True
    )
    
    # Verify results
    assert len(results) == len(items)
    assert all(task.success for task in results)
    
    # Sort results by task_id to match original order
    sorted_results = sorted(results, key=lambda r: int(r.task_id.split('_')[1]))
    assert [task.result for task in sorted_results] == [item * 2 for item in items]


def test_handle_exceptions(parallel_processor):
    """Test handling exceptions in worker functions"""
    # Create test items
    items = list(range(10))
    
    # Process items with a function that fails for some inputs
    results = parallel_processor.process_items(
        items=items,
        process_func=failing_function
    )
    
    # Verify results
    assert len(results) == len(items)
    
    # Check which tasks succeeded and which failed
    for i, task in enumerate(results):
        if i % 5 == 0:
            assert not task.success, f"Task {i} should have failed"
            assert "Simulated failure" in task.error, f"Unexpected error for task {i}: {task.error}"
        else:
            assert task.success, f"Task {i} should have succeeded"
            assert task.result == i * 2, f"Unexpected result for task {i}: {task.result}"


def test_max_workers(parallel_processor):
    """Test setting maximum workers"""
    # Create large number of items
    items = list(range(30))
    
    # Track active workers
    max_active_workers = [0]
    active_workers = [0]
    
    def monitored_work(item):
        """Function that monitors concurrency"""
        # Increment active worker count
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(lambda: active_workers[0] + 1)
            active_workers[0] = future.result()
        
        # Update max workers seen
        max_active_workers[0] = max(max_active_workers[0], active_workers[0])
        
        # Do some work
        time.sleep(0.05)
        
        # Decrement active worker count
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(lambda: active_workers[0] - 1)
            active_workers[0] = future.result()
        
        return item
    
    # Process with limited workers
    max_workers = 5
    limited_processor = ParallelProcessor(max_workers=max_workers)
    limited_processor.process_items(
        items=items,
        process_func=monitored_work
    )
    
    # Verify max concurrent workers did not exceed the limit
    assert max_active_workers[0] <= max_workers, f"Expected max {max_workers} workers, but saw {max_active_workers[0]}"


def test_task_ids(parallel_processor):
    """Test using task IDs"""
    # Create test items
    items = list(range(5))
    task_ids = [f"task_{i}" for i in items]
    
    # Process items with task IDs
    results = parallel_processor.process_items(
        items=items,
        process_func=slow_function,
        task_ids=task_ids
    )
    
    # Verify results
    assert len(results) == len(items)
    
    # Check task IDs were preserved
    for i, task in enumerate(results):
        assert task.task_id == task_ids[i], f"Task ID mismatch for task {i}"


def test_complex_items(parallel_processor):
    """Test processing complex items like tuples"""
    # Create complex items (tuples)
    items = [(i, i*10) for i in range(5)]
    
    def process_tuple(item: Tuple[int, int]) -> int:
        return item[0] + item[1]
    
    # Process tuple items
    results = parallel_processor.process_items(
        items=items,
        process_func=process_tuple
    )
    
    # Verify results
    assert len(results) == len(items)
    assert all(task.success for task in results)
    assert [task.result for task in results] == [i + (i*10) for i in range(5)]


def test_result_order(parallel_processor):
    """Test that results are returned in the same order as inputs"""
    # Create items that would complete in reverse order if not synchronized
    items = list(range(10))
    
    def reverse_timing_function(item):
        # Items with higher values complete faster
        time.sleep(0.05 * (10 - item) / 10)
        return item
    
    # Process items
    results = parallel_processor.process_items(
        items=items,
        process_func=reverse_timing_function
    )
    
    # Verify results are in the original order
    assert [task.result for task in results] == items


def test_empty_items(parallel_processor):
    """Test processing an empty list"""
    # Process empty list
    results = parallel_processor.process_items(
        items=[],
        process_func=slow_function
    )
    
    # Verify empty results
    assert len(results) == 0


def test_very_large_input(parallel_processor):
    """Test processing a large number of items efficiently"""
    # Skip this test in normal runs to avoid long test times
    pytest.skip("Skipping large input test for normal test runs")
    
    # Create a large number of items
    items = list(range(1000))
    
    # Process items
    start_time = time.time()
    results = parallel_processor.process_items(
        items=items,
        process_func=lambda x: x * 2
    )
    end_time = time.time()
    
    # Verify all processed correctly
    assert len(results) == len(items)
    assert all(task.success for task in results)
    assert [task.result for task in results] == [item * 2 for item in items]
    
    # Performance check - should be much faster than sequential
    elapsed = end_time - start_time
    print(f"Processed 1000 items in {elapsed:.2f} seconds")
    
    # Sequential timing for comparison
    start_time = time.time()
    sequential_results = [slow_function(item) for item in items]
    sequential_elapsed = time.time() - start_time
    
    print(f"Sequential processing: {sequential_elapsed:.2f} seconds")
    print(f"Parallel speedup: {sequential_elapsed/elapsed:.1f}x")
