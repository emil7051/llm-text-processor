"""Performance optimization utilities for TextCleaner.

This module provides utilities for improving performance through caching,
memoization, and other optimization techniques.
"""

import functools
import hashlib
import time
import statistics
from typing import Dict, List, Any, Optional, Callable, TypeVar, cast
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from textcleaner.utils.logging_config import get_logger

T = TypeVar('T')


def timed(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that times the execution of a function.
    
    Args:
        func: The function to time
        
    Returns:
        A wrapped function that logs execution time
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds to run")
        return result
    
    return wrapper


def memoize(func: Callable[..., T]) -> Callable[..., T]:
    """Simple memoization decorator for caching function results.
    
    Args:
        func: The function to memoize
        
    Returns:
        A memoized version of the function
    """
    cache: Dict[str, Any] = {}
    
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Create a cache key from the function arguments
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key = hashlib.md5(str(key_parts).encode()).hexdigest()
        
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        
        return cast(T, cache[key])
    
    # Add a method to clear the cache
    wrapper.clear_cache = lambda: cache.clear()  # type: ignore
    
    return wrapper


# Create a specialized token counter cache with limited size
@functools.lru_cache(maxsize=128)
def calculate_token_estimate(text: str, model: str = "default") -> int:
    """Calculate estimated tokens with caching for repeated calls.
    
    This function provides a simple approximation of token count based on
    whitespace. For accurate counts, it should be replaced with a proper
    tokenizer implementation.
    
    Args:
        text: The text to estimate token count for
        model: The model to use for tokenization (defaults to a simple approach)
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
        
    # Simple approximation - replace with proper tokenizers in practice
    if model == "default":
        # Rough estimate - about 4 chars per token for English text
        return max(1, len(text) // 4)
    elif model in ["gpt-3.5", "gpt-4"]:
        # Slightly more precise but still an approximation
        return len(text.split())
    else:
        # Fallback
        return len(text.split())


class TokenCounter:
    """Class for tracking token usage with model-specific counting."""
    
    def __init__(self) -> None:
        """Initialize the token counter."""
        self.reset()
        
    def reset(self) -> None:
        """Reset all counters."""
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        
    def add_input(self, text: str, model: str = "default") -> int:
        """Add input text and count its tokens.
        
        Args:
            text: The input text
            model: The model to use for tokenization
            
        Returns:
            The token count for this text
        """
        tokens = calculate_token_estimate(text, model)
        self.input_tokens += tokens
        self.total_tokens += tokens
        return tokens
        
    def add_output(self, text: str, model: str = "default") -> int:
        """Add output text and count its tokens.
        
        Args:
            text: The output text
            model: The model to use for tokenization
            
        Returns:
            The token count for this text
        """
        tokens = calculate_token_estimate(text, model)
        self.output_tokens += tokens
        self.total_tokens += tokens
        return tokens
        
    def get_stats(self) -> Dict[str, int]:
        """Get token usage statistics.
        
        Returns:
            Dictionary with token counts
        """
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens
        }


# Create a global token counter instance for convenience
token_counter = TokenCounter()


@dataclass
class OperationMetrics:
    """Metrics for a specific operation."""
    name: str
    times: List[float] = field(default_factory=list)
    
    def add_time(self, seconds: float) -> None:
        """Add a time measurement."""
        self.times.append(seconds)
    
    @property
    def average(self) -> Optional[float]:
        """Get average time."""
        if not self.times:
            return None
        return statistics.mean(self.times)
    
    @property
    def median(self) -> Optional[float]:
        """Get median time."""
        if not self.times:
            return None
        return statistics.median(self.times)
    
    @property
    def min(self) -> Optional[float]:
        """Get minimum time."""
        if not self.times:
            return None
        return min(self.times)
    
    @property
    def max(self) -> Optional[float]:
        """Get maximum time."""
        if not self.times:
            return None
        return max(self.times)
    
    @property
    def stdev(self) -> Optional[float]:
        """Get standard deviation."""
        if len(self.times) < 2:
            return None
        return statistics.stdev(self.times)
    
    @property
    def count(self) -> int:
        """Get number of measurements."""
        return len(self.times)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "count": self.count,
        }
        
        # Only include statistics if we have measurements
        if self.times:
            result.update({
                "average_seconds": self.average,
                "median_seconds": self.median,
                "min_seconds": self.min,
                "max_seconds": self.max,
                "total_seconds": sum(self.times),
            })
            
            # Only include standard deviation if we have enough measurements
            if len(self.times) >= 2:
                result["stdev_seconds"] = self.stdev
                
        return result


class PerformanceMonitor:
    """Monitor and report on processing performance."""
    
    def __init__(self, enabled: bool = True):
        """Initialize the performance monitor.
        
        Args:
            enabled: Whether the monitor is enabled
        """
        self.logger = get_logger(__name__)
        self.enabled = enabled
        self.operations: Dict[str, OperationMetrics] = {}
        self.start_time = datetime.now()
    
    def record_operation(self, operation: str, time_taken: float) -> None:
        """Record the time taken for an operation.
        
        Args:
            operation: Name of the operation
            time_taken: Time taken in seconds
        """
        if not self.enabled:
            return
            
        if operation not in self.operations:
            self.operations[operation] = OperationMetrics(operation)
        
        self.operations[operation].add_time(time_taken)
        
    def get_operation_stats(self, operation: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific operation.
        
        Args:
            operation: Name of the operation
            
        Returns:
            Dictionary of statistics or None if operation not found
        """
        if not self.enabled or operation not in self.operations:
            return None
            
        return self.operations[operation].to_dict()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report.
        
        Returns:
            Dictionary with performance data
        """
        if not self.enabled:
            return {"enabled": False}
            
        total_time = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "enabled": True,
            "total_runtime_seconds": total_time,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "operations": [op.to_dict() for op in self.operations.values()]
        }
    
    def save_report(self, output_path: Path) -> None:
        """Save the performance report to a file.
        
        Args:
            output_path: Path to save the report to
        """
        if not self.enabled:
            self.logger.warning("Performance monitor is disabled, not saving report")
            return
            
        try:
            report = self.generate_report()
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"Performance report saved to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save performance report: {e}")
        except (IOError, OSError) as e:
            self.logger.error(f"Failed to save performance report to {output_path}: {e}")
        except Exception as e:
            self.logger.exception(f"Unexpected error saving performance report to {output_path}")
    
    def performance_context(self, operation: str):
        """Context manager to time an operation.
        
        Args:
            operation: Name of the operation
            
        Returns:
            Context manager that records the time taken
        """
        class PerformanceContext:
            def __init__(self, monitor, operation):
                self.monitor = monitor
                self.operation = operation
                self.start_time = None
                
            def __enter__(self):
                self.start_time = time.time()
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.monitor.enabled and self.start_time is not None:
                    time_taken = time.time() - self.start_time
                    self.monitor.record_operation(self.operation, time_taken)
        
        return PerformanceContext(self, operation)
    
    def reset(self) -> None:
        """Reset all performance data."""
        self.operations.clear()
        self.start_time = datetime.now()


# Create a singleton instance for common usage
performance_monitor = PerformanceMonitor()
