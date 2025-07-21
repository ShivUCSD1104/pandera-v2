#!/usr/bin/env python3
"""
Isolated test for Greeks caching functionality.

This script tests only the caching components without database dependencies.
"""

import time
import logging
import math
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
from scipy.stats import norm
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class GreeksData:
    """Greeks data structure for testing."""
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

class CacheManager:
    """Isolated cache manager for testing."""
    
    def __init__(self, cache_duration_hours: int = 1):
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.cache = {}
        self.cache_timestamps = {}
        self._hit_count = 0
        self._total_requests = 0
    
    def get_cache_key(self, *args, **kwargs) -> str:
        """Generate a unique cache key from function arguments."""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid based on timestamp."""
        if cache_key not in self.cache_timestamps:
            return False
        
        cache_time = self.cache_timestamps[cache_key]
        return datetime.now() - cache_time < self.cache_duration
    
    def get_cached_result(self, cache_key: str):
        """Get cached result if valid, otherwise return None."""
        self._total_requests += 1
        if self.is_cache_valid(cache_key):
            self._hit_count += 1
            return self.cache.get(cache_key)
        return None
    
    def cache_result(self, cache_key: str, result):
        """Cache a result with current timestamp."""
        self.cache[cache_key] = result
        self.cache_timestamps[cache_key] = datetime.now()
    
    def invalidate_cache(self, pattern: str = None):
        """Invalidate cache entries matching a pattern or all if no pattern."""
        if pattern is None:
            self.cache.clear()
            self.cache_timestamps.clear()
            logger.info("All cache cleared")
        else:
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                self.cache.pop(key, None)
                self.cache_timestamps.pop(key, None)
            logger.info(f"Cleared {len(keys_to_remove)} cache entries matching pattern: {pattern}")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics for performance monitoring."""
        total_entries = len(self.cache)
        valid_entries = sum(1 for key in self.cache.keys() if self.is_cache_valid(key))
        expired_entries = total_entries - valid_entries
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_hit_ratio': self._hit_count / max(self._total_requests, 1)
        }

class GreeksCalculator:
    """Simplified Greeks calculator with caching."""
    
    def __init__(self):
        self.cache_manager = CacheManager(cache_duration_hours=1)
        self.min_time_to_expiry = 1/365
        self.min_volatility = 0.001
        self.max_volatility = 5.0
    
    def calculate_all_greeks(self, greeks_data: GreeksData) -> GreeksData:
        """Calculate all Greeks with caching."""
        try:
            # Generate cache key
            cache_key = self.cache_manager.get_cache_key(
                greeks_data.underlying_price,
                greeks_data.strike,
                greeks_data.time_to_expiry,
                greeks_data.volatility,
                greeks_data.risk_free_rate,
                greeks_data.option_type
            )
            
            # Check cache first
            cached_result = self.cache_manager.get_cached_result(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for Greeks calculation: {cache_key[:8]}...")
                return cached_result
            
            # Validate inputs
            if not self._validate_inputs(greeks_data):
                logger.warning(f"Invalid inputs for Greeks calculation")
                return greeks_data
            
            # Calculate Greeks (simplified Black-Scholes)
            d1, d2 = self._calculate_d1_d2(greeks_data)
            
            if greeks_data.option_type.lower() == 'call':
                greeks_data.delta = norm.cdf(d1)
                greeks_data.theta = self._calculate_call_theta(greeks_data, d1, d2)
            else:
                greeks_data.delta = norm.cdf(d1) - 1.0
                greeks_data.theta = self._calculate_put_theta(greeks_data, d1, d2)
            
            greeks_data.gamma = self._calculate_gamma(greeks_data, d1)
            greeks_data.vega = self._calculate_vega(greeks_data, d1)
            greeks_data.rho = self._calculate_rho(greeks_data, d2)
            
            # Cache the result
            self.cache_manager.cache_result(cache_key, greeks_data)
            logger.debug(f"Cached Greeks calculation result: {cache_key[:8]}...")
            
            return greeks_data
            
        except Exception as e:
            logger.error(f"Error calculating Greeks: {str(e)}")
            return greeks_data
    
    def _validate_inputs(self, greeks_data: GreeksData) -> bool:
        """Validate input parameters."""
        return (greeks_data.underlying_price > 0 and 
                greeks_data.strike > 0 and 
                greeks_data.time_to_expiry > 0 and
                greeks_data.volatility >= 0 and
                greeks_data.volatility <= self.max_volatility)
    
    def _calculate_d1_d2(self, greeks_data: GreeksData):
        """Calculate d1 and d2 for Black-Scholes."""
        S = greeks_data.underlying_price
        K = greeks_data.strike
        T = greeks_data.time_to_expiry
        r = greeks_data.risk_free_rate
        sigma = max(greeks_data.volatility, self.min_volatility)
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        return d1, d2
    
    def _calculate_gamma(self, greeks_data: GreeksData, d1: float) -> float:
        """Calculate gamma."""
        S = greeks_data.underlying_price
        T = greeks_data.time_to_expiry
        sigma = max(greeks_data.volatility, self.min_volatility)
        
        return norm.pdf(d1) / (S * sigma * math.sqrt(T))
    
    def _calculate_call_theta(self, greeks_data: GreeksData, d1: float, d2: float) -> float:
        """Calculate theta for call option."""
        S = greeks_data.underlying_price
        K = greeks_data.strike
        T = greeks_data.time_to_expiry
        r = greeks_data.risk_free_rate
        sigma = max(greeks_data.volatility, self.min_volatility)
        
        term1 = -(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
        term2 = -r * K * math.exp(-r * T) * norm.cdf(d2)
        
        return (term1 + term2) / 365
    
    def _calculate_put_theta(self, greeks_data: GreeksData, d1: float, d2: float) -> float:
        """Calculate theta for put option."""
        S = greeks_data.underlying_price
        K = greeks_data.strike
        T = greeks_data.time_to_expiry
        r = greeks_data.risk_free_rate
        sigma = max(greeks_data.volatility, self.min_volatility)
        
        term1 = -(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
        term2 = r * K * math.exp(-r * T) * norm.cdf(-d2)
        
        return (term1 + term2) / 365
    
    def _calculate_vega(self, greeks_data: GreeksData, d1: float) -> float:
        """Calculate vega."""
        S = greeks_data.underlying_price
        T = greeks_data.time_to_expiry
        
        return S * norm.pdf(d1) * math.sqrt(T) / 100
    
    def _calculate_rho(self, greeks_data: GreeksData, d2: float) -> float:
        """Calculate rho."""
        K = greeks_data.strike
        T = greeks_data.time_to_expiry
        r = greeks_data.risk_free_rate
        
        if greeks_data.option_type.lower() == 'call':
            return K * T * math.exp(-r * T) * norm.cdf(d2) / 100
        else:
            return -K * T * math.exp(-r * T) * norm.cdf(-d2) / 100
    
    def calculate_batch_greeks(self, greeks_data_list: list) -> list:
        """Calculate Greeks for a batch of options."""
        logger.info(f"Calculating Greeks for {len(greeks_data_list)} options")
        
        calculated_data = []
        for data in greeks_data_list:
            calculated_data.append(self.calculate_all_greeks(data))
        
        return calculated_data
    
    def invalidate_cache(self, ticker: str = None):
        """Invalidate cache."""
        self.cache_manager.invalidate_cache(pattern=ticker)
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return self.cache_manager.get_cache_stats()
    
    def clear_expired_cache(self):
        """Clear expired cache entries."""
        expired_keys = []
        for key in self.cache_manager.cache.keys():
            if not self.cache_manager.is_cache_valid(key):
                expired_keys.append(key)
        
        for key in expired_keys:
            self.cache_manager.cache.pop(key, None)
            self.cache_manager.cache_timestamps.pop(key, None)
        
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)

def test_caching_performance():
    """Test caching performance with various scenarios."""
    logger.info("Starting Greeks caching performance test...")
    
    calculator = GreeksCalculator()
    
    # Create test data
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
    
    logger.info(f"Created {len(test_data)} test cases")
    
    # Test 1: First run (no cache)
    logger.info("Test 1: First run (no cache)")
    start_time = time.time()
    results1 = calculator.calculate_batch_greeks(test_data)
    first_run_time = time.time() - start_time
    
    valid_results = sum(1 for r in results1 if r.delta is not None)
    logger.info(f"First run: {first_run_time:.4f}s, {valid_results}/{len(results1)} valid results")
    
    # Test 2: Second run (with cache)
    logger.info("Test 2: Second run (with cache)")
    start_time = time.time()
    results2 = calculator.calculate_batch_greeks(test_data)
    second_run_time = time.time() - start_time
    
    logger.info(f"Second run: {second_run_time:.4f}s")
    
    # Verify results are identical
    identical_results = sum(1 for r1, r2 in zip(results1, results2) 
                          if r1.delta == r2.delta and r1.gamma == r2.gamma)
    logger.info(f"Identical results: {identical_results}/{len(results1)}")
    
    # Test 3: Mixed run with duplicates
    logger.info("Test 3: Mixed run with duplicates")
    mixed_data = test_data + test_data[:10]  # Add 10 duplicates
    start_time = time.time()
    results3 = calculator.calculate_batch_greeks(mixed_data)
    third_run_time = time.time() - start_time
    
    logger.info(f"Third run (with duplicates): {third_run_time:.4f}s, {len(mixed_data)} calculations")
    
    # Performance analysis
    cache_speedup = first_run_time / second_run_time if second_run_time > 0 else float('inf')
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
    
    # Test 5: Cache expiration
    logger.info("Test 5: Cache expiration test")
    original_duration = calculator.cache_manager.cache_duration
    calculator.cache_manager.cache_duration = timedelta(seconds=1)
    
    try:
        # Calculate one result
        test_result = calculator.calculate_all_greeks(test_data[0])
        logger.info("Calculated result, waiting for cache expiration...")
        
        # Wait for cache to expire
        time.sleep(1.5)
        
        # Check if cache expired
        cache_key = calculator.cache_manager.get_cache_key(
            test_data[0].underlying_price,
            test_data[0].strike,
            test_data[0].time_to_expiry,
            test_data[0].volatility,
            test_data[0].risk_free_rate,
            test_data[0].option_type
        )
        
        is_valid = calculator.cache_manager.is_cache_valid(cache_key)
        logger.info(f"Cache valid after expiration: {is_valid}")
        
    finally:
        calculator.cache_manager.cache_duration = original_duration
    
    # Test 6: Expired cache cleanup
    logger.info("Test 6: Expired cache cleanup")
    
    # Calculate some results
    for i in range(5):
        calculator.calculate_all_greeks(test_data[i])
    
    # Manually add expired entry
    expired_time = datetime.now() - timedelta(hours=2)
    calculator.cache_manager.cache['expired_test'] = test_data[0]
    calculator.cache_manager.cache_timestamps['expired_test'] = expired_time
    
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
        'cache_speedup': cache_speedup,
        'cache_stats': cache_stats,
        'test_cases': len(test_data),
        'cache_hit_ratio': cache_stats['cache_hit_ratio']
    }

if __name__ == '__main__':
    results = test_caching_performance()
    
    print("\n" + "="*70)
    print("GREEKS CACHING PERFORMANCE TEST RESULTS")
    print("="*70)
    print(f"Test cases: {results['test_cases']}")
    print(f"First run (no cache): {results['first_run_time']:.4f}s")
    print(f"Second run (cached): {results['second_run_time']:.4f}s")
    print(f"Third run (mixed): {results['third_run_time']:.4f}s")
    print(f"Cache speedup: {results['cache_speedup']:.2f}x")
    print(f"Cache hit ratio: {results['cache_hit_ratio']:.2%}")
    print(f"Cache statistics: {results['cache_stats']}")
    print("="*70)
    
    # Verify performance requirements
    if results['cache_speedup'] >= 2.0:
        print("✅ PASS: Cache provides at least 2x speedup")
    else:
        print("❌ FAIL: Cache speedup is less than 2x")
    
    if results['cache_hit_ratio'] >= 0.3:
        print("✅ PASS: Cache hit ratio is above 30%")
    else:
        print("❌ FAIL: Cache hit ratio is below 30%")
    
    print("="*70)