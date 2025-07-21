"""
Unit tests for the performance monitoring system.

Tests the PerformanceMonitor class and related functionality
without requiring database connections or external dependencies.
"""

import pytest
import time
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Mock DATABASE_URL before importing modules that need it
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from GreeksLandscape.performance_monitor import (
    PerformanceMonitor, PerformanceMetrics, monitor_performance,
    performance_monitor, log_performance_summary
)


class TestPerformanceMetrics:
    """Test the PerformanceMetrics dataclass."""
    
    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics objects."""
        metrics = PerformanceMetrics(
            operation_name="test_operation",
            start_time=time.time()
        )
        
        assert metrics.operation_name == "test_operation"
        assert metrics.start_time > 0
        assert metrics.end_time is None
        assert metrics.duration is None
        assert metrics.success is True
        assert metrics.error_message is None
    
    def test_performance_metrics_with_additional_data(self):
        """Test PerformanceMetrics with additional data."""
        additional_data = {"ticker": "AAPL", "operation_type": "test"}
        
        metrics = PerformanceMetrics(
            operation_name="test_operation",
            start_time=time.time(),
            additional_data=additional_data
        )
        
        assert metrics.additional_data == additional_data
        assert metrics.additional_data["ticker"] == "AAPL"


class TestPerformanceMonitor:
    """Test the PerformanceMonitor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
    
    def test_monitor_initialization(self):
        """Test PerformanceMonitor initialization."""
        assert self.monitor.metrics_history == []
        assert self.monitor.max_history_size == 1000
        assert isinstance(self.monitor.thresholds, dict)
        assert isinstance(self.monitor.cache_stats, dict)
        assert isinstance(self.monitor.db_pool_stats, dict)
    
    @patch('GreeksLandscape.performance_monitor.psutil.Process')
    def test_start_operation(self, mock_process):
        """Test starting performance monitoring."""
        # Mock memory info
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        mock_process.return_value = mock_process_instance
        
        metrics = self.monitor.start_operation("test_operation", test_param="value")
        
        assert metrics.operation_name == "test_operation"
        assert metrics.start_time > 0
        assert metrics.memory_before == 100.0  # MB
        assert metrics.additional_data["test_param"] == "value"
    
    @patch('GreeksLandscape.performance_monitor.psutil.Process')
    def test_end_operation(self, mock_process):
        """Test ending performance monitoring."""
        # Mock memory info
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value.rss = 110 * 1024 * 1024  # 110MB
        mock_process.return_value = mock_process_instance
        
        # Start operation
        metrics = PerformanceMetrics(
            operation_name="test_operation",
            start_time=time.time(),
            memory_before=100.0
        )
        
        # End operation
        self.monitor.end_operation(metrics, success=True)
        
        assert metrics.end_time > metrics.start_time
        assert metrics.duration > 0
        assert metrics.success is True
        assert metrics.memory_after == 110.0
        assert metrics.memory_delta == 10.0
        assert len(self.monitor.metrics_history) == 1
    
    def test_cache_performance_tracking(self):
        """Test cache performance tracking."""
        # Record cache hits and misses
        self.monitor.record_cache_hit()
        self.monitor.record_cache_hit()
        self.monitor.record_cache_miss()
        
        stats = self.monitor.get_cache_performance()
        
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['total_requests'] == 3
        assert stats['hit_ratio'] == 2/3
    
    def test_performance_summary(self):
        """Test performance summary generation."""
        # Add some test metrics
        for i in range(3):
            metrics = PerformanceMetrics(
                operation_name="test_operation",
                start_time=time.time() - 1,
                end_time=time.time(),
                duration=0.1 + i * 0.05,
                success=True
            )
            self.monitor.metrics_history.append(metrics)
        
        summary = self.monitor.get_performance_summary("test_operation", hours=1)
        
        assert summary['total_operations'] == 3
        assert summary['successful_operations'] == 3
        assert summary['success_rate'] == 1.0
        assert 'avg_duration_seconds' in summary
        assert 'min_duration_seconds' in summary
        assert 'max_duration_seconds' in summary
    
    @patch('GreeksLandscape.performance_monitor.psutil.Process')
    def test_system_performance_metrics(self, mock_process):
        """Test system performance metrics collection."""
        # Mock process info
        mock_process_instance = Mock()
        mock_process_instance.cpu_percent.return_value = 25.5
        mock_process_instance.memory_info.return_value.rss = 100 * 1024 * 1024
        mock_process_instance.memory_percent.return_value = 15.2
        mock_process_instance.num_threads.return_value = 8
        mock_process_instance.open_files.return_value = []
        mock_process_instance.connections.return_value = []
        mock_process.return_value = mock_process_instance
        
        stats = self.monitor.get_system_performance()
        
        assert stats['cpu_percent'] == 25.5
        assert stats['memory_mb'] == 100.0
        assert stats['memory_percent'] == 15.2
        assert stats['num_threads'] == 8
        assert 'open_files' in stats
        assert 'connections' in stats
    
    def test_reset_stats(self):
        """Test resetting performance statistics."""
        # Add some data
        self.monitor.record_cache_hit()
        self.monitor.metrics_history.append(
            PerformanceMetrics("test", time.time())
        )
        
        # Reset
        self.monitor.reset_stats()
        
        assert len(self.monitor.metrics_history) == 0
        assert self.monitor.cache_stats['hits'] == 0
        assert self.monitor.cache_stats['total_requests'] == 0


class TestPerformanceDecorator:
    """Test the monitor_performance decorator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset global performance monitor
        performance_monitor.reset_stats()
    
    def test_decorator_basic_functionality(self):
        """Test basic decorator functionality."""
        @monitor_performance('test_operation')
        def test_function():
            time.sleep(0.01)  # Small delay
            return "test_result"
        
        result = test_function()
        
        assert result == "test_result"
        
        # Check that metrics were recorded
        summary = performance_monitor.get_performance_summary('test_operation', hours=1)
        assert summary['total_operations'] >= 1
        assert summary['successful_operations'] >= 1
    
    def test_decorator_with_exception(self):
        """Test decorator behavior when function raises exception."""
        @monitor_performance('test_operation_error')
        def test_function_with_error():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            test_function_with_error()
        
        # Check that error was recorded
        summary = performance_monitor.get_performance_summary('test_operation_error', hours=1)
        assert summary['total_operations'] >= 1
        assert summary['failed_operations'] >= 1
    
    def test_decorator_with_additional_data(self):
        """Test decorator with additional data parameters."""
        @monitor_performance('test_operation_data', ticker='AAPL', operation_type='test')
        def test_function_with_data():
            return "success"
        
        result = test_function_with_data()
        
        assert result == "success"
        
        # Verify additional data was recorded
        summary = performance_monitor.get_performance_summary('test_operation_data', hours=1)
        assert summary['total_operations'] >= 1


class TestPerformanceUtilities:
    """Test performance monitoring utility functions."""
    
    @patch('GreeksLandscape.performance_monitor.logger')
    def test_log_performance_summary(self, mock_logger):
        """Test performance summary logging."""
        # Add some test data
        performance_monitor.reset_stats()
        metrics = PerformanceMetrics(
            operation_name="test_log_operation",
            start_time=time.time() - 1,
            end_time=time.time(),
            duration=0.5,
            success=True
        )
        performance_monitor.metrics_history.append(metrics)
        
        # Test logging
        log_performance_summary('test_log_operation', hours=1)
        
        # Verify logger was called
        assert mock_logger.info.called
        
        # Check log message content
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any('Performance Summary' in call for call in log_calls)
    
    @patch('GreeksLandscape.performance_monitor.logger')
    def test_log_performance_summary_no_operations(self, mock_logger):
        """Test logging when no operations are found."""
        performance_monitor.reset_stats()
        
        log_performance_summary('nonexistent_operation', hours=1)
        
        # Should log that no operations were found
        assert mock_logger.info.called
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any('No' in call and 'found' in call for call in log_calls)


class TestPerformanceThresholds:
    """Test performance threshold monitoring."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
    
    @patch('GreeksLandscape.performance_monitor.logger')
    def test_slow_operation_warning(self, mock_logger):
        """Test that slow operations trigger warnings."""
        # Create a slow operation
        metrics = PerformanceMetrics(
            operation_name="greeks_calculation",
            start_time=time.time() - 1,
            duration=0.5  # Exceeds 0.1s threshold
        )
        
        self.monitor.end_operation(metrics, success=True)
        
        # Should log a warning
        assert mock_logger.warning.called
        warning_message = mock_logger.warning.call_args[0][0]
        assert "Slow operation detected" in warning_message
    
    @patch('GreeksLandscape.performance_monitor.logger')
    def test_memory_usage_logging(self, mock_logger):
        """Test that significant memory usage is logged."""
        metrics = PerformanceMetrics(
            operation_name="test_operation",
            start_time=time.time() - 1,
            memory_before=100.0,
            memory_after=160.0,  # 60MB increase
            memory_delta=60.0
        )
        
        self.monitor.end_operation(metrics, success=True)
        
        # Should log memory usage
        assert mock_logger.info.called
        info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any("Memory usage change" in call for call in info_calls)


@pytest.mark.integration
class TestPerformanceMonitorIntegration:
    """Integration tests for performance monitoring."""
    
    def test_full_monitoring_workflow(self):
        """Test complete monitoring workflow."""
        monitor = PerformanceMonitor()
        
        # Start operation
        metrics = monitor.start_operation("integration_test", test_param="value")
        
        # Simulate work
        time.sleep(0.01)
        
        # End operation
        monitor.end_operation(metrics, success=True)
        
        # Verify results
        assert len(monitor.metrics_history) == 1
        assert metrics.duration > 0
        assert metrics.success is True
        
        # Get summary
        summary = monitor.get_performance_summary("integration_test", hours=1)
        assert summary['total_operations'] == 1
        assert summary['successful_operations'] == 1
        assert summary['success_rate'] == 1.0