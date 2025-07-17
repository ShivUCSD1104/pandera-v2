"""
Performance monitoring module for Greeks calculations.

This module provides performance metrics, monitoring, and optimization
utilities for the Greeks Landscape feature.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from functools import wraps
import threading
import psutil
import os

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Data structure for storing performance metrics."""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_before: Optional[float] = None
    memory_after: Optional[float] = None
    memory_delta: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """
    Performance monitoring system for Greeks calculations.
    
    Tracks execution times, memory usage, cache performance,
    and database query performance.
    """
    
    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.lock = threading.Lock()
        self.max_history_size = 1000  # Keep last 1000 operations
        
        # Performance thresholds (in seconds)
        self.thresholds = {
            'greeks_calculation': 0.1,      # 100ms for single Greeks calculation
            'options_data_fetch': 2.0,      # 2 seconds for options data fetch
            'database_query': 1.0,          # 1 second for database queries
            'cache_operation': 0.01,        # 10ms for cache operations
            'full_landscape_generation': 5.0 # 5 seconds for full landscape
        }
        
        # Cache performance tracking
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0,
            'hit_ratio': 0.0
        }
        
        # Database connection pool monitoring
        self.db_pool_stats = {
            'active_connections': 0,
            'total_connections': 0,
            'overflow_connections': 0,
            'pool_size': 0
        }
    
    def start_operation(self, operation_name: str, **additional_data) -> PerformanceMetrics:
        """
        Start monitoring a performance operation.
        
        Args:
            operation_name: Name of the operation being monitored
            **additional_data: Additional data to track with this operation
            
        Returns:
            PerformanceMetrics object to track this operation
        """
        try:
            # Get current memory usage
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            metrics = PerformanceMetrics(
                operation_name=operation_name,
                start_time=time.time(),
                memory_before=memory_before,
                additional_data=additional_data
            )
            
            logger.debug(f"Started monitoring operation: {operation_name}")
            return metrics
            
        except Exception as e:
            logger.warning(f"Error starting performance monitoring for {operation_name}: {str(e)}")
            # Return a basic metrics object even if monitoring fails
            return PerformanceMetrics(
                operation_name=operation_name,
                start_time=time.time(),
                additional_data=additional_data
            )
    
    def end_operation(self, metrics: PerformanceMetrics, success: bool = True, error_message: str = None):
        """
        End monitoring a performance operation and record results.
        
        Args:
            metrics: PerformanceMetrics object from start_operation
            success: Whether the operation completed successfully
            error_message: Error message if operation failed
        """
        try:
            metrics.end_time = time.time()
            metrics.duration = metrics.end_time - metrics.start_time
            metrics.success = success
            metrics.error_message = error_message
            
            # Get memory usage after operation
            try:
                process = psutil.Process(os.getpid())
                metrics.memory_after = process.memory_info().rss / 1024 / 1024  # MB
                if metrics.memory_before is not None:
                    metrics.memory_delta = metrics.memory_after - metrics.memory_before
            except Exception as e:
                logger.debug(f"Could not measure memory usage: {str(e)}")
            
            # Store metrics in history
            with self.lock:
                self.metrics_history.append(metrics)
                
                # Trim history if it gets too large
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history = self.metrics_history[-self.max_history_size:]
            
            # Log performance warnings if operation was slow
            if metrics.duration and metrics.duration > self.thresholds.get(metrics.operation_name, 10.0):
                logger.warning(
                    f"Slow operation detected: {metrics.operation_name} took {metrics.duration:.3f}s "
                    f"(threshold: {self.thresholds.get(metrics.operation_name, 10.0)}s)"
                )
            
            # Log memory usage if significant
            if metrics.memory_delta and abs(metrics.memory_delta) > 50:  # 50MB threshold
                logger.info(
                    f"Memory usage change for {metrics.operation_name}: "
                    f"{metrics.memory_delta:+.1f}MB (before: {metrics.memory_before:.1f}MB, "
                    f"after: {metrics.memory_after:.1f}MB)"
                )
            
            logger.debug(
                f"Completed monitoring operation: {metrics.operation_name} "
                f"({metrics.duration:.3f}s, success: {success})"
            )
            
        except Exception as e:
            logger.error(f"Error ending performance monitoring: {str(e)}")
    
    def record_cache_hit(self):
        """Record a cache hit for performance tracking."""
        with self.lock:
            self.cache_stats['hits'] += 1
            self.cache_stats['total_requests'] += 1
            self._update_cache_hit_ratio()
    
    def record_cache_miss(self):
        """Record a cache miss for performance tracking."""
        with self.lock:
            self.cache_stats['misses'] += 1
            self.cache_stats['total_requests'] += 1
            self._update_cache_hit_ratio()
    
    def _update_cache_hit_ratio(self):
        """Update the cache hit ratio calculation."""
        if self.cache_stats['total_requests'] > 0:
            self.cache_stats['hit_ratio'] = (
                self.cache_stats['hits'] / self.cache_stats['total_requests']
            )
    
    def update_db_pool_stats(self, engine):
        """
        Update database connection pool statistics.
        
        Args:
            engine: SQLAlchemy engine with connection pool
        """
        try:
            pool = engine.pool
            with self.lock:
                self.db_pool_stats.update({
                    'pool_size': pool.size(),
                    'active_connections': pool.checkedout(),
                    'total_connections': pool.checkedin() + pool.checkedout(),
                    'overflow_connections': pool.overflow(),
                })
            
            # Log warnings if pool is under stress
            if self.db_pool_stats['active_connections'] > self.db_pool_stats['pool_size'] * 0.8:
                logger.warning(
                    f"Database connection pool usage high: "
                    f"{self.db_pool_stats['active_connections']}/{self.db_pool_stats['pool_size']} "
                    f"active connections"
                )
                
        except Exception as e:
            logger.debug(f"Could not update database pool stats: {str(e)}")
    
    def get_performance_summary(self, operation_name: str = None, hours: int = 1) -> Dict[str, Any]:
        """
        Get performance summary for recent operations.
        
        Args:
            operation_name: Filter by specific operation name (optional)
            hours: Number of hours to look back (default: 1)
            
        Returns:
            Dictionary with performance summary statistics
        """
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            with self.lock:
                # Filter metrics by time and operation name
                filtered_metrics = [
                    m for m in self.metrics_history
                    if m.start_time >= cutoff_time and
                    (operation_name is None or m.operation_name == operation_name)
                ]
            
            if not filtered_metrics:
                return {
                    'operation_name': operation_name or 'all',
                    'time_period_hours': hours,
                    'total_operations': 0,
                    'message': 'No operations found in time period'
                }
            
            # Calculate statistics
            durations = [m.duration for m in filtered_metrics if m.duration is not None]
            successful_ops = [m for m in filtered_metrics if m.success]
            failed_ops = [m for m in filtered_metrics if not m.success]
            
            summary = {
                'operation_name': operation_name or 'all',
                'time_period_hours': hours,
                'total_operations': len(filtered_metrics),
                'successful_operations': len(successful_ops),
                'failed_operations': len(failed_ops),
                'success_rate': len(successful_ops) / len(filtered_metrics) if filtered_metrics else 0,
            }
            
            if durations:
                summary.update({
                    'avg_duration_seconds': sum(durations) / len(durations),
                    'min_duration_seconds': min(durations),
                    'max_duration_seconds': max(durations),
                    'total_duration_seconds': sum(durations),
                })
                
                # Calculate percentiles
                sorted_durations = sorted(durations)
                n = len(sorted_durations)
                summary.update({
                    'p50_duration_seconds': sorted_durations[n // 2],
                    'p95_duration_seconds': sorted_durations[int(n * 0.95)] if n > 20 else max(durations),
                    'p99_duration_seconds': sorted_durations[int(n * 0.99)] if n > 100 else max(durations),
                })
            
            # Add memory statistics if available
            memory_deltas = [m.memory_delta for m in filtered_metrics if m.memory_delta is not None]
            if memory_deltas:
                summary.update({
                    'avg_memory_delta_mb': sum(memory_deltas) / len(memory_deltas),
                    'max_memory_delta_mb': max(memory_deltas),
                    'min_memory_delta_mb': min(memory_deltas),
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating performance summary: {str(e)}")
            return {
                'error': f"Could not generate performance summary: {str(e)}"
            }
    
    def get_cache_performance(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache performance metrics
        """
        with self.lock:
            return dict(self.cache_stats)
    
    def get_db_pool_performance(self) -> Dict[str, Any]:
        """
        Get database connection pool performance statistics.
        
        Returns:
            Dictionary with database pool metrics
        """
        with self.lock:
            return dict(self.db_pool_stats)
    
    def get_system_performance(self) -> Dict[str, Any]:
        """
        Get current system performance metrics.
        
        Returns:
            Dictionary with system performance metrics
        """
        try:
            process = psutil.Process(os.getpid())
            
            return {
                'cpu_percent': process.cpu_percent(),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'memory_percent': process.memory_percent(),
                'num_threads': process.num_threads(),
                'open_files': len(process.open_files()) if hasattr(process, 'open_files') else 0,
                'connections': len(process.connections()) if hasattr(process, 'connections') else 0,
            }
            
        except Exception as e:
            logger.warning(f"Could not get system performance metrics: {str(e)}")
            return {'error': str(e)}
    
    def reset_stats(self):
        """Reset all performance statistics."""
        with self.lock:
            self.metrics_history.clear()
            self.cache_stats = {
                'hits': 0,
                'misses': 0,
                'total_requests': 0,
                'hit_ratio': 0.0
            }
            self.db_pool_stats = {
                'active_connections': 0,
                'total_connections': 0,
                'overflow_connections': 0,
                'pool_size': 0
            }
        
        logger.info("Performance statistics reset")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(operation_name: str, **additional_data):
    """
    Decorator to automatically monitor function performance.
    
    Args:
        operation_name: Name of the operation being monitored
        **additional_data: Additional data to track with this operation
    
    Usage:
        @monitor_performance('greeks_calculation', ticker='AAPL')
        def calculate_greeks(data):
            # function implementation
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            metrics = performance_monitor.start_operation(operation_name, **additional_data)
            
            try:
                result = func(*args, **kwargs)
                performance_monitor.end_operation(metrics, success=True)
                return result
                
            except Exception as e:
                performance_monitor.end_operation(
                    metrics, 
                    success=False, 
                    error_message=str(e)
                )
                raise
        
        return wrapper
    return decorator


def log_performance_summary(operation_name: str = None, hours: int = 1):
    """
    Log a performance summary for recent operations.
    
    Args:
        operation_name: Filter by specific operation name (optional)
        hours: Number of hours to look back (default: 1)
    """
    try:
        summary = performance_monitor.get_performance_summary(operation_name, hours)
        
        if 'error' in summary:
            logger.error(f"Performance summary error: {summary['error']}")
            return
        
        if summary['total_operations'] == 0:
            logger.info(f"No {operation_name or 'operations'} found in last {hours} hour(s)")
            return
        
        logger.info(
            f"Performance Summary ({operation_name or 'all operations'}, last {hours}h): "
            f"{summary['total_operations']} ops, "
            f"{summary['success_rate']:.1%} success rate, "
            f"avg: {summary.get('avg_duration_seconds', 0):.3f}s, "
            f"p95: {summary.get('p95_duration_seconds', 0):.3f}s"
        )
        
        if summary.get('avg_memory_delta_mb'):
            logger.info(
                f"Memory usage: avg {summary['avg_memory_delta_mb']:+.1f}MB, "
                f"max {summary['max_memory_delta_mb']:+.1f}MB"
            )
        
    except Exception as e:
        logger.error(f"Error logging performance summary: {str(e)}")