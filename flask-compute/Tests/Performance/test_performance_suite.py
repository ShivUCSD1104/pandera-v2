"""
Performance testing script for Greeks Landscape optimizations.

This script tests the performance improvements with:
- Large options chains
- Multiple concurrent requests
- Database connection pooling
- Caching effectiveness
- Memory usage optimization
"""

import asyncio
import concurrent.futures
import time
import logging
import statistics
import threading
from typing import List, Dict, Any
import sys
import os

# Add the parent directories to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from GreeksLandscape.main import generate_greeks_landscape_html
from GreeksLandscape.data import GreeksDataFetcher
from GreeksLandscape.greeks_calculator import GreeksCalculator
from GreeksLandscape.performance_monitor import performance_monitor, log_performance_summary
from db import engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceTestSuite:
    """
    Comprehensive performance testing suite for Greeks Landscape optimizations.
    """
    
    def __init__(self):
        self.test_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
        self.results = {}
        
    def run_all_tests(self):
        """Run all performance tests and generate a comprehensive report."""
        logger.info("Starting comprehensive performance test suite")
        
        # Reset performance monitor stats
        performance_monitor.reset_stats()
        
        # Test 1: Single request baseline
        logger.info("=== Test 1: Single Request Baseline ===")
        self.test_single_request_performance()
        
        # Test 2: Large options chain performance
        logger.info("=== Test 2: Large Options Chain Performance ===")
        self.test_large_options_chain_performance()
        
        # Test 3: Concurrent requests
        logger.info("=== Test 3: Concurrent Request Performance ===")
        self.test_concurrent_requests()
        
        # Test 4: Caching effectiveness
        logger.info("=== Test 4: Caching Effectiveness ===")
        self.test_caching_effectiveness()
        
        # Test 5: Database connection pooling
        logger.info("=== Test 5: Database Connection Pool Performance ===")
        self.test_database_connection_pooling()
        
        # Test 6: Memory usage optimization
        logger.info("=== Test 6: Memory Usage Optimization ===")
        self.test_memory_usage()
        
        # Generate final report
        self.generate_performance_report()
        
        logger.info("Performance test suite completed")
    
    def test_single_request_performance(self):
        """Test baseline performance for single requests."""
        try:
            results = []
            
            for ticker in self.test_tickers:
                logger.info(f"Testing single request performance for {ticker}")
                
                start_time = time.time()
                result = generate_greeks_landscape_html(ticker, 'All')
                end_time = time.time()
                
                duration = end_time - start_time
                success = not isinstance(result, dict) or 'error' not in result
                
                results.append({
                    'ticker': ticker,
                    'duration': duration,
                    'success': success,
                    'result_size': len(str(result)) if result else 0
                })
                
                logger.info(f"{ticker}: {duration:.3f}s, success: {success}")
            
            # Calculate statistics
            durations = [r['duration'] for r in results if r['success']]
            success_rate = sum(1 for r in results if r['success']) / len(results)
            
            self.results['single_request'] = {
                'total_requests': len(results),
                'successful_requests': len(durations),
                'success_rate': success_rate,
                'avg_duration': statistics.mean(durations) if durations else 0,
                'min_duration': min(durations) if durations else 0,
                'max_duration': max(durations) if durations else 0,
                'median_duration': statistics.median(durations) if durations else 0,
                'details': results
            }
            
            logger.info(f"Single request test completed: {success_rate:.1%} success rate, avg: {statistics.mean(durations):.3f}s")
            
        except Exception as e:
            logger.error(f"Error in single request performance test: {str(e)}")
            self.results['single_request'] = {'error': str(e)}
    
    def test_large_options_chain_performance(self):
        """Test performance with large options chains (simulated by multiple date ranges)."""
        try:
            logger.info("Testing large options chain performance")
            
            # Test with different date ranges to get varying amounts of data
            test_cases = [
                {'ticker': 'AAPL', 'start_date': '2024-01-01', 'end_date': '2024-12-31', 'description': 'Full year'},
                {'ticker': 'GOOGL', 'start_date': '2024-06-01', 'end_date': '2024-12-31', 'description': '6 months'},
                {'ticker': 'MSFT', 'start_date': '2024-09-01', 'end_date': '2024-12-31', 'description': '3 months'},
            ]
            
            results = []
            
            for case in test_cases:
                logger.info(f"Testing {case['ticker']} with {case['description']} data range")
                
                start_time = time.time()
                result = generate_greeks_landscape_html(
                    case['ticker'], 
                    'All',
                    case['start_date'],
                    case['end_date']
                )
                end_time = time.time()
                
                duration = end_time - start_time
                success = not isinstance(result, dict) or 'error' not in result
                
                results.append({
                    'ticker': case['ticker'],
                    'description': case['description'],
                    'duration': duration,
                    'success': success,
                    'result_size': len(str(result)) if result else 0
                })
                
                logger.info(f"{case['ticker']} ({case['description']}): {duration:.3f}s, success: {success}")
            
            # Calculate statistics
            durations = [r['duration'] for r in results if r['success']]
            success_rate = sum(1 for r in results if r['success']) / len(results)
            
            self.results['large_options_chain'] = {
                'total_tests': len(results),
                'successful_tests': len(durations),
                'success_rate': success_rate,
                'avg_duration': statistics.mean(durations) if durations else 0,
                'max_duration': max(durations) if durations else 0,
                'details': results
            }
            
            logger.info(f"Large options chain test completed: {success_rate:.1%} success rate")
            
        except Exception as e:
            logger.error(f"Error in large options chain performance test: {str(e)}")
            self.results['large_options_chain'] = {'error': str(e)}
    
    def test_concurrent_requests(self):
        """Test performance with multiple concurrent requests."""
        try:
            logger.info("Testing concurrent request performance")
            
            # Test different concurrency levels
            concurrency_levels = [2, 5, 10]
            
            for concurrency in concurrency_levels:
                logger.info(f"Testing with {concurrency} concurrent requests")
                
                # Create test requests
                requests = []
                for i in range(concurrency):
                    ticker = self.test_tickers[i % len(self.test_tickers)]
                    requests.append({'ticker': ticker, 'view': 'All'})
                
                # Execute concurrent requests
                start_time = time.time()
                results = self._execute_concurrent_requests(requests)
                end_time = time.time()
                
                total_duration = end_time - start_time
                successful_requests = sum(1 for r in results if r['success'])
                success_rate = successful_requests / len(results)
                
                # Calculate individual request statistics
                individual_durations = [r['duration'] for r in results if r['success']]
                
                test_result = {
                    'concurrency_level': concurrency,
                    'total_requests': len(requests),
                    'successful_requests': successful_requests,
                    'success_rate': success_rate,
                    'total_duration': total_duration,
                    'avg_individual_duration': statistics.mean(individual_durations) if individual_durations else 0,
                    'max_individual_duration': max(individual_durations) if individual_durations else 0,
                    'throughput_requests_per_second': successful_requests / total_duration if total_duration > 0 else 0,
                    'details': results
                }
                
                if 'concurrent_requests' not in self.results:
                    self.results['concurrent_requests'] = []
                self.results['concurrent_requests'].append(test_result)
                
                logger.info(
                    f"Concurrency {concurrency}: {success_rate:.1%} success, "
                    f"{test_result['throughput_requests_per_second']:.2f} req/s"
                )
            
        except Exception as e:
            logger.error(f"Error in concurrent request performance test: {str(e)}")
            self.results['concurrent_requests'] = {'error': str(e)}
    
    def _execute_concurrent_requests(self, requests: List[Dict]) -> List[Dict]:
        """Execute multiple requests concurrently using ThreadPoolExecutor."""
        results = []
        
        def execute_single_request(request):
            start_time = time.time()
            try:
                result = generate_greeks_landscape_html(request['ticker'], request['view'])
                success = not isinstance(result, dict) or 'error' not in result
            except Exception as e:
                result = None
                success = False
            end_time = time.time()
            
            return {
                'ticker': request['ticker'],
                'duration': end_time - start_time,
                'success': success,
                'result_size': len(str(result)) if result else 0
            }
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(requests)) as executor:
            future_to_request = {executor.submit(execute_single_request, req): req for req in requests}
            
            for future in concurrent.futures.as_completed(future_to_request):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Request failed: {str(e)}")
                    results.append({
                        'ticker': 'unknown',
                        'duration': 0,
                        'success': False,
                        'result_size': 0
                    })
        
        return results
    
    def test_caching_effectiveness(self):
        """Test the effectiveness of caching mechanisms."""
        try:
            logger.info("Testing caching effectiveness")
            
            # Clear cache first
            data_fetcher = GreeksDataFetcher()
            calculator = GreeksCalculator()
            data_fetcher.invalidate_options_cache()
            calculator.invalidate_cache()
            
            ticker = 'AAPL'
            
            # First request (cache miss)
            logger.info("Making first request (cache miss expected)")
            start_time = time.time()
            result1 = generate_greeks_landscape_html(ticker, 'All')
            first_duration = time.time() - start_time
            
            # Second request (cache hit expected)
            logger.info("Making second request (cache hit expected)")
            start_time = time.time()
            result2 = generate_greeks_landscape_html(ticker, 'All')
            second_duration = time.time() - start_time
            
            # Third request with different view (partial cache hit)
            logger.info("Making third request with different view")
            start_time = time.time()
            result3 = generate_greeks_landscape_html(ticker, 'Delta')
            third_duration = time.time() - start_time
            
            # Calculate cache effectiveness
            cache_improvement = (first_duration - second_duration) / first_duration if first_duration > 0 else 0
            
            # Get cache statistics
            cache_stats = data_fetcher.get_cache_stats()
            greeks_cache_stats = calculator.get_cache_stats()
            
            self.results['caching_effectiveness'] = {
                'first_request_duration': first_duration,
                'second_request_duration': second_duration,
                'third_request_duration': third_duration,
                'cache_improvement_percentage': cache_improvement * 100,
                'cache_stats': cache_stats,
                'greeks_cache_stats': greeks_cache_stats,
                'all_requests_successful': all([
                    not isinstance(r, dict) or 'error' not in r 
                    for r in [result1, result2, result3]
                ])
            }
            
            logger.info(f"Cache effectiveness: {cache_improvement:.1%} improvement on second request")
            
        except Exception as e:
            logger.error(f"Error in caching effectiveness test: {str(e)}")
            self.results['caching_effectiveness'] = {'error': str(e)}
    
    def test_database_connection_pooling(self):
        """Test database connection pool performance and monitoring."""
        try:
            logger.info("Testing database connection pool performance")
            
            # Update pool stats
            performance_monitor.update_db_pool_stats(engine)
            initial_pool_stats = performance_monitor.get_db_pool_performance()
            
            # Create multiple data fetchers to test connection pooling
            fetchers = [GreeksDataFetcher() for _ in range(5)]
            
            # Execute multiple database operations concurrently
            def fetch_data(fetcher, ticker):
                try:
                    return fetcher.fetch_options_chain(ticker)
                except Exception as e:
                    logger.warning(f"Database fetch failed for {ticker}: {str(e)}")
                    return None
            
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for i, fetcher in enumerate(fetchers):
                    ticker = self.test_tickers[i % len(self.test_tickers)]
                    futures.append(executor.submit(fetch_data, fetcher, ticker))
                
                results = []
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    results.append(result is not None)
            
            total_duration = time.time() - start_time
            
            # Update pool stats after operations
            performance_monitor.update_db_pool_stats(engine)
            final_pool_stats = performance_monitor.get_db_pool_performance()
            
            success_rate = sum(results) / len(results)
            
            self.results['database_connection_pooling'] = {
                'concurrent_operations': len(fetchers),
                'total_duration': total_duration,
                'success_rate': success_rate,
                'initial_pool_stats': initial_pool_stats,
                'final_pool_stats': final_pool_stats,
                'pool_utilization': final_pool_stats.get('active_connections', 0) / max(final_pool_stats.get('pool_size', 1), 1)
            }
            
            logger.info(f"Database pool test: {success_rate:.1%} success rate, {total_duration:.3f}s total")
            
        except Exception as e:
            logger.error(f"Error in database connection pooling test: {str(e)}")
            self.results['database_connection_pooling'] = {'error': str(e)}
    
    def test_memory_usage(self):
        """Test memory usage optimization."""
        try:
            logger.info("Testing memory usage optimization")
            
            # Get initial system performance
            initial_system_stats = performance_monitor.get_system_performance()
            
            # Execute multiple operations to test memory usage
            memory_results = []
            
            for ticker in self.test_tickers:
                logger.info(f"Testing memory usage for {ticker}")
                
                before_stats = performance_monitor.get_system_performance()
                
                # Execute Greeks landscape generation
                result = generate_greeks_landscape_html(ticker, 'All')
                success = not isinstance(result, dict) or 'error' not in result
                
                after_stats = performance_monitor.get_system_performance()
                
                memory_delta = after_stats.get('memory_mb', 0) - before_stats.get('memory_mb', 0)
                
                memory_results.append({
                    'ticker': ticker,
                    'success': success,
                    'memory_before_mb': before_stats.get('memory_mb', 0),
                    'memory_after_mb': after_stats.get('memory_mb', 0),
                    'memory_delta_mb': memory_delta
                })
                
                logger.info(f"{ticker}: {memory_delta:+.1f}MB memory change")
            
            # Calculate memory statistics
            successful_results = [r for r in memory_results if r['success']]
            memory_deltas = [r['memory_delta_mb'] for r in successful_results]
            
            final_system_stats = performance_monitor.get_system_performance()
            
            self.results['memory_usage'] = {
                'initial_memory_mb': initial_system_stats.get('memory_mb', 0),
                'final_memory_mb': final_system_stats.get('memory_mb', 0),
                'total_memory_change_mb': final_system_stats.get('memory_mb', 0) - initial_system_stats.get('memory_mb', 0),
                'avg_memory_delta_per_operation': statistics.mean(memory_deltas) if memory_deltas else 0,
                'max_memory_delta_per_operation': max(memory_deltas) if memory_deltas else 0,
                'min_memory_delta_per_operation': min(memory_deltas) if memory_deltas else 0,
                'memory_efficiency_score': 100 - abs(statistics.mean(memory_deltas)) if memory_deltas else 0,
                'details': memory_results
            }
            
            logger.info(f"Memory usage test completed: avg {statistics.mean(memory_deltas):+.1f}MB per operation")
            
        except Exception as e:
            logger.error(f"Error in memory usage test: {str(e)}")
            self.results['memory_usage'] = {'error': str(e)}
    
    def generate_performance_report(self):
        """Generate a comprehensive performance report."""
        logger.info("Generating comprehensive performance report")
        
        print("\n" + "="*80)
        print("GREEKS LANDSCAPE PERFORMANCE OPTIMIZATION REPORT")
        print("="*80)
        
        # Overall performance summary
        log_performance_summary('full_landscape_generation', hours=1)
        log_performance_summary('greeks_calculation', hours=1)
        log_performance_summary('options_data_fetch', hours=1)
        log_performance_summary('database_query', hours=1)
        
        # Detailed test results
        for test_name, results in self.results.items():
            print(f"\n{test_name.upper().replace('_', ' ')} RESULTS:")
            print("-" * 50)
            
            if 'error' in results:
                print(f"❌ Test failed: {results['error']}")
                continue
            
            if test_name == 'single_request':
                print(f"✅ Success Rate: {results['success_rate']:.1%}")
                print(f"📊 Average Duration: {results['avg_duration']:.3f}s")
                print(f"⚡ Fastest Request: {results['min_duration']:.3f}s")
                print(f"🐌 Slowest Request: {results['max_duration']:.3f}s")
                print(f"📈 Median Duration: {results['median_duration']:.3f}s")
                
            elif test_name == 'large_options_chain':
                print(f"✅ Success Rate: {results['success_rate']:.1%}")
                print(f"📊 Average Duration: {results['avg_duration']:.3f}s")
                print(f"🐌 Max Duration: {results['max_duration']:.3f}s")
                
            elif test_name == 'concurrent_requests':
                if isinstance(results, list):
                    for result in results:
                        print(f"🔄 Concurrency {result['concurrency_level']}: {result['success_rate']:.1%} success, {result['throughput_requests_per_second']:.2f} req/s")
                
            elif test_name == 'caching_effectiveness':
                print(f"✅ All Requests Successful: {results['all_requests_successful']}")
                print(f"🚀 Cache Improvement: {results['cache_improvement_percentage']:.1f}%")
                print(f"⏱️  First Request: {results['first_request_duration']:.3f}s")
                print(f"⚡ Second Request: {results['second_request_duration']:.3f}s")
                print(f"🎯 Cache Hit Ratio: {results['greeks_cache_stats'].get('cache_hit_ratio', 0):.1%}")
                
            elif test_name == 'database_connection_pooling':
                print(f"✅ Success Rate: {results['success_rate']:.1%}")
                print(f"⏱️  Total Duration: {results['total_duration']:.3f}s")
                print(f"🏊 Pool Utilization: {results['pool_utilization']:.1%}")
                print(f"🔗 Active Connections: {results['final_pool_stats'].get('active_connections', 0)}")
                
            elif test_name == 'memory_usage':
                print(f"💾 Total Memory Change: {results['total_memory_change_mb']:+.1f}MB")
                print(f"📊 Avg Memory per Operation: {results['avg_memory_delta_per_operation']:+.1f}MB")
                print(f"📈 Max Memory per Operation: {results['max_memory_delta_per_operation']:+.1f}MB")
                print(f"🎯 Memory Efficiency Score: {results['memory_efficiency_score']:.1f}/100")
        
        # Performance recommendations
        print(f"\n{'PERFORMANCE RECOMMENDATIONS'}")
        print("-" * 50)
        
        # Analyze results and provide recommendations
        if 'caching_effectiveness' in self.results:
            cache_improvement = self.results['caching_effectiveness'].get('cache_improvement_percentage', 0)
            if cache_improvement > 20:
                print("✅ Caching is working effectively (>20% improvement)")
            else:
                print("⚠️  Consider tuning cache settings for better performance")
        
        if 'concurrent_requests' in self.results and isinstance(self.results['concurrent_requests'], list):
            max_throughput = max([r.get('throughput_requests_per_second', 0) for r in self.results['concurrent_requests']])
            if max_throughput > 2:
                print("✅ Good concurrent request handling (>2 req/s)")
            else:
                print("⚠️  Consider optimizing for better concurrent performance")
        
        if 'memory_usage' in self.results:
            avg_memory = abs(self.results['memory_usage'].get('avg_memory_delta_per_operation', 0))
            if avg_memory < 50:
                print("✅ Good memory efficiency (<50MB per operation)")
            else:
                print("⚠️  Consider memory optimization (high memory usage per operation)")
        
        print("\n" + "="*80)
        print("Performance testing completed successfully!")
        print("="*80)


def main():
    """Main function to run performance tests."""
    try:
        test_suite = PerformanceTestSuite()
        test_suite.run_all_tests()
        
    except KeyboardInterrupt:
        logger.info("Performance testing interrupted by user")
    except Exception as e:
        logger.error(f"Performance testing failed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()