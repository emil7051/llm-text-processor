"""Enhanced parallel processing utilities for the LLM Text Processor."""

import os
import time
# import signal # Unused
# import platform # Unused
import psutil
import concurrent.futures
# import queue # Unused
import threading
# from pathlib import Path # Unused
from typing import List, Callable, TypeVar, Any, Dict, Optional, Union, Tuple, Iterator # Generic unused
from dataclasses import dataclass, field

from textcleaner.utils.logging_config import get_logger
from textcleaner.utils.performance import performance_monitor

# Type variables for generic functions
T = TypeVar('T')  # Input type
R = TypeVar('R')  # Result type


@dataclass
class ParallelResult(Generic[T, R]):
    """Result of a parallel processing operation with enhanced metadata."""
    task_id: str
    result: R
    success: bool
    input_item: T
    error: Optional[str] = None
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    worker_id: Optional[str] = None
    memory_usage: Optional[float] = None  # Memory usage in MB


class ProgressTracker:
    """Tracks progress of parallel processing tasks."""
    
    def __init__(self, total_items: int, update_interval: float = 0.5):
        """Initialize progress tracker.
        
        Args:
            total_items: Total number of items to process
            update_interval: How often to update progress (in seconds)
        """
        self.logger = get_logger(__name__)
        self.total = total_items
        self.completed = 0
        self.failed = 0
        self.in_progress = 0
        self.update_interval = update_interval
        self.start_time = time.time()
        self.last_update_time = 0
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self._progress_thread = None
        self.estimated_time_remaining = None
        self.callbacks = []
    
    def start(self):
        """Start the progress tracker."""
        if self._progress_thread is None and self.total > 0:
            self._stop_event.clear()
            self._progress_thread = threading.Thread(target=self._update_progress)
            self._progress_thread.daemon = True
            self._progress_thread.start()
    
    def stop(self):
        """Stop the progress tracker."""
        if self._progress_thread is not None:
            self._stop_event.set()
            self._progress_thread.join(timeout=1.0)
            self._progress_thread = None
    
    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a callback function to be called on progress updates.
        
        Args:
            callback: Function that takes a progress dictionary as input
        """
        self.callbacks.append(callback)
    
    def item_started(self):
        """Mark an item as started."""
        with self.lock:
            self.in_progress += 1
    
    def item_completed(self, success: bool = True):
        """Mark an item as completed.
        
        Args:
            success: Whether the item was processed successfully
        """
        with self.lock:
            self.in_progress -= 1
            if success:
                self.completed += 1
            else:
                self.failed += 1
    
    def get_progress(self) -> Dict[str, Any]:
        """Get the current progress information.
        
        Returns:
            Dictionary with progress information
        """
        with self.lock:
            elapsed = time.time() - self.start_time
            
            # Calculate processing rate (items per second)
            rate = (self.completed + self.failed) / max(elapsed, 0.001)
            
            # Estimate time remaining
            remaining_items = self.total - (self.completed + self.failed)
            estimated_seconds = remaining_items / max(rate, 0.001) if rate > 0 else 0
            
            # Format time remaining
            if estimated_seconds < 60:
                estimated_time = f"{estimated_seconds:.1f} seconds"
            elif estimated_seconds < 3600:
                estimated_time = f"{estimated_seconds/60:.1f} minutes"
            else:
                estimated_time = f"{estimated_seconds/3600:.1f} hours"
            
            return {
                "total": self.total,
                "completed": self.completed,
                "failed": self.failed,
                "in_progress": self.in_progress,
                "percent_complete": (self.completed + self.failed) / max(self.total, 1) * 100,
                "elapsed_seconds": elapsed,
                "items_per_second": rate,
                "estimated_time_remaining": estimated_time,
                "success_rate": self.completed / max(self.completed + self.failed, 1) * 100
            }
    
    def _update_progress(self):
        """Update and log progress at regular intervals."""
        while not self._stop_event.is_set():
            now = time.time()
            if now - self.last_update_time >= self.update_interval:
                progress = self.get_progress()
                
                # Log progress
                self.logger.info(
                    f"Progress: {progress['percent_complete']:.1f}% "
                    f"({progress['completed']} completed, {progress['failed']} failed, "
                    f"{progress['in_progress']} in progress) - "
                    f"ETA: {progress['estimated_time_remaining']}"
                )
                
                # Call any registered callbacks
                for callback in self.callbacks:
                    try:
                        callback(progress)
                    except Exception as e:
                        self.logger.error(f"Error in progress callback: {e}")
                
                self.last_update_time = now
            
            # Sleep briefly
            time.sleep(0.1)


class ResourceMonitor:
    """Monitors system resources during parallel processing."""
    
    def __init__(self, check_interval: float = 2.0, memory_threshold: float = 85.0):
        """Initialize resource monitor.
        
        Args:
            check_interval: How often to check resource usage (in seconds)
            memory_threshold: Memory usage threshold (percentage) to trigger alerts
        """
        self.logger = get_logger(__name__)
        self.check_interval = check_interval
        self.memory_threshold = memory_threshold
        self._stop_event = threading.Event()
        self._monitor_thread = None
        self.peak_memory_percent = 0.0
        self.peak_cpu_percent = 0.0
        self.throttle_event = threading.Event()
    
    def start(self):
        """Start resource monitoring."""
        if self._monitor_thread is None:
            self._stop_event.clear()
            self.throttle_event.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_resources)
            self._monitor_thread.daemon = True
            self._monitor_thread.start()
    
    def stop(self):
        """Stop resource monitoring."""
        if self._monitor_thread is not None:
            self._stop_event.set()
            self._monitor_thread.join(timeout=1.0)
            self._monitor_thread = None
    
    def should_throttle(self) -> bool:
        """Check if processing should be throttled due to resource constraints."""
        return self.throttle_event.is_set()
    
    def _monitor_resources(self):
        """Monitor system resources and log/throttle as needed."""
        while not self._stop_event.is_set():
            try:
                # Get memory usage
                memory_info = psutil.virtual_memory()
                memory_percent = memory_info.percent
                
                # Get CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.5)
                
                # Update peak values
                self.peak_memory_percent = max(self.peak_memory_percent, memory_percent)
                self.peak_cpu_percent = max(self.peak_cpu_percent, cpu_percent)
                
                # Log resource usage at regular intervals
                self.logger.debug(
                    f"Resource usage - Memory: {memory_percent:.1f}% "
                    f"(Peak: {self.peak_memory_percent:.1f}%), "
                    f"CPU: {cpu_percent:.1f}% (Peak: {self.peak_cpu_percent:.1f}%)"
                )
                
                # Check if memory usage is above threshold
                if memory_percent > self.memory_threshold:
                    if not self.throttle_event.is_set():
                        self.logger.warning(
                            f"High memory usage detected ({memory_percent:.1f}%), "
                            f"throttling parallel processing"
                        )
                        self.throttle_event.set()
                else:
                    # If we were throttling and memory has gone down, remove throttle
                    if self.throttle_event.is_set() and memory_percent < (self.memory_threshold - 5):
                        self.logger.info(
                            f"Memory usage decreased ({memory_percent:.1f}%), "
                            f"resuming normal processing"
                        )
                        self.throttle_event.clear()
            
            except Exception as e:
                self.logger.error(f"Error in resource monitoring: {e}")
            
            # Sleep until next check
            time.sleep(self.check_interval)
    
    def get_resource_stats(self) -> Dict[str, float]:
        """Get current resource usage statistics.
        
        Returns:
            Dictionary with resource statistics
        """
        try:
            memory_info = psutil.virtual_memory()
            
            return {
                "memory_percent": memory_info.percent,
                "peak_memory_percent": self.peak_memory_percent,
                "memory_available_mb": memory_info.available / (1024 * 1024),
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "peak_cpu_percent": self.peak_cpu_percent
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.logger.warning(f"psutil error getting resource stats: {e}")
            return {}
        except Exception as e:
            self.logger.exception(f"Unexpected error getting resource stats: {e}") # Log with traceback
            return {}


class ParallelProcessor:
    """Enhanced utility for processing items in parallel with progress tracking and resource management."""
    
    def __init__(self, max_workers: Optional[int] = None, 
                 adaptive_workers: bool = True,
                 min_workers: int = 2):
        """Initialize the parallel processor.
        
        Args:
            max_workers: Maximum number of worker threads/processes to use.
                         If None, defaults to number of CPU cores.
            adaptive_workers: Whether to adapt the number of workers based on system load
            min_workers: Minimum number of workers to use when adapting
        """
        self.logger = get_logger(__name__)
        
        # Determine optimal number of workers
        cpu_count = os.cpu_count() or 4
        self.max_workers = max_workers or max(2, min(32, cpu_count))
        self.min_workers = min(min_workers, self.max_workers)
        self.adaptive_workers = adaptive_workers
        
        # Create resource monitor
        self.resource_monitor = ResourceMonitor()
        
        self.logger.info(
            f"Initialized parallel processor with {self.max_workers} max workers "
            f"(adaptive: {self.adaptive_workers})"
        )
    
    def _get_worker_count(self) -> int:
        """Determine the optimal number of workers based on system resources.
        
        Returns:
            Number of worker threads/processes to use
        """
        if not self.adaptive_workers:
            return self.max_workers
        
        # Check if we're throttling due to resource constraints
        if self.resource_monitor.should_throttle():
            # When throttling, use minimum workers
            return self.min_workers
        
        try:
            # Get current CPU and memory usage
            stats = self.resource_monitor.get_resource_stats()
            cpu_percent = stats.get("cpu_percent", 0)
            memory_percent = stats.get("memory_percent", 0)
            
            # Adapt worker count based on system load
            if cpu_percent > 90 or memory_percent > 90:
                # System under heavy load, use minimum
                workers = self.min_workers
            elif cpu_percent > 70 or memory_percent > 70:
                # System under moderate load, use half
                workers = max(self.min_workers, self.max_workers // 2)
            else:
                # System has available resources, use maximum
                workers = self.max_workers
            
            return workers
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.logger.warning(f"psutil error determining worker count: {e}")
            return self.max_workers # Fallback to max workers
        except Exception as e:
            self.logger.exception(f"Unexpected error determining worker count: {e}")
            return self.max_workers
    
    def process_items(self, 
                     items: List[T], 
                     process_func: Callable[[T], R],
                     task_ids: Optional[List[str]] = None,
                     use_processes: bool = False,
                     show_progress: bool = True,
                     progress_interval: float = 0.5,
                     timeout: Optional[float] = None,
                     preserve_order: bool = True) -> List[ParallelResult[T, R]]:
        """Process items in parallel with enhanced tracking and resource management.
        
        Args:
            items: List of items to process
            process_func: Function to apply to each item
            task_ids: Optional list of task IDs (must match length of items)
            use_processes: Whether to use processes instead of threads
            show_progress: Whether to show progress updates
            progress_interval: How often to update progress (in seconds)
            timeout: Optional timeout per item (in seconds)
            preserve_order: Whether to preserve the original order of items in the results
                           (defaults to True to ensure consistent test behavior)
            
        Returns:
            List of ParallelResult objects
        """
        if not items:
            self.logger.warning("No items to process")
            return []
            
        # Create task IDs if not provided
        if task_ids is None:
            task_ids = [f"task_{i}" for i in range(len(items))]
        
        if len(task_ids) != len(items):
            self.logger.error(f"Task IDs length ({len(task_ids)}) doesn't match items length ({len(items)})")
            raise ValueError("Task IDs must match the number of items")
            
        # Create progress tracker
        progress = ProgressTracker(len(items), progress_interval) if show_progress else None
        
        # Start resource monitoring
        self.resource_monitor.start()
        
        # Start progress tracking if enabled
        if progress:
            progress.start()
        
        # Results will be stored here
        if preserve_order:
            results = [None] * len(items)  # Pre-allocate for preserving order
        else:
            results = []
            results_lock = threading.Lock()
        
        # Prepare for execution
        self.logger.info(
            f"Processing {len(items)} items in parallel using "
            f"{'processes' if use_processes else 'threads'} "
            f"(max workers: {self.max_workers})"
        )
        
        # Choose executor based on use_processes flag
        executor_class = (concurrent.futures.ProcessPoolExecutor if use_processes 
                          else concurrent.futures.ThreadPoolExecutor)
            
        # Start timing
        start_time = time.time()
        
        try:
            # Execute in parallel with dynamic worker count adjustment
            with executor_class(max_workers=self._get_worker_count()) as executor:
                # Submit all tasks with progress tracking
                futures = {}
                for i, (task_id, item) in enumerate(zip(task_ids, items)):
                    if progress:
                        progress.item_started()
                    
                    future = executor.submit(
                        self._execute_task_with_tracking, 
                        process_func, item, task_id,
                        i if preserve_order else None  # Track original index if preserving order
                    )
                    futures[future] = (i, task_id, item)
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(futures):
                    i, task_id, item = futures[future]
                    try:
                        result = future.result(timeout=timeout)
                        
                        # Store result in the appropriate place
                        if preserve_order:
                            # If preserving order, store at the original index
                            results[result.metadata.get('original_index', i)] = result
                        else:
                            # Otherwise, just append to the results list
                            with results_lock:
                                results.append(result)
                        
                        # Update progress
                        if progress:
                            progress.item_completed(result.success)
                        
                        # Log result
                        if result.success:
                            self.logger.debug(
                                f"Task {task_id} completed successfully in "
                                f"{result.processing_time:.2f}s"
                            )
                        else:
                            self.logger.warning(f"Task {task_id} failed: {result.error}")
                            
                    except concurrent.futures.TimeoutError:
                        # Handle timeout
                        error_msg = f"Task {task_id} timed out after {timeout}s"
                        self.logger.error(error_msg)
                        
                        # Create error result
                        error_result = ParallelResult(
                            task_id=task_id,
                            result=None,
                            success=False,
                            input_item=item,
                            error=error_msg,
                            processing_time=timeout or 0.0,
                            metadata={"timeout": True, "original_index": i if preserve_order else None}
                        )
                        
                        # Store result
                        if preserve_order:
                            results[i] = error_result
                        else:
                            with results_lock:
                                results.append(error_result)
                        
                        # Update progress
                        if progress:
                            progress.item_completed(False)
                        
                    except Exception as exc:
                        # Handle other exceptions
                        error_msg = f"Task {task_id} generated an exception: {exc}"
                        self.logger.exception(error_msg)
                        
                        # Create error result
                        error_result = ParallelResult(
                            task_id=task_id,
                            result=None,
                            success=False,
                            input_item=item,
                            error=str(exc),
                            processing_time=0.0,
                            metadata={"original_index": i if preserve_order else None}
                        )
                        
                        # Store result
                        if preserve_order:
                            results[i] = error_result
                        else:
                            with results_lock:
                                results.append(error_result)
                        
                        # Update progress
                        if progress:
                            progress.item_completed(False)
        
        finally:
            # Stop progress tracking and resource monitoring
            if progress:
                progress.stop()
            
            self.resource_monitor.stop()
        
        # Calculate total time and record metric
        total_time = time.time() - start_time
        performance_monitor.record_operation(
            f"parallel_processing_{len(items)}_items", total_time)
            
        # Log summary
        successful = sum(1 for r in results if r and r.success)
        self.logger.info(
            f"Parallel processing complete: {successful}/{len(items)} successful "
            f"in {total_time:.2f}s"
        )
        
        # Log resource usage
        self.logger.info(
            f"Peak resource usage - Memory: {self.resource_monitor.peak_memory_percent:.1f}%, "
            f"CPU: {self.resource_monitor.peak_cpu_percent:.1f}%"
        )
            
        return results
    
    @staticmethod
    def _execute_task_with_tracking(
        func: Callable[[T], R], 
        item: T, 
        task_id: str,
        original_index: Optional[int] = None
    ) -> ParallelResult[T, R]:
        """Execute a single task with enhanced tracking.
        
        Args:
            func: Function to execute
            item: Item to process
            task_id: Task identifier
            original_index: Original index of the item in the input list
            
        Returns:
            ParallelResult with task outcome and enhanced metadata
        """
        start_time = time.time()
        
        # Set worker ID (process or thread ID)
        worker_id = f"{os.getpid()}-{threading.get_ident()}"
        
        # Try to get initial memory usage
        try:
            # psutil already imported at top level
            # import psutil 
            process = psutil.Process(os.getpid())
            start_memory = process.memory_info().rss / (1024 * 1024)  # MB
        except ImportError:
            start_memory = 0
        except psutil.NoSuchProcess:
            # Process might have ended quickly, handle gracefully
            start_memory = 0
            worker_id += " (ended?)" # Mark worker ID if process ended early
        
        try:
            # Execute the function
            result = func(item)
            
            # Measure end time and memory
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Try to get memory usage after processing
            try:
                end_memory = process.memory_info().rss / (1024 * 1024)  # MB
                memory_change = end_memory - start_memory
            except:
                memory_change = 0
            
            # Create success result with enhanced metadata
            return ParallelResult(
                task_id=task_id,
                result=result,
                success=True,
                input_item=item,
                processing_time=processing_time,
                start_time=start_time,
                end_time=end_time,
                worker_id=worker_id,
                memory_usage=memory_change,
                metadata={
                    "item": str(item),
                    "original_index": original_index
                }
            )
        except Exception as e:
            # Measure end time for failed processing
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Create failure result
            return ParallelResult(
                task_id=task_id,
                result=None,
                success=False,
                input_item=item,
                error=str(e),
                processing_time=processing_time,
                start_time=start_time,
                end_time=end_time,
                worker_id=worker_id,
                metadata={
                    "item": str(item),
                    "original_index": original_index,
                    "exception_type": type(e).__name__
                }
            )
    
    def process_batches(self, 
                        items: List[T], 
                        process_func: Callable[[List[T]], List[R]],
                        batch_size: int = 10) -> List[R]:
        """Process items in batches to reduce overhead for small tasks.
        
        Args:
            items: List of items to process
            process_func: Function to apply to each batch of items
            batch_size: Number of items per batch
            
        Returns:
            List of results (flattened)
        """
        if not items:
            return []
            
        # Split items into batches
        batches = [items[i:i+batch_size] for i in range(0, len(items), batch_size)]
        
        self.logger.info(
            f"Processing {len(items)} items in {len(batches)} batches "
            f"(batch size: {batch_size})"
        )
        
        # Process each batch in parallel
        batch_results = self.process_items(
            items=batches,
            process_func=process_func,
            task_ids=[f"batch_{i}" for i in range(len(batches))]
        )
        
        # Flatten and filter results
        results = []
        for batch_result in batch_results:
            if batch_result.success and batch_result.result:
                results.extend(batch_result.result)
        
        return results
    
    def map_reduce(self,
                  items: List[T],
                  map_func: Callable[[T], R],
                  reduce_func: Callable[[List[R]], Any],
                  chunk_size: Optional[int] = None) -> Any:
        """Map-reduce style parallel processing with enhanced features.
        
        Args:
            items: List of items to process
            map_func: Function to apply to each item
            reduce_func: Function to combine results
            chunk_size: Optional chunk size for processing
            
        Returns:
            Result of the reduce function
        """
        if not items:
            return reduce_func([])
            
        # Calculate chunk size if not provided
        if chunk_size is None:
            chunk_size = max(1, len(items) // (self.max_workers * 2))
            
        self.logger.info(
            f"Running map-reduce on {len(items)} items with chunk size {chunk_size}"
        )
            
        # Create chunks
        chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
        
        # Process each chunk in parallel
        with performance_monitor.performance_context("map_reduce_operation"):
            # Map phase - process chunks in parallel
            chunk_results = self.process_items(
                items=chunks,
                process_func=lambda chunk: [map_func(item) for item in chunk],
                task_ids=[f"chunk_{i}" for i in range(len(chunks))],
                show_progress=True
            )
            
            # Extract results from successful chunks
            mapped_results = []
            for result in chunk_results:
                if result.success:
                    mapped_results.extend(result.result)
            
            # Reduce phase
            final_result = reduce_func(mapped_results)
                
        return final_result
    
    def ordered_results_iterator(self, results: List[ParallelResult[T, R]]) -> Iterator[R]:
        """Get an iterator over successful results in their original order.
        
        Args:
            results: List of ParallelResult objects
            
        Returns:
            Iterator yielding successful results in original order
        """
        # First, sort results by their original index if available
        ordered_results = sorted(
            [r for r in results if r.success],
            key=lambda r: r.metadata.get('original_index', 0) 
            if 'original_index' in r.metadata else 0
        )
        
        # Yield each successful result
        for result in ordered_results:
            yield result.result


# Create singleton for common usage
parallel_processor = ParallelProcessor()
