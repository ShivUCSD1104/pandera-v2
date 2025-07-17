"""
Integration Test Runner for Greeks Landscape functionality.

This script runs all integration tests for the Greeks Landscape feature,
covering end-to-end functionality as specified in task 9.

Test Coverage:
1. Complete API request/response cycles
2. Frontend modal rendering with Greeks Landscape model type  
3. Parameter passing and data visualization rendering
4. Responsive design across different screen sizes

Requirements: 4.4, 4.5
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

# Import all test classes
from test_integration_simple import TestGreeksLandscapeSimpleIntegration
from test_frontend_integration import TestGreeksLandscapeFrontendIntegration

def create_test_suite():
    """Create a comprehensive test suite for Greeks Landscape integration."""
    suite = unittest.TestSuite()
    
    # Add simple integration tests
    suite.addTest(unittest.makeSuite(TestGreeksLandscapeSimpleIntegration))
    
    # Add frontend integration tests
    suite.addTest(unittest.makeSuite(TestGreeksLandscapeFrontendIntegration))
    
    return suite

def run_integration_tests():
    """Run all integration tests and return results."""
    print("=" * 80)
    print("GREEKS LANDSCAPE INTEGRATION TESTS")
    print("=" * 80)
    print()
    
    # Create test suite
    suite = create_test_suite()
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Determine overall success
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n✅ ALL INTEGRATION TESTS PASSED!")
        print("\nTask 9 Implementation Summary:")
        print("✅ Complete API request/response cycles - TESTED")
        print("✅ Frontend modal rendering with Greeks Landscape model type - TESTED")
        print("✅ Parameter passing and data visualization rendering - TESTED")
        print("✅ Responsive design across different screen sizes - TESTED")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    print("=" * 80)
    
    return success

if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)