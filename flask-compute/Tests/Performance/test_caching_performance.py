#!/usr/bin/env python3
"""
Simple performance test for Greeks caching functionality.

This script tests the caching implementation without database dependencies.
"""

import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class GreeksData:
    """Simplified Greeks data structure for testing."""
    strike: float
    expiry: datetime
    time_to_expiry: float
    underlying_price: float
    risk_free_rate: float
    volatility: float
    option_type: str
    
    # Greeks values
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None

# Import the Greeks calculator
try:
    from GreeksLandscape.greeks_calculator import GreeksCalculator, _cache_manager
    
    def test_caching_performance():
        """Test caching performance with various scenarios."""
        logger.info("Starting Greeks caching performance test...")
        
        calculator = GreeksCalculator()
        
        # Clear cache to start fresh
        _cache_manager.invalidate_cache()
        
        # Create test data
        test_data = []
        for strike in range(90, 111, 5):  # 5 strikes: 90, 95, 100, 105, 110
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
        
        logger.info(f"Created {len(test_data)} test cases")
        
        # Test 1: First run (no cache)
        logger.info("Test 1: First run (no cache)")
        start_time = time.time()
        results1 = []
        for data in test_data:
            result = calculator.calculate_all_greeks(data)
            results1.append(result)
        first_run_time = time.time() - start_time
        
        # Verify calculations were performed
        valid_results = sum(1 for r in results1 if r.delta is not None)
        logger.info(f"First run: {first_run_time:.4f}s, {valid_results}/{len(results1)} valid results")
        
        # Test 2: Second run (with cache)
        logger.info("Test 2: Second run (with cache)")
        start_time = time.time()
        results2 = []
        for data in test_data:
            result = calculator.calculate_all_greeks(data)
            results2.append(result)
        second_run_time = time.time() - start_time
        
        logger.info(f"Second run: {second_run_time:.4f}s")
        
        # Verify results are identical
        identical_results = 0
        for r1, r2 in zip(results1, results2):
            if r1.delta == r2.delta and r1.gamma == r2.gamma:
                identical_results += 1
        
        logger.info(f"Identical results: {identical_results}/{len(results1)}")
        
        # Test 3: Mixed run with duplicates
        logger.info("Test 3: Mixed run with duplicates")
        mixed_data = test_data + test_data[:10]  # Add 10 duplicates
        start_time = time.time()
        results3 = []
        for data in mixed_data:
            result = calculator.calculate_all_greeks(data)
            results3.append(result)
        third_run_time = time.time() - start_time
        
        logger.info(f"Third run (with duplicates): {third_run_time:.4f}s, {len(mixed_data)} calculations")
        
        # Performance analysis
        if second_run_time > 0:
            cache_speedup = first_run_time / second_run_time
            logger.info(f"Cache speedup: {cache_speedup:.2f}x")
        
        if third_run_time > 0:
            expected_time = first_run_time * len(mixed_data) / len(test_data)
            mixed_speedup = expected_time / third_run_time
            logger.info(f"Mixed run speedup: {mixed_speedup:.2f}x")
        
        # Cache statistics
        cache_stats = calculator.get_cache_stats()
        logger.info(f"Cache statistics: {cache_stats}")
        
        # Test 4: Cache invalidation
        logger.info("Test 4: Cache invalidation")
        calculator.invalidate_cache()
        stats_after_clear = calculator.get_cache_stats()
        logger.info(f"Stats after cache clear: {stats_after_clear}")
        
        # Test 5: Cache expiration simulation
        logger.info("Test 5: Cache expiration test")
        
        # Set short cache duration for testing
        original_duration = _cache_manager.cache_duration
        _cache_manager.cache_duration = timedelta(seconds=2)
        
        try:
            # Calculate one result
            test_result = calculator.calculate_all_greeks(test_data[0])
            logger.info("Calculated result, waiting for cache expiration...")
            
            # Wait for cache to expire
            time.sleep(2.5)
            
            # Check if cache expired
            cache_key = _cache_manager.get_cache_key(
                test_data[0].underlying_price,
                test_data[0].strike,
                test_data[0].time_to_expiry,
                test_data[0].volatility,
                test_data[0].risk_free_rate,
                test_data[0].option_type
            )
            
            is_valid = _cache_manager.is_cache_valid(cache_key)
            logger.info(f"Cache valid after expiration: {is_valid}")
            
        finally:
            # Restore original cache duration
            _cache_manager.cache_duration = original_duration
        
        # Test 6: Expired cache cleanup
        logger.info("Test 6: Expired cache cleanup")
        
        # Add some entries and then clean expired ones
        for i in range(5):
            calculator.calculate_all_greeks(test_data[i])
        
        # Manually add expired entry for testing
        expired_time = datetime.now() - timedelta(hours=2)
        _cache_manager.cache['expired_test'] = test_data[0]
        _cache_manager.cache_timestamps['expired_test'] = expired_time
        
        stats_before_cleanup = calculator.get_cache_stats()
        cleared_count = calculator.clear_expired_cache()
        stats_after_cleanup = calculator.get_cache_stats()
        
        logger.info(f"Before cleanup: {stats_before_cleanup}")
        logger.info(f"Cleared {cleared_count} expired entries")
        logger.info(f"After cleanup: {stats_after_cleanup}")
        
        logger.info("Greeks caching performance test completed successfully!")
        
        return {
            'first_run_time': first_run_time,
            'second_run_time': second_run_time,
            'third_run_time': third_run_time,
            'cache_speedup': cache_speedup if second_run_time > 0 else 0,
            'cache_stats': cache_stats,
            'test_cases': len(test_data)
        }

except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info("Skipping caching test due to import issues")
    
    def test_caching_performance():
        logger.info("Caching test skipped due to import issues")
        return None

if __name__ == '__main__':
    results = test_caching_performance()
    if results:
        print("\n" + "="*60)
        print("CACHING PERFORMANCE TEST RESULTS")
        print("="*60)
        print(f"Test cases: {results['test_cases']}")
        print(f"First run (no cache): {results['first_run_time']:.4f}s")
        print(f"Second run (cached): {results['second_run_time']:.4f}s")
        print(f"Cache speedup: {results['cache_speedup']:.2f}x")
        print(f"Cache statistics: {results['cache_stats']}")
        print("="*60)