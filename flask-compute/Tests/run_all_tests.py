#!/usr/bin/env python3
"""
Master test runner for the Flask Compute application.

This script provides a comprehensive test execution framework with:
- Organized test categories (Unit, Integration, Performance, etc.)
- Flexible test selection and filtering
- Performance monitoring and reporting
- Test result analysis and recommendations
"""

import os
import sys
import argparse
import subprocess
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestRunner:
    """
    Comprehensive test runner for Flask Compute application.
    """
    
    def __init__(self):
        self.tests_dir = current_dir
        self.results = {}
        self.total_start_time = None
        
        # Test categories and their descriptions
        self.test_categories = {
            'unit': {
                'path': 'Unit',
                'description': 'Fast unit tests with mocked dependencies',
                'markers': ['unit'],
                'timeout': 300  # 5 minutes
            },
            'integration': {
                'path': 'Integration',
                'description': 'Integration tests with real component interactions',
                'markers': ['integration'],
                'timeout': 600  # 10 minutes
            },
            'performance': {
                'path': 'Performance',
                'description': 'Performance and load testing',
                'markers': ['performance', 'slow'],
                'timeout': 1800  # 30 minutes
            },
            'error_handling': {
                'path': 'ErrorHandling',
                'description': 'Error scenarios and edge case testing',
                'markers': ['unit'],
                'timeout': 300  # 5 minutes
            },
            'migration': {
                'path': 'Migration',
                'description': 'Database migration and schema tests',
                'markers': ['database'],
                'timeout': 600  # 10 minutes
            },
            'validation': {
                'path': 'Validation',
                'description': 'Implementation validation and code quality checks',
                'markers': ['unit'],
                'timeout': 180  # 3 minutes
            },
            'greeks_landscape': {
                'path': 'GreeksLandscape',
                'description': 'Greeks Landscape specific tests',
                'markers': ['integration'],
                'timeout': 900  # 15 minutes
            }
        }
    
    def run_category(self, category: str, verbose: bool = False, coverage: bool = False) -> Dict[str, Any]:
        """
        Run tests for a specific category.
        
        Args:
            category: Test category name
            verbose: Enable verbose output
            coverage: Enable coverage reporting
            
        Returns:
            Dictionary with test results
        """
        if category not in self.test_categories:
            raise ValueError(f"Unknown test category: {category}")
        
        config = self.test_categories[category]
        test_path = self.tests_dir / config['path']
        
        if not test_path.exists():
            logger.warning(f"Test directory does not exist: {test_path}")
            return {
                'category': category,
                'status': 'skipped',
                'reason': 'directory_not_found',
                'duration': 0
            }
        
        logger.info(f"Running {category} tests: {config['description']}")
        
        # Build pytest command
        cmd = ['python', '-m', 'pytest', str(test_path)]
        
        if verbose:
            cmd.append('-v')
        
        if coverage:
            cmd.extend(['--cov=GreeksLandscape', '--cov-report=term-missing'])
        
        # Add markers (only if they exist)
        if config['markers'] and any(marker != 'unit' for marker in config['markers']):
            for marker in config['markers']:
                cmd.extend(['-m', marker])
        
        # Add timeout
        cmd.extend(['--timeout', str(config['timeout'])])
        
        # Add output formatting
        cmd.extend(['--tb=short', '--strict-markers'])
        
        start_time = time.time()
        
        try:
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=parent_dir,
                capture_output=True,
                text=True,
                timeout=config['timeout']
            )
            
            duration = time.time() - start_time
            
            return {
                'category': category,
                'status': 'passed' if result.returncode == 0 else 'failed',
                'return_code': result.returncode,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"Tests timed out after {config['timeout']} seconds")
            
            return {
                'category': category,
                'status': 'timeout',
                'duration': duration,
                'timeout_limit': config['timeout']
            }
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error running tests: {str(e)}")
            
            return {
                'category': category,
                'status': 'error',
                'duration': duration,
                'error': str(e)
            }
    
    def run_all_categories(self, exclude: List[str] = None, verbose: bool = False, coverage: bool = False) -> Dict[str, Any]:
        """
        Run all test categories.
        
        Args:
            exclude: List of categories to exclude
            verbose: Enable verbose output
            coverage: Enable coverage reporting
            
        Returns:
            Dictionary with all test results
        """
        exclude = exclude or []
        self.total_start_time = time.time()
        
        logger.info("Starting comprehensive test suite execution")
        
        for category in self.test_categories:
            if category in exclude:
                logger.info(f"Skipping {category} tests (excluded)")
                self.results[category] = {
                    'category': category,
                    'status': 'skipped',
                    'reason': 'excluded',
                    'duration': 0
                }
                continue
            
            self.results[category] = self.run_category(category, verbose, coverage)
        
        total_duration = time.time() - self.total_start_time
        
        return {
            'results': self.results,
            'total_duration': total_duration,
            'summary': self._generate_summary()
        }
    
    def run_specific_tests(self, test_paths: List[str], verbose: bool = False) -> Dict[str, Any]:
        """
        Run specific test files or directories.
        
        Args:
            test_paths: List of test file or directory paths
            verbose: Enable verbose output
            
        Returns:
            Dictionary with test results
        """
        logger.info(f"Running specific tests: {test_paths}")
        
        cmd = ['python', '-m', 'pytest'] + test_paths
        
        if verbose:
            cmd.append('-v')
        
        cmd.extend(['--tb=short'])
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=parent_dir,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes max
            )
            
            duration = time.time() - start_time
            
            return {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'return_code': result.returncode,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(cmd)
            }
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error running specific tests: {str(e)}")
            
            return {
                'status': 'error',
                'duration': duration,
                'error': str(e)
            }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of test results."""
        total_categories = len(self.results)
        passed_categories = sum(1 for r in self.results.values() if r['status'] == 'passed')
        failed_categories = sum(1 for r in self.results.values() if r['status'] == 'failed')
        skipped_categories = sum(1 for r in self.results.values() if r['status'] == 'skipped')
        error_categories = sum(1 for r in self.results.values() if r['status'] == 'error')
        timeout_categories = sum(1 for r in self.results.values() if r['status'] == 'timeout')
        
        total_duration = sum(r['duration'] for r in self.results.values())
        
        return {
            'total_categories': total_categories,
            'passed_categories': passed_categories,
            'failed_categories': failed_categories,
            'skipped_categories': skipped_categories,
            'error_categories': error_categories,
            'timeout_categories': timeout_categories,
            'success_rate': passed_categories / total_categories if total_categories > 0 else 0,
            'total_duration': total_duration
        }
    
    def print_results(self):
        """Print comprehensive test results."""
        if not self.results:
            print("No test results to display")
            return
        
        print("\n" + "="*80)
        print("FLASK COMPUTE TEST SUITE RESULTS")
        print("="*80)
        
        # Category results
        for category, result in self.results.items():
            config = self.test_categories[category]
            status_emoji = {
                'passed': '✅',
                'failed': '❌',
                'skipped': '⏭️',
                'error': '💥',
                'timeout': '⏰'
            }.get(result['status'], '❓')
            
            print(f"\n{status_emoji} {category.upper().replace('_', ' ')}")
            print(f"   Description: {config['description']}")
            print(f"   Status: {result['status'].upper()}")
            print(f"   Duration: {result['duration']:.2f}s")
            
            if result['status'] == 'failed' and 'return_code' in result:
                print(f"   Return Code: {result['return_code']}")
            
            if result['status'] == 'timeout':
                print(f"   Timeout Limit: {result.get('timeout_limit', 'unknown')}s")
            
            if result['status'] == 'error':
                print(f"   Error: {result.get('error', 'unknown')}")
        
        # Summary
        summary = self._generate_summary()
        print(f"\n{'SUMMARY'}")
        print("-" * 50)
        print(f"Total Categories: {summary['total_categories']}")
        print(f"Passed: {summary['passed_categories']} ✅")
        print(f"Failed: {summary['failed_categories']} ❌")
        print(f"Skipped: {summary['skipped_categories']} ⏭️")
        print(f"Errors: {summary['error_categories']} 💥")
        print(f"Timeouts: {summary['timeout_categories']} ⏰")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        
        # Recommendations
        self._print_recommendations(summary)
        
        print("\n" + "="*80)
    
    def _print_recommendations(self, summary: Dict[str, Any]):
        """Print recommendations based on test results."""
        print(f"\n{'RECOMMENDATIONS'}")
        print("-" * 50)
        
        if summary['success_rate'] == 1.0:
            print("🎉 All test categories passed! Your code is ready for deployment.")
        elif summary['success_rate'] >= 0.8:
            print("✅ Most tests passed. Address failing tests before deployment.")
        elif summary['success_rate'] >= 0.5:
            print("⚠️  Several test categories failed. Review and fix issues.")
        else:
            print("🚨 Many test categories failed. Significant issues need attention.")
        
        # Specific recommendations
        if summary['failed_categories'] > 0:
            print("- Review failed test output for specific error details")
            print("- Run individual test categories with -v flag for more details")
        
        if summary['timeout_categories'] > 0:
            print("- Some tests timed out - consider optimizing slow operations")
            print("- Check for infinite loops or blocking operations")
        
        if summary['error_categories'] > 0:
            print("- Test execution errors indicate environment or setup issues")
            print("- Verify all dependencies are installed and configured")
        
        # Performance recommendations
        if summary['total_duration'] > 600:  # 10 minutes
            print("- Consider running tests in parallel with pytest-xdist")
            print("- Optimize slow tests or move them to separate performance suite")


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(
        description="Flask Compute Test Suite Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_tests.py                    # Run all test categories
  python run_all_tests.py --category unit   # Run only unit tests
  python run_all_tests.py --exclude performance  # Exclude performance tests
  python run_all_tests.py --verbose --coverage   # Verbose output with coverage
  python run_all_tests.py --specific Tests/Unit/test_example.py  # Run specific test
        """
    )
    
    parser.add_argument(
        '--category', '-c',
        choices=list(TestRunner().test_categories.keys()),
        help='Run specific test category'
    )
    
    parser.add_argument(
        '--exclude', '-e',
        nargs='+',
        choices=list(TestRunner().test_categories.keys()),
        help='Exclude specific test categories'
    )
    
    parser.add_argument(
        '--specific', '-s',
        nargs='+',
        help='Run specific test files or directories'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Enable coverage reporting'
    )
    
    parser.add_argument(
        '--list-categories',
        action='store_true',
        help='List available test categories'
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.list_categories:
        print("Available test categories:")
        for category, config in runner.test_categories.items():
            print(f"  {category}: {config['description']}")
        return 0
    
    try:
        if args.specific:
            # Run specific tests
            result = runner.run_specific_tests(args.specific, args.verbose)
            print(f"Specific tests result: {result['status']}")
            return 0 if result['status'] == 'passed' else 1
            
        elif args.category:
            # Run single category
            result = runner.run_category(args.category, args.verbose, args.coverage)
            runner.results[args.category] = result
            runner.print_results()
            return 0 if result['status'] == 'passed' else 1
            
        else:
            # Run all categories (with exclusions)
            results = runner.run_all_categories(args.exclude, args.verbose, args.coverage)
            runner.print_results()
            
            summary = results['summary']
            return 0 if summary['success_rate'] == 1.0 else 1
    
    except KeyboardInterrupt:
        logger.info("Test execution interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Test runner failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)