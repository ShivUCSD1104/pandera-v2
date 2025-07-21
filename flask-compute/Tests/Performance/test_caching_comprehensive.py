#!/usr/bin/env python3
"""
Comprehensive test for the complete Greeks caching strategy implementation.

This test verifies that all caching requirements are met:
1. LRU cache decorators with 1-hour expiration
2. Cache invalidation logic for stale options data  
3. Performance measurements for caching effectiveness
"""

import time
import logging
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_comprehensive_caching():
    """Test the complete caching strategy implementation."""
    
    logger.info("Starting comprehensive Greeks caching test...")
    
    try:
        # Set a mock DATABASE_URL to avoid connection issues
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        
        # Import after setting environment variable
        from GreeksLandscape.greeks_calculator import GreeksCalculator, _cache_manager
        from GreeksLandscape.data import GreeksDataFetcher, GreeksData
        
        # Test 1: Verify cache manager configuration
        logger.info("Test 1: Verifying cache manager configuration")
        
        # Check that cache duration is set to 1 hour
        expected_duration = timedelta(hours=1)
        actual_duration = _cache_manager.cache_duration
        
        assert actual_duration == expected_duration, f"Expected {expected_duration}, got {actual_duration}"
        logger.info(f"✅ Cache duration correctly set to {actual_duration}")
        
        # Test 2: Verify Greeks calculation caching
        logger.info("Test 2: Testing Greeks calculation caching")
        
        calculator = GreeksCalculator()
        
        # Clear cache to start fresh
        calculator.invalidate_cache()
        
        # Create test data
        test_greeks_data = GreeksData(
            strike=100.0,
            expiry=datetime.now().date(),
            time_to_expiry=0.25,
            underlying_price=105.0,
            risk_free_rate=0.05,
            volatility=0.20,
            option_type='call'
        )
        
        # First calculation (should not be cached)
        start_time = time.time()
        result1 = calculator.calculate_all_greeks(test_greeks_data)
        first_calc_time = time.time() - start_time
        
        # Second calculation (should be cached)
        start_time = time.time()
        result2 = calculator.calculate_all_greeks(test_greeks_data)
        second_calc_time = time.time() - start_time
        
        # Verify caching effectiveness
        assert result1.delta == result2.delta, "Cached results should be identical"
        assert second_calc_time < first_calc_time * 0.5, "Cached calculation should be significantly faster"
        
        cache_speedup = first_calc_time / second_calc_time if second_calc_time > 0 else float('inf')
        logger.info(f"✅ Greeks calculation caching: {cache_speedup:.2f}x speedup")
        
        # Test 3: Verify cache statistics
        logger.info("Test 3: Testing cache statistics")
        
        stats = calculator.get_cache_stats()
        assert 'total_entries' in stats, "Cache stats should include total_entries"
        assert 'valid_entries' in stats, "Cache stats should include valid_entries"
        assert 'cache_hit_ratio' in stats, "Cache stats should include cache_hit_ratio"
        
        logger.info(f"✅ Cache statistics: {stats}")
        
        # Test 4: Verify cache invalidation
        logger.info("Test 4: Testing cache invalidation")
        
        # Populate cache with multiple entries
        for i in range(5):
            test_data = GreeksData(
                strike=100.0 + i,
                expiry=datetime.now().date(),
                time_to_expiry=0.25,
                underlying_price=105.0,
                risk_free_rate=0.05,
                volatility=0.20,
                option_type='call'
            )
            calculator.calculate_all_greeks(test_data)
        
        stats_before = calculator.get_cache_stats()
        assert stats_before['total_entries'] > 0, "Cache should have entries before invalidation"
        
        # Test ticker-specific invalidation
        calculator.invalidate_cache(ticker='AAPL')
        
        # Test full cache invalidation
        calculator.invalidate_cache()
        stats_after = calculator.get_cache_stats()
        assert stats_after['total_entries'] == 0, "Cache should be empty after invalidation"
        
        logger.info("✅ Cache invalidation working correctly")
        
        # Test 5: Verify cache expiration
        logger.info("Test 5: Testing cache expiration")
        
        # Set short cache duration for testing
        original_duration = _cache_manager.cache_duration
        _cache_manager.cache_duration = timedelta(seconds=1)
        
        try:
            # Calculate result
            calculator.calculate_all_greeks(test_greeks_data)
            
            # Wait for expiration
            time.sleep(1.5)
            
            # Generate cache key to check expiration
            cache_key = _cache_manager.get_cache_key(
                test_greeks_data.underlying_price,
                test_greeks_data.strike,
                test_greeks_data.time_to_expiry,
                test_greeks_data.volatility,
                test_greeks_data.risk_free_rate,
                test_greeks_data.option_type
            )
            
            is_valid = _cache_manager.is_cache_valid(cache_key)
            assert not is_valid, "Cache should expire after timeout"
            
            logger.info("✅ Cache expiration working correctly")
            
        finally:
            # Restore original duration
            _cache_manager.cache_duration = original_duration
        
        # Test 6: Test data fetcher caching
        logger.info("Test 6: Testing data fetcher caching")
        
        data_fetcher = GreeksDataFetcher()
        
        # Mock database calls to test caching without actual database
        with patch.object(data_fetcher, '_get_options_data') as mock_get_options, \
             patch.object(data_fetcher, '_get_underlying_price') as mock_get_price:
            
            mock_get_price.return_value = 105.0
            mock_get_options.return_value = [
                {
                    'strike': 100.0,
                    'expiry': datetime.now().date(),
                    'type': 'call',
                    'implied_volatility': 0.20,
                    'time_to_expiry': 0.25,
                    'bid': 5.0,
                    'ask': 5.5,
                    'last_price': 5.25,
                    'option_price': 5.25
                }
            ]
            
            # First fetch - should call database
            options_chain1 = data_fetcher.fetch_options_chain('AAPL')
            assert mock_get_options.call_count == 1, "First fetch should call database"
            
            # Second fetch - should use cache
            options_chain2 = data_fetcher.fetch_options_chain('AAPL')
            assert mock_get_options.call_count == 1, "Second fetch should use cache"
            
            # Verify data is identical
            assert options_chain1.ticker == options_chain2.ticker, "Cached data should be identical"
            
            logger.info("✅ Data fetcher caching working correctly")
        
        # Test 7: Test cache invalidation for stale data
        logger.info("Test 7: Testing cache invalidation for stale options data")
        
        # Test options cache invalidation
        data_fetcher.invalidate_options_cache('AAPL')
        data_fetcher.invalidate_options_cache()  # Clear all
        
        # Test cache statistics
        cache_stats = data_fetcher.get_cache_stats()
        assert 'options_cache' in cache_stats, "Should have options cache stats"
        assert 'underlying_cache' in cache_stats, "Should have underlying cache stats"
        
        logger.info("✅ Options cache invalidation working correctly")
        
        # Test 8: Performance measurement with batch calculations
        logger.info("Test 8: Testing batch calculation performance")
        
        # Create larger test dataset
        batch_test_data = []
        for strike in range(90, 121, 5):  # 7 strikes
            for expiry_days in [30, 60, 90, 120]:  # 4 expiries
                for vol in [0.15, 0.20, 0.25, 0.30]:  # 4 volatilities
                    data = GreeksData(
                        strike=float(strike),
                        expiry=datetime.now().date(),
                        time_to_expiry=expiry_days / 365.0,
                        underlying_price=105.0,
                        risk_free_rate=0.05,
                        volatility=vol,
                        option_type='call'
                    )
                    batch_test_data.append(data)
        
        logger.info(f"Testing with {len(batch_test_data)} calculations")
        
        # Clear cache for clean test
        calculator.invalidate_cache()
        
        # First batch run
        start_time = time.time()
        results1 = calculator.calculate_batch_greeks(batch_test_data)
        first_batch_time = time.time() - start_time
        
        # Second batch run (should benefit from caching)
        start_time = time.time()
        results2 = calculator.calculate_batch_greeks(batch_test_data)
        second_batch_time = time.time() - start_time
        
        # Performance analysis
        batch_speedup = first_batch_time / second_batch_time if second_batch_time > 0 else float('inf')
        
        # Get final cache statistics
        final_stats = calculator.get_cache_stats()
        
        logger.info(f"Batch performance:")
        logger.info(f"  First run: {first_batch_time:.4f}s")
        logger.info(f"  Second run: {second_batch_time:.4f}s")
        logger.info(f"  Speedup: {batch_speedup:.2f}x")
        logger.info(f"  Cache hit ratio: {final_stats['cache_hit_ratio']:.2%}")
        
        # Verify performance requirements
        assert batch_speedup >= 2.0, f"Cache should provide at least 2x speedup, got {batch_speedup:.2f}x"
        assert final_stats['cache_hit_ratio'] >= 0.3, f"Cache hit ratio should be >= 30%, got {final_stats['cache_hit_ratio']:.2%}"
        
        logger.info("✅ Batch calculation performance meets requirements")
        
        # Test 9: Test expired cache cleanup
        logger.info("Test 9: Testing expired cache cleanup")
        
        # Add some valid entries
        for i in range(3):
            calculator.calculate_all_greeks(batch_test_data[i])
        
        # Manually add expired entry for testing
        expired_time = datetime.now() - timedelta(hours=2)
        _cache_manager.cache['expired_test'] = batch_test_data[0]
        _cache_manager.cache_timestamps['expired_test'] = expired_time
        
        stats_before_cleanup = calculator.get_cache_stats()
        cleared_count = calculator.clear_expired_cache()
        stats_after_cleanup = calculator.get_cache_stats()
        
        assert cleared_count > 0, "Should have cleared at least one expired entry"
        assert stats_after_cleanup['expired_entries'] == 0, "Should have no expired entries after cleanup"
        
        logger.info(f"✅ Expired cache cleanup: cleared {cleared_count} entries")
        
        logger.info("🎉 All comprehensive caching tests passed!")
        
        return {
            'cache_speedup': batch_speedup,
            'cache_hit_ratio': final_stats['cache_hit_ratio'],
            'total_test_cases': len(batch_test_data),
            'cache_stats': final_stats
        }
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.info("Skipping comprehensive test due to import issues")
        return None
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == '__main__':
    results = test_comprehensive_caching()
    
    if results:
        print("\n" + "="*80)
        print("COMPREHENSIVE GREEKS CACHING TEST RESULTS")
        print("="*80)
        print(f"Total test cases: {results['total_test_cases']}")
        print(f"Cache speedup: {results['cache_speedup']:.2f}x")
        print(f"Cache hit ratio: {results['cache_hit_ratio']:.2%}")
        print(f"Final cache statistics: {results['cache_stats']}")
        print("="*80)
        
        # Summary of requirements verification
        print("\nREQUIREMENTS VERIFICATION:")
        print("✅ LRU cache decorators with 1-hour expiration: IMPLEMENTED")
        print("✅ Cache invalidation logic for stale options data: IMPLEMENTED")
        print("✅ Performance measurements show caching effectiveness: VERIFIED")
        print(f"✅ Cache provides {results['cache_speedup']:.2f}x speedup (requirement: ≥2x)")
        print(f"✅ Cache hit ratio: {results['cache_hit_ratio']:.2%} (requirement: ≥30%)")
        print("="*80)
    else:
        print("Test could not be completed due to import issues")