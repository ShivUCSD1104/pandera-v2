"""
Test module for Greeks calculation caching functionality.

This module tests the caching strategy implementation including:
- LRU cache decorators with 1-hour expiration
- Cache invalidation logic for stale options data
- Performance measurements for caching effectiveness
"""

import unittest
import time
import logging
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from GreeksLandscape.greeks_calculator import GreeksCalculator, _cache_manager
from GreeksLandscape.data import GreeksDataFetcher, GreeksData

# Set up logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestGreeksCaching(unittest.TestCase):
    """Test cases for Greeks calculation caching functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = GreeksCalculator()
        self.data_fetcher = GreeksDataFetcher()
        
        # Clear caches before each test
        _cache_manager.invalidate_cache()
        self.data_fetcher.invalidate_options_cache()
        
        # Sample Greeks data for testing
        self.sample_greeks_data = GreeksData(
            strike=100.0,
            expiry=datetime.now().date(),
            time_to_expiry=0.25,  # 3 months
            underlying_price=105.0,
            risk_free_rate=0.05,
            volatility=0.20,
            option_type='call'
        )
    
    def test_greeks_calculation_caching(self):
        """Test that Greeks calculations are properly cached."""
        logger.info("Testing Greeks calculation caching...")
        
        # First calculation - should not be cached
        start_time = time.time()
        result1 = self.calculator.calculate_all_greeks(self.sample_greeks_data)
        first_calc_time = time.time() - start_time
        
        # Verify Greeks were calculated
        self.assertIsNotNone(result1.delta)
        self.assertIsNotNone(result1.gamma)
        self.assertIsNotNone(result1.theta)
        self.assertIsNotNone(result1.vega)
        
        # Second calculation with same parameters - should be cached
        start_time = time.time()
        result2 = self.calculator.calculate_all_greeks(self.sample_greeks_data)
        second_calc_time = time.time() - start_time
        
        # Verify results are identical
        self.assertEqual(result1.delta, result2.delta)
        self.assertEqual(result1.gamma, result2.gamma)
        self.assertEqual(result1.theta, result2.theta)
        self.assertEqual(result1.vega, result2.vega)
        
        # Second calculation should be significantly faster (cached)
        self.assertLess(second_calc_time, first_calc_time * 0.5)
        
        logger.info(f"First calculation: {first_calc_time:.4f}s, Second (cached): {second_calc_time:.4f}s")
        logger.info(f"Cache speedup: {first_calc_time / second_calc_time:.2f}x")
    
    def test_cache_expiration(self):
        """Test that cache entries expire after the specified duration."""
        logger.info("Testing cache expiration...")
        
        # Set a very short cache duration for testing
        original_duration = _cache_manager.cache_duration
        _cache_manager.cache_duration = timedelta(seconds=1)
        
        try:
            # First calculation
            result1 = self.calculator.calculate_all_greeks(self.sample_greeks_data)
            
            # Wait for cache to expire
            time.sleep(1.1)
            
            # Check that cache is no longer valid
            cache_key = _cache_manager.get_cache_key(
                self.sample_greeks_data.underlying_price,
                self.sample_greeks_data.strike,
                self.sample_greeks_data.time_to_expiry,
                self.sample_greeks_data.volatility,
                self.sample_greeks_data.risk_free_rate,
                self.sample_greeks_data.option_type
            )
            
            self.assertFalse(_cache_manager.is_cache_valid(cache_key))
            
        finally:
            # Restore original cache duration
            _cache_manager.cache_duration = original_duration
    
    def test_cache_invalidation(self):
        """Test cache invalidation functionality."""
        logger.info("Testing cache invalidation...")
        
        # Calculate Greeks to populate cache
        result1 = self.calculator.calculate_all_greeks(self.sample_greeks_data)
        
        # Verify cache has entries
        cache_stats = self.calculator.get_cache_stats()
        self.assertGreater(cache_stats['total_entries'], 0)
        
        # Invalidate cache
        self.calculator.invalidate_cache()
        
        # Verify cache is empty
        cache_stats = self.calculator.get_cache_stats()
        self.assertEqual(cache_stats['total_entries'], 0)
    
    def test_batch_calculation_caching(self):
        """Test caching effectiveness with batch calculations."""
        logger.info("Testing batch calculation caching...")
        
        # Create multiple Greeks data with some duplicates
        greeks_data_list = []
        for i in range(10):
            data = GreeksData(
                strike=100.0 + i * 5,  # Different strikes
                expiry=datetime.now().date(),
                time_to_expiry=0.25,
                underlying_price=105.0,
                risk_free_rate=0.05,
                volatility=0.20,
                option_type='call'
            )
            greeks_data_list.append(data)
        
        # Add some duplicate entries to test caching
        greeks_data_list.extend(greeks_data_list[:3])
        
        # First batch calculation
        start_time = time.time()
        results1 = self.calculator.calculate_batch_greeks(greeks_data_list)
        first_batch_time = time.time() - start_time
        
        # Second batch calculation (should benefit from caching)
        start_time = time.time()
        results2 = self.calculator.calculate_batch_greeks(greeks_data_list)
        second_batch_time = time.time() - start_time
        
        # Verify results are identical
        self.assertEqual(len(results1), len(results2))
        for r1, r2 in zip(results1, results2):
            self.assertEqual(r1.delta, r2.delta)
        
        # Second batch should be faster due to caching
        self.assertLess(second_batch_time, first_batch_time * 0.8)
        
        logger.info(f"First batch: {first_batch_time:.4f}s, Second batch (cached): {second_batch_time:.4f}s")
        logger.info(f"Batch cache speedup: {first_batch_time / second_batch_time:.2f}x")
    
    def test_options_data_caching(self):
        """Test options data fetching caching."""
        logger.info("Testing options data caching...")
        
        with patch.object(self.data_fetcher, '_get_options_data') as mock_get_options, \
             patch.object(self.data_fetcher, '_get_underlying_price') as mock_get_price:
            
            # Mock return values
            mock_get_price.return_value = 105.0
            mock_get_options.return_value = [
                {
                    'strike': 100.0,
                    'expiry': datetime.now().date(),
                    'type': 'call',
                    'implied_volatility': 0.20,
                    'time_to_expiry': 0.25
                }
            ]
            
            # First fetch - should call database
            options_chain1 = self.data_fetcher.fetch_options_chain('AAPL')
            self.assertEqual(mock_get_options.call_count, 1)
            self.assertEqual(mock_get_price.call_count, 1)
            
            # Second fetch - should use cache
            options_chain2 = self.data_fetcher.fetch_options_chain('AAPL')
            self.assertEqual(mock_get_options.call_count, 1)  # Should not increase
            self.assertEqual(mock_get_price.call_count, 1)    # Should not increase
            
            # Verify data is identical
            self.assertEqual(options_chain1.ticker, options_chain2.ticker)
            self.assertEqual(len(options_chain1.options), len(options_chain2.options))
    
    def test_underlying_price_caching(self):
        """Test underlying price caching functionality."""
        logger.info("Testing underlying price caching...")
        
        with patch.object(self.data_fetcher, '_get_underlying_price') as mock_method:
            # Create a new instance to test the actual caching logic
            original_method = self.data_fetcher.__class__._get_underlying_price
            
            def side_effect(self, ticker):
                # Call the original method but track calls
                return original_method(self, ticker)
            
            mock_method.side_effect = side_effect
            
            # Mock database response
            with patch('GreeksLandscape.data.SessionLocal') as mock_session_local:
                mock_session = MagicMock()
                mock_session_local.return_value = mock_session
                
                mock_record = MagicMock()
                mock_record.close = 105.0
                mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_record
                
                # First call - should hit database
                price1 = self.data_fetcher._get_underlying_price('AAPL')
                
                # Second call - should use cache
                price2 = self.data_fetcher._get_underlying_price('AAPL')
                
                # Verify prices are identical
                self.assertEqual(price1, price2)
                
                # Verify database was only called once
                self.assertEqual(mock_session.query.call_count, 1)
    
    def test_cache_statistics(self):
        """Test cache statistics functionality."""
        logger.info("Testing cache statistics...")
        
        # Initial stats should show empty cache
        stats = self.calculator.get_cache_stats()
        self.assertEqual(stats['total_entries'], 0)
        
        # Calculate some Greeks to populate cache
        for i in range(5):
            data = GreeksData(
                strike=100.0 + i,
                expiry=datetime.now().date(),
                time_to_expiry=0.25,
                underlying_price=105.0,
                risk_free_rate=0.05,
                volatility=0.20,
                option_type='call'
            )
            self.calculator.calculate_all_greeks(data)
        
        # Check stats show populated cache
        stats = self.calculator.get_cache_stats()
        self.assertEqual(stats['total_entries'], 5)
        self.assertGreater(stats['cache_hit_ratio'], 0)
        
        logger.info(f"Cache stats: {stats}")
    
    def test_data_fetcher_cache_statistics(self):
        """Test data fetcher cache statistics."""
        logger.info("Testing data fetcher cache statistics...")
        
        # Initial stats
        stats = self.data_fetcher.get_cache_stats()
        self.assertEqual(stats['options_cache']['total_entries'], 0)
        self.assertEqual(stats['underlying_cache']['total_entries'], 0)
        
        # Add some cache entries manually for testing
        self.data_fetcher.cache['AAPL_None_None'] = {
            'data': MagicMock(),
            'timestamp': datetime.now()
        }
        self.data_fetcher.underlying_cache['AAPL'] = {
            'price': 105.0,
            'timestamp': datetime.now()
        }
        
        # Check updated stats
        stats = self.data_fetcher.get_cache_stats()
        self.assertEqual(stats['options_cache']['total_entries'], 1)
        self.assertEqual(stats['underlying_cache']['total_entries'], 1)
        self.assertEqual(stats['options_cache']['valid_entries'], 1)
        self.assertEqual(stats['underlying_cache']['valid_entries'], 1)
    
    def test_expired_cache_cleanup(self):
        """Test cleanup of expired cache entries."""
        logger.info("Testing expired cache cleanup...")
        
        # Add expired entries to cache
        expired_time = datetime.now() - timedelta(hours=2)
        _cache_manager.cache['expired_key'] = MagicMock()
        _cache_manager.cache_timestamps['expired_key'] = expired_time
        
        # Add valid entry
        _cache_manager.cache['valid_key'] = MagicMock()
        _cache_manager.cache_timestamps['valid_key'] = datetime.now()
        
        # Clean expired cache
        cleared_count = self.calculator.clear_expired_cache()
        
        # Verify expired entry was removed
        self.assertEqual(cleared_count, 1)
        self.assertNotIn('expired_key', _cache_manager.cache)
        self.assertIn('valid_key', _cache_manager.cache)
    
    def test_performance_measurement(self):
        """Test and measure overall caching performance."""
        logger.info("Testing overall caching performance...")
        
        # Create a realistic dataset
        test_data = []
        for strike in range(90, 111, 5):  # 5 strikes
            for expiry_days in [30, 60, 90]:  # 3 expiries
                for vol in [0.15, 0.20, 0.25]:  # 3 volatilities
                    data = GreeksData(
                        strike=float(strike),
                        expiry=datetime.now().date(),
                        time_to_expiry=expiry_days / 365.0,
                        underlying_price=105.0,
                        risk_free_rate=0.05,
                        volatility=vol,
                        option_type='call'
                    )
                    test_data.append(data)
        
        logger.info(f"Testing with {len(test_data)} Greeks calculations")
        
        # First run - no cache
        start_time = time.time()
        results1 = self.calculator.calculate_batch_greeks(test_data)
        first_run_time = time.time() - start_time
        
        # Second run - with cache
        start_time = time.time()
        results2 = self.calculator.calculate_batch_greeks(test_data)
        second_run_time = time.time() - start_time
        
        # Third run - duplicate some calculations
        mixed_data = test_data + test_data[:10]  # Add some duplicates
        start_time = time.time()
        results3 = self.calculator.calculate_batch_greeks(mixed_data)
        third_run_time = time.time() - start_time
        
        # Performance analysis
        cache_speedup = first_run_time / second_run_time if second_run_time > 0 else float('inf')
        mixed_speedup = (first_run_time * len(mixed_data) / len(test_data)) / third_run_time if third_run_time > 0 else float('inf')
        
        logger.info(f"Performance Results:")
        logger.info(f"  First run (no cache): {first_run_time:.4f}s")
        logger.info(f"  Second run (cached): {second_run_time:.4f}s")
        logger.info(f"  Third run (mixed): {third_run_time:.4f}s")
        logger.info(f"  Cache speedup: {cache_speedup:.2f}x")
        logger.info(f"  Mixed speedup: {mixed_speedup:.2f}x")
        
        # Cache should provide significant speedup
        self.assertGreater(cache_speedup, 2.0, "Cache should provide at least 2x speedup")
        
        # Get final cache statistics
        cache_stats = self.calculator.get_cache_stats()
        logger.info(f"Final cache stats: {cache_stats}")
        
        # Verify cache hit ratio is reasonable
        self.assertGreater(cache_stats['cache_hit_ratio'], 0.3, "Cache hit ratio should be > 30%")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)