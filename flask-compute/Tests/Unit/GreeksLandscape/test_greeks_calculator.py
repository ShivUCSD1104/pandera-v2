"""
Unit tests for the Greeks calculator with performance optimizations.

Tests the GreeksCalculator class and CacheManager functionality
with mocked dependencies to ensure fast, isolated testing.
"""

import pytest
import time
import math
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Mock DATABASE_URL before importing modules that need it
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from GreeksLandscape.greeks_calculator import (
    GreeksCalculator, CacheManager, _cache_manager
)
from GreeksLandscape.data import GreeksData
from GreeksLandscape.exceptions import CalculationError, ValidationError


class TestCacheManager:
    """Test the CacheManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache_manager = CacheManager(cache_duration_hours=1)
    
    def test_cache_manager_initialization(self):
        """Test CacheManager initialization."""
        assert self.cache_manager.cache_duration == timedelta(hours=1)
        assert self.cache_manager.cache == {}
        assert self.cache_manager.cache_timestamps == {}
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        key1 = self.cache_manager.get_cache_key('test', param1='value1', param2='value2')
        key2 = self.cache_manager.get_cache_key('test', param1='value1', param2='value2')
        key3 = self.cache_manager.get_cache_key('test', param1='different', param2='value2')
        
        # Same parameters should generate same key
        assert key1 == key2
        # Different parameters should generate different key
        assert key1 != key3
        # Keys should be strings
        assert isinstance(key1, str)
        assert len(key1) > 0
    
    def test_cache_storage_and_retrieval(self):
        """Test caching and retrieving results."""
        test_data = {'result': 'test_value', 'number': 42}
        cache_key = 'test_key'
        
        # Cache the result
        self.cache_manager.cache_result(cache_key, test_data)
        
        # Retrieve the result
        retrieved_data = self.cache_manager.get_cached_result(cache_key)
        
        assert retrieved_data == test_data
        assert self.cache_manager.is_cache_valid(cache_key)
    
    def test_cache_expiration(self):
        """Test cache expiration functionality."""
        test_data = {'result': 'test_value'}
        cache_key = 'test_key'
        
        # Create cache manager with very short duration
        short_cache = CacheManager(cache_duration_hours=0.001)  # ~3.6 seconds
        
        # Cache the result
        short_cache.cache_result(cache_key, test_data)
        
        # Should be valid immediately
        assert short_cache.is_cache_valid(cache_key)
        assert short_cache.get_cached_result(cache_key) == test_data
        
        # Manually expire by setting old timestamp
        short_cache.cache_timestamps[cache_key] = datetime.now() - timedelta(hours=1)
        
        # Should be expired now
        assert not short_cache.is_cache_valid(cache_key)
        assert short_cache.get_cached_result(cache_key) is None
    
    def test_cache_invalidation(self):
        """Test cache invalidation."""
        # Add some test data
        self.cache_manager.cache_result('key1', 'data1')
        self.cache_manager.cache_result('key2', 'data2')
        self.cache_manager.cache_result('pattern_key', 'pattern_data')
        
        # Invalidate by pattern
        self.cache_manager.invalidate_cache('pattern')
        
        # Pattern key should be gone
        assert 'pattern_key' not in self.cache_manager.cache
        # Other keys should remain
        assert 'key1' in self.cache_manager.cache
        assert 'key2' in self.cache_manager.cache
        
        # Invalidate all
        self.cache_manager.invalidate_cache()
        
        # All should be gone
        assert len(self.cache_manager.cache) == 0
        assert len(self.cache_manager.cache_timestamps) == 0
    
    def test_cache_statistics(self):
        """Test cache statistics generation."""
        # Add some test data
        self.cache_manager.cache_result('key1', 'data1')
        self.cache_manager.cache_result('key2', 'data2')
        
        # Simulate some hits
        self.cache_manager._hit_count = 5
        self.cache_manager._total_requests = 10
        
        stats = self.cache_manager.get_cache_stats()
        
        assert stats['total_entries'] == 2
        assert stats['valid_entries'] == 2
        assert stats['expired_entries'] == 0
        assert stats['cache_hit_ratio'] == 0.5


class TestGreeksCalculator:
    """Test the GreeksCalculator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = GreeksCalculator()
        # Clear global cache
        _cache_manager.invalidate_cache()
    
    def create_sample_greeks_data(self, **kwargs):
        """Create sample GreeksData for testing."""
        defaults = {
            'strike': 100.0,
            'expiry': datetime.now().date(),
            'time_to_expiry': 0.25,  # 3 months
            'underlying_price': 105.0,
            'risk_free_rate': 0.05,
            'volatility': 0.20,
            'option_type': 'call'
        }
        defaults.update(kwargs)
        return GreeksData(**defaults)
    
    def test_calculator_initialization(self):
        """Test GreeksCalculator initialization."""
        assert self.calculator.min_time_to_expiry == 1/365
        assert self.calculator.min_volatility == 0.001
        assert self.calculator.max_volatility == 5.0
    
    @patch('GreeksLandscape.greeks_calculator.performance_monitor')
    def test_calculate_all_greeks_basic(self, mock_monitor):
        """Test basic Greeks calculation."""
        greeks_data = self.create_sample_greeks_data()
        
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # Check that Greeks were calculated
        assert result.delta is not None
        assert result.gamma is not None
        assert result.theta is not None
        assert result.vega is not None
        assert result.rho is not None
        
        # Check reasonable ranges for call option
        assert 0 <= result.delta <= 1  # Call delta should be between 0 and 1
        assert result.gamma >= 0  # Gamma should be non-negative
        assert result.vega >= 0  # Vega should be non-negative
    
    @patch('GreeksLandscape.greeks_calculator.performance_monitor')
    def test_calculate_put_greeks(self, mock_monitor):
        """Test Greeks calculation for put options."""
        greeks_data = self.create_sample_greeks_data(option_type='put')
        
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # Check that Greeks were calculated
        assert result.delta is not None
        assert result.gamma is not None
        assert result.theta is not None
        assert result.vega is not None
        assert result.rho is not None
        
        # Check reasonable ranges for put option
        assert -1 <= result.delta <= 0  # Put delta should be between -1 and 0
        assert result.gamma >= 0  # Gamma should be non-negative
        assert result.vega >= 0  # Vega should be non-negative
    
    @patch('GreeksLandscape.greeks_calculator.performance_monitor')
    def test_caching_effectiveness(self, mock_monitor):
        """Test that caching improves performance."""
        greeks_data = self.create_sample_greeks_data()
        
        # First calculation (cache miss)
        start_time = time.time()
        result1 = self.calculator.calculate_all_greeks(greeks_data)
        first_duration = time.time() - start_time
        
        # Second calculation (cache hit)
        start_time = time.time()
        result2 = self.calculator.calculate_all_greeks(greeks_data)
        second_duration = time.time() - start_time
        
        # Results should be identical
        assert result1.delta == result2.delta
        assert result1.gamma == result2.gamma
        assert result1.theta == result2.theta
        assert result1.vega == result2.vega
        assert result1.rho == result2.rho
        
        # Second call should be faster (cached)
        assert second_duration < first_duration
    
    def test_input_validation(self):
        """Test input validation."""
        # Test with invalid underlying price
        invalid_data = self.create_sample_greeks_data(underlying_price=-10.0)
        
        with pytest.raises(ValidationError):
            self.calculator.calculate_all_greeks(invalid_data)
        
        # Test with invalid strike
        invalid_data = self.create_sample_greeks_data(strike=0.0)
        
        with pytest.raises(ValidationError):
            self.calculator.calculate_all_greeks(invalid_data)
        
        # Test with invalid time to expiry
        invalid_data = self.create_sample_greeks_data(time_to_expiry=-0.1)
        
        with pytest.raises(ValidationError):
            self.calculator.calculate_all_greeks(invalid_data)
    
    def test_detailed_input_validation(self):
        """Test detailed input validation."""
        # Test with None values
        invalid_data = self.create_sample_greeks_data(underlying_price=None)
        
        with pytest.raises(ValidationError) as exc_info:
            self.calculator.calculate_all_greeks(invalid_data)
        
        assert "Underlying price is required" in str(exc_info.value)
        
        # Test with invalid option type
        invalid_data = self.create_sample_greeks_data(option_type='invalid')
        
        with pytest.raises(ValidationError) as exc_info:
            self.calculator.calculate_all_greeks(invalid_data)
        
        assert "Option type must be 'call' or 'put'" in str(exc_info.value)
    
    def test_edge_cases(self):
        """Test edge cases in Greeks calculation."""
        # Very short time to expiry
        short_expiry_data = self.create_sample_greeks_data(time_to_expiry=1/365)
        result = self.calculator.calculate_all_greeks(short_expiry_data)
        
        # Should still calculate without errors
        assert result.delta is not None
        assert result.gamma is not None
        
        # Very low volatility
        low_vol_data = self.create_sample_greeks_data(volatility=0.001)
        result = self.calculator.calculate_all_greeks(low_vol_data)
        
        # Should still calculate without errors
        assert result.delta is not None
        assert result.vega is not None
    
    def test_batch_greeks_calculation(self):
        """Test batch Greeks calculation."""
        greeks_data_list = [
            self.create_sample_greeks_data(strike=95.0),
            self.create_sample_greeks_data(strike=100.0),
            self.create_sample_greeks_data(strike=105.0),
        ]
        
        results = self.calculator.calculate_batch_greeks(greeks_data_list)
        
        assert len(results) == 3
        for result in results:
            assert result.delta is not None
            assert result.gamma is not None
            assert result.theta is not None
            assert result.vega is not None
            assert result.rho is not None
    
    def test_cache_invalidation(self):
        """Test cache invalidation functionality."""
        greeks_data = self.create_sample_greeks_data()
        
        # Calculate to populate cache
        self.calculator.calculate_all_greeks(greeks_data)
        
        # Verify cache has entries
        stats = self.calculator.get_cache_stats()
        assert stats['total_entries'] > 0
        
        # Invalidate cache
        self.calculator.invalidate_cache()
        
        # Verify cache is empty
        stats = self.calculator.get_cache_stats()
        assert stats['total_entries'] == 0
    
    def test_cache_statistics(self):
        """Test cache statistics functionality."""
        greeks_data = self.create_sample_greeks_data()
        
        # Clear cache first
        self.calculator.invalidate_cache()
        
        # First calculation (miss)
        self.calculator.calculate_all_greeks(greeks_data)
        
        # Second calculation (hit)
        self.calculator.calculate_all_greeks(greeks_data)
        
        stats = self.calculator.get_cache_stats()
        
        assert 'total_entries' in stats
        assert 'valid_entries' in stats
        assert 'cache_hit_ratio' in stats
        assert stats['cache_hit_ratio'] > 0  # Should have some hits
    
    @patch('GreeksLandscape.greeks_calculator.norm.cdf')
    def test_calculation_error_handling(self, mock_cdf):
        """Test error handling in calculations."""
        # Mock norm.cdf to raise an exception
        mock_cdf.side_effect = Exception("Math error")
        
        greeks_data = self.create_sample_greeks_data()
        
        with pytest.raises(CalculationError):
            self.calculator.calculate_all_greeks(greeks_data)
    
    def test_clear_expired_cache(self):
        """Test clearing expired cache entries."""
        # Add some entries to cache
        greeks_data = self.create_sample_greeks_data()
        self.calculator.calculate_all_greeks(greeks_data)
        
        # Manually expire cache entries
        for key in _cache_manager.cache_timestamps:
            _cache_manager.cache_timestamps[key] = datetime.now() - timedelta(hours=2)
        
        # Clear expired entries
        cleared_count = self.calculator.clear_expired_cache()
        
        assert cleared_count > 0
        
        # Cache should be empty now
        stats = self.calculator.get_cache_stats()
        assert stats['total_entries'] == 0


class TestGreeksCalculatorMathematical:
    """Test mathematical correctness of Greeks calculations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = GreeksCalculator()
    
    def create_sample_greeks_data(self, **kwargs):
        """Create sample GreeksData for testing."""
        defaults = {
            'strike': 100.0,
            'expiry': datetime.now().date(),
            'time_to_expiry': 0.25,  # 3 months
            'underlying_price': 100.0,  # At-the-money
            'risk_free_rate': 0.05,
            'volatility': 0.20,
            'option_type': 'call'
        }
        defaults.update(kwargs)
        return GreeksData(**defaults)
    
    def test_atm_call_delta_approximately_half(self):
        """Test that at-the-money call delta is approximately 0.5."""
        atm_data = self.create_sample_greeks_data()
        result = self.calculator.calculate_all_greeks(atm_data)
        
        # ATM call delta should be around 0.5
        assert 0.4 <= result.delta <= 0.6
    
    def test_put_call_parity_delta(self):
        """Test put-call parity for delta."""
        call_data = self.create_sample_greeks_data(option_type='call')
        put_data = self.create_sample_greeks_data(option_type='put')
        
        call_result = self.calculator.calculate_all_greeks(call_data)
        put_result = self.calculator.calculate_all_greeks(put_data)
        
        # Put delta = Call delta - 1
        expected_put_delta = call_result.delta - 1
        assert abs(put_result.delta - expected_put_delta) < 0.001
    
    def test_gamma_symmetry(self):
        """Test that gamma is the same for calls and puts."""
        call_data = self.create_sample_greeks_data(option_type='call')
        put_data = self.create_sample_greeks_data(option_type='put')
        
        call_result = self.calculator.calculate_all_greeks(call_data)
        put_result = self.calculator.calculate_all_greeks(put_data)
        
        # Gamma should be the same for calls and puts
        assert abs(call_result.gamma - put_result.gamma) < 0.001
    
    def test_vega_symmetry(self):
        """Test that vega is the same for calls and puts."""
        call_data = self.create_sample_greeks_data(option_type='call')
        put_data = self.create_sample_greeks_data(option_type='put')
        
        call_result = self.calculator.calculate_all_greeks(call_data)
        put_result = self.calculator.calculate_all_greeks(put_data)
        
        # Vega should be the same for calls and puts
        assert abs(call_result.vega - put_result.vega) < 0.001
    
    def test_theta_time_decay(self):
        """Test that theta represents time decay."""
        greeks_data = self.create_sample_greeks_data()
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # Theta should be negative for long options (time decay)
        assert result.theta < 0


@pytest.mark.performance
class TestGreeksCalculatorPerformance:
    """Performance tests for Greeks calculator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = GreeksCalculator()
    
    def create_sample_greeks_data(self, **kwargs):
        """Create sample GreeksData for testing."""
        defaults = {
            'strike': 100.0,
            'expiry': datetime.now().date(),
            'time_to_expiry': 0.25,
            'underlying_price': 105.0,
            'risk_free_rate': 0.05,
            'volatility': 0.20,
            'option_type': 'call'
        }
        defaults.update(kwargs)
        return GreeksData(**defaults)
    
    def test_single_calculation_performance(self):
        """Test performance of single Greeks calculation."""
        greeks_data = self.create_sample_greeks_data()
        
        start_time = time.time()
        result = self.calculator.calculate_all_greeks(greeks_data)
        duration = time.time() - start_time
        
        # Should complete within 100ms
        assert duration < 0.1
        assert result.delta is not None
    
    def test_batch_calculation_performance(self):
        """Test performance of batch Greeks calculation."""
        # Create 100 different options
        greeks_data_list = [
            self.create_sample_greeks_data(strike=90 + i)
            for i in range(100)
        ]
        
        start_time = time.time()
        results = self.calculator.calculate_batch_greeks(greeks_data_list)
        duration = time.time() - start_time
        
        # Should complete within 2 seconds
        assert duration < 2.0
        assert len(results) == 100
        
        # All should have calculated Greeks
        for result in results:
            assert result.delta is not None
    
    def test_cache_performance_improvement(self):
        """Test that caching significantly improves performance."""
        greeks_data = self.create_sample_greeks_data()
        
        # Clear cache
        self.calculator.invalidate_cache()
        
        # Time first calculation (cache miss)
        start_time = time.time()
        result1 = self.calculator.calculate_all_greeks(greeks_data)
        first_duration = time.time() - start_time
        
        # Time second calculation (cache hit)
        start_time = time.time()
        result2 = self.calculator.calculate_all_greeks(greeks_data)
        second_duration = time.time() - start_time
        
        # Cache hit should be at least 2x faster
        assert second_duration < first_duration / 2
        assert result1.delta == result2.delta