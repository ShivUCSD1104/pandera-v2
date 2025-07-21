# Test Suite Organization

This directory contains all tests for the Flask Compute application, organized by feature and test type.

## Directory Structure

```
Tests/
├── README.md                           # This file
├── conftest.py                         # Shared pytest configuration
├── requirements.txt                    # Test-specific dependencies
├── run_all_tests.py                   # Master test runner
│
├── Unit/                              # Unit tests
│   ├── __init__.py
│   ├── test_database_models.py
│   ├── test_utils.py
│   └── GreeksLandscape/
│       ├── __init__.py
│       ├── test_greeks_calculator.py
│       ├── test_data_fetcher.py
│       ├── test_validators.py
│       └── test_performance_monitor.py
│
├── Integration/                       # Integration tests
│   ├── __init__.py
│   ├── test_api_endpoints.py
│   ├── test_database_integration.py
│   └── GreeksLandscape/
│       ├── __init__.py
│       ├── test_greeks_integration.py
│       ├── test_data_integration.py
│       └── test_end_to_end.py
│
├── Performance/                       # Performance tests
│   ├── __init__.py
│   ├── test_performance_suite.py
│   ├── test_caching_performance.py
│   ├── test_concurrent_requests.py
│   ├── test_memory_usage.py
│   └── GreeksLandscape/
│       ├── __init__.py
│       ├── test_greeks_performance.py
│       └── test_database_performance.py
│
├── ErrorHandling/                     # Error handling tests
│   ├── __init__.py
│   ├── test_error_scenarios.py
│   ├── test_validation_errors.py
│   └── GreeksLandscape/
│       ├── __init__.py
│       ├── test_greeks_errors.py
│       └── test_data_errors.py
│
├── Migration/                         # Database migration tests
│   ├── __init__.py
│   ├── test_database_migration.py
│   └── migrate_database_indexes.py
│
├── Validation/                        # Implementation validation tests
│   ├── __init__.py
│   ├── test_code_validation.py
│   └── test_implementation_check.py
│
└── GreeksLandscape/                   # Existing Greeks Landscape tests
    ├── README_Integration_Tests.md
    ├── test_integration_runner.py
    ├── test_integration_simple.py
    ├── test_frontend_integration.py
    ├── test_api_integration.py
    ├── test_integration_e2e.py
    ├── test_error_handling.py
    ├── test_greeks_caching.py
    └── test_live_data_integration.py
```

## Test Categories

### Unit Tests (`Unit/`)
- Test individual functions and classes in isolation
- Mock external dependencies
- Fast execution, no database required
- Run frequently during development

### Integration Tests (`Integration/`)
- Test component interactions
- Use test database or mocked services
- Verify data flow between modules
- Run before deployment

### Performance Tests (`Performance/`)
- Measure execution time and resource usage
- Test with large datasets
- Concurrent request testing
- Memory usage optimization validation
- Run periodically or before releases

### Error Handling Tests (`ErrorHandling/`)
- Test error scenarios and edge cases
- Validate error messages and user experience
- Test recovery mechanisms
- Ensure graceful degradation

### Migration Tests (`Migration/`)
- Test database schema changes
- Validate index creation and optimization
- Test migration rollback scenarios

### Validation Tests (`Validation/`)
- Validate implementation completeness
- Check code structure and patterns
- Verify optimization implementation
- Static analysis and code quality checks

## Running Tests

### Run All Tests
```bash
python Tests/run_all_tests.py
```

### Run Specific Test Categories
```bash
# Unit tests only
python -m pytest Tests/Unit/ -v

# Performance tests only
python -m pytest Tests/Performance/ -v

# Greeks Landscape tests only
python -m pytest Tests/GreeksLandscape/ -v
```

### Run Individual Test Files
```bash
python -m pytest Tests/Unit/GreeksLandscape/test_greeks_calculator.py -v
```

## Test Configuration

- `conftest.py`: Shared fixtures and configuration
- `requirements.txt`: Test-specific dependencies
- Environment variables for test database connections
- Mock configurations for external services

## Best Practices

1. **Naming Convention**: `test_*.py` for all test files
2. **Isolation**: Each test should be independent
3. **Cleanup**: Proper teardown of test data
4. **Documentation**: Clear test descriptions and comments
5. **Performance**: Keep unit tests fast (<1s each)
6. **Coverage**: Aim for >80% code coverage
7. **Mocking**: Mock external dependencies in unit tests
8. **Data**: Use fixtures for test data setup