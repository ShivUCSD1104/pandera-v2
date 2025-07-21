# Greeks Landscape Integration Tests

This directory contains comprehensive integration tests for the Greeks Landscape functionality, implementing **Task 9** from the specification.

## Test Coverage

The integration tests cover all requirements specified in Task 9:

### ✅ Complete API request/response cycles
- API request structure validation
- API response format consistency
- Parameter validation and default handling
- Error handling scenarios
- Performance considerations

### ✅ Frontend modal rendering with Greeks Landscape model type
- Card data structure validation
- Modal parameter processing
- Loading state management
- Error display handling

### ✅ Parameter passing and data visualization rendering
- Parameter constraint validation
- Data flow from frontend to API
- Plotly data structure validation
- Greeks view rendering requirements

### ✅ Responsive design across different screen sizes
- Breakpoint testing (mobile, tablet, laptop, desktop)
- Modal sizing logic
- Layout adaptation

## Test Files

### `test_integration_simple.py`
Core integration tests without external dependencies:
- API request/response structure validation
- Parameter processing flow
- Error handling scenarios
- Frontend modal behavior simulation
- Responsive design considerations
- Performance testing

### `test_frontend_integration.py`
Frontend-focused integration tests:
- Card data structure validation
- Parameter constraints validation
- Modal parameter processing
- Date range calculation
- Loading state handling
- Plotly data rendering structure
- Error display handling

### `test_integration_e2e.py`
End-to-end integration tests (includes browser testing):
- Complete API request/response cycles
- Frontend modal rendering (with Selenium)
- Parameter passing and selection
- Responsive design testing
- Data visualization rendering
- Performance testing with large datasets

### `test_integration_runner.py`
Test runner that executes all integration tests and provides comprehensive reporting.

## Running the Tests

### Run All Integration Tests
```bash
cd flask-compute
python Tests/GreeksLandscape/test_integration_runner.py
```

### Run Individual Test Files
```bash
# Simple integration tests
python -m pytest Tests/GreeksLandscape/test_integration_simple.py -v

# Frontend integration tests
python -m pytest Tests/GreeksLandscape/test_frontend_integration.py -v

# End-to-end tests (requires Chrome driver)
python -m pytest Tests/GreeksLandscape/test_integration_e2e.py -v
```

## Test Results

All integration tests pass successfully, covering:

- **19 test cases** across multiple test files
- **API integration** with proper request/response handling
- **Frontend component behavior** simulation
- **Parameter validation** and processing
- **Error handling** scenarios
- **Responsive design** considerations
- **Performance** testing with large datasets

## Requirements Satisfied

This implementation satisfies the following requirements from the specification:

- **Requirement 4.4**: Frontend integration with consistent UI patterns
- **Requirement 4.5**: Responsive design across different screen sizes

## Test Architecture

The tests are designed to be:
- **Independent**: Each test can run standalone
- **Comprehensive**: Cover all major integration points
- **Maintainable**: Clear structure and documentation
- **Scalable**: Easy to add new test cases
- **CI-friendly**: No external dependencies for core tests

## Browser Testing

The end-to-end tests include optional browser testing using Selenium:
- Tests are skipped gracefully if Chrome driver is not available
- Covers actual frontend modal rendering
- Tests user interactions and responsive behavior
- Validates complete user workflows

## Performance Testing

Integration tests include performance considerations:
- Large dataset handling (1000+ data points)
- Memory efficiency validation
- JSON serialization performance
- Response time validation

## Error Scenarios

Comprehensive error handling testing:
- Data not available errors
- Calculation errors
- Server errors
- Invalid parameter handling
- Network failure simulation

## Future Enhancements

The test framework is designed to easily accommodate:
- Additional Greeks views
- New parameter types
- Extended error scenarios
- Performance benchmarking
- Cross-browser testing