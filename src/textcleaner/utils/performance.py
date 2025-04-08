"""Performance monitoring utilities for the LLM Text Processor."""

import time
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from textcleaner.utils.logging_config import get_logger


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
