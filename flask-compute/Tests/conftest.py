"""
Shared pytest configuration and fixtures for all tests.

This file provides common fixtures, test configuration, and utilities
that can be used across all test modules.
"""

import pytest
import os
import sys
import logging
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add parent directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@pytest.fixture(scope="session")
def test_database_url():
    """Provide a test database URL for testing."""
    return 'sqlite:///:memory:'


@pytest.fixture(scope="function")
def mock_database_url(test_database_url):
    """Mock the DATABASE_URL environment variable for tests."""
    with patch.dict(os.environ, {'DATABASE_URL': test_database_url}):
        yield test_database_url


@pytest.fixture(scope="function")
def sample_greeks_data():
    """Provide sample Greeks data for testing."""
    from GreeksLandscape.data import GreeksData
    
    return GreeksData(
        strike=100.0,
        expiry=datetime.now().date(),
        time_to_expiry=0.25,  # 3 months
        underlying_price=105.0,
        risk_free_rate=0.05,
        volatility=0.20,
        option_type='call'
    )


@pytest.fixture(scope="function")
def sample_options_chain():
    """Provide sample options chain data for testing."""
    from GreeksLandscape.data import OptionsChainData
    
    options = [
        {
            'strike': 95.0,
            'expiry': datetime.now().date(),
            'type': 'call',
            'bid': 8.0,
            'ask': 8.5,
            'last_price': 8.25,
            'implied_volatility': 0.18,
            'time_to_expiry': 0.25
        },
        {
            'strike': 100.0,
            'expiry': datetime.now().date(),
            'type': 'call',
            'bid': 5.0,
            'ask': 5.5,
            'last_price': 5.25,
            'implied_volatility': 0.20,
            'time_to_expiry': 0.25
        },
        {
            'strike': 105.0,
            'expiry': datetime.now().date(),
            'type': 'call',
            'bid': 2.5,
            'ask': 3.0,
            'last_price': 2.75,
            'implied_volatility': 0.22,
            'time_to_expiry': 0.25
        }
    ]
    
    return OptionsChainData(
        ticker='TEST',
        underlying_price=100.0,
        options=options,
        fetch_date=datetime.now()
    )


@pytest.fixture(scope="function")
def mock_performance_monitor():
    """Mock the performance monitor for testing."""
    with patch('GreeksLandscape.performance_monitor.performance_monitor') as mock_monitor:
        mock_monitor.start_operation.return_value = Mock()
        mock_monitor.end_operation.return_value = None
        mock_monitor.get_performance_summary.return_value = {
            'total_operations': 1,
            'successful_operations': 1,
            'success_rate': 1.0,
            'avg_duration': 0.1
        }
        yield mock_monitor


@pytest.fixture(scope="function")
def mock_database_session():
    """Mock database session for testing."""
    with patch('db.SessionLocal') as mock_session_class:
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        yield mock_session


@pytest.fixture(scope="function")
def clean_cache():
    """Clean all caches before and after tests."""
    try:
        from GreeksLandscape.greeks_calculator import GreeksCalculator
        from GreeksLandscape.data import GreeksDataFetcher
        
        # Clean caches before test
        calculator = GreeksCalculator()
        data_fetcher = GreeksDataFetcher()
        
        calculator.invalidate_cache()
        data_fetcher.invalidate_options_cache()
        
        yield
        
        # Clean caches after test
        calculator.invalidate_cache()
        data_fetcher.invalidate_options_cache()
        
    except ImportError:
        # If modules can't be imported, just yield
        yield


@pytest.fixture(scope="function")
def test_tickers():
    """Provide a list of test ticker symbols."""
    return ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']


@pytest.fixture(scope="function")
def performance_test_config():
    """Provide configuration for performance tests."""
    return {
        'concurrency_levels': [2, 5, 10],
        'test_duration_seconds': 30,
        'cache_test_iterations': 5,
        'memory_threshold_mb': 100,
        'response_time_threshold_seconds': 5.0
    }


@pytest.fixture(scope="session")
def test_logger():
    """Provide a test logger."""
    logger = logging.getLogger('test_logger')
    logger.setLevel(logging.INFO)
    return logger


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database connection"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location."""
    for item in items:
        # Add markers based on test file location
        if "Unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "Integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "Performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        elif "ErrorHandling" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add database marker for tests that need database
        if any(keyword in str(item.fspath) for keyword in ["database", "migration", "integration"]):
            item.add_marker(pytest.mark.database)


# Utility functions for tests
def assert_performance_within_threshold(duration, threshold, operation_name="operation"):
    """Assert that an operation completed within the performance threshold."""
    assert duration <= threshold, (
        f"{operation_name} took {duration:.3f}s, "
        f"which exceeds threshold of {threshold:.3f}s"
    )


def assert_cache_hit_ratio_above_threshold(hit_ratio, threshold=0.5):
    """Assert that cache hit ratio is above the specified threshold."""
    assert hit_ratio >= threshold, (
        f"Cache hit ratio {hit_ratio:.1%} is below threshold of {threshold:.1%}"
    )


def assert_memory_usage_within_limit(memory_delta, limit_mb=50):
    """Assert that memory usage increase is within acceptable limits."""
    assert abs(memory_delta) <= limit_mb, (
        f"Memory usage change of {memory_delta:.1f}MB exceeds limit of {limit_mb}MB"
    )


# Export utility functions
__all__ = [
    'assert_performance_within_threshold',
    'assert_cache_hit_ratio_above_threshold', 
    'assert_memory_usage_within_limit'
]