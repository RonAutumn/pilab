# CinePi Dashboard Test Suite

This directory contains comprehensive unit tests for the CinePi Dashboard application. The test suite is designed to achieve 90%+ code coverage and ensure the reliability and correctness of all dashboard components.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest configuration and fixtures
├── test_utils.py            # Unit tests for utility functions
├── test_config.py           # Unit tests for configuration management
├── test_services.py         # Unit tests for service layer
├── test_routes.py           # Unit tests for Flask routes
└── README.md               # This documentation file
```

## Test Categories

### 1. Unit Tests (`test_utils.py`)
Tests for utility functions in `dashboard/utils/validators.py`:
- **Interval validation**: Tests for capture interval validation (5-3600 seconds)
- **Camera settings validation**: Tests for camera parameter validation
- **Configuration structure validation**: Tests for YAML configuration validation
- **Filename validation**: Tests for security validation of filenames

### 2. Configuration Tests (`test_config.py`)
Tests for configuration management in `dashboard/config.py`:
- **Base configuration**: Tests for common configuration attributes
- **Environment-specific configs**: Tests for development, production, and testing configs
- **Path management**: Tests for application and CinePi integration paths
- **Environment variables**: Tests for environment variable handling

### 3. Service Layer Tests (`test_services.py`)
Tests for service layer functions:
- **Camera Service**: Tests for camera control and integration
- **Capture Service**: Tests for timelapse capture control
- **Config Service**: Tests for configuration management
- **WebSocket Service**: Tests for real-time communication

### 4. Route Tests (`test_routes.py`)
Tests for Flask API routes in `dashboard/routes/api.py`:
- **Capture routes**: Tests for timelapse control endpoints
- **Camera routes**: Tests for camera settings endpoints
- **Status routes**: Tests for system status endpoints
- **Config routes**: Tests for configuration management endpoints
- **Error handling**: Tests for exception handling and validation

## Running Tests

### Prerequisites
Install test dependencies:
```bash
pip install -r requirements-test.txt
```

### Basic Test Execution
```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_utils.py

# Run specific test class
python -m pytest tests/test_utils.py::TestValidateInterval

# Run specific test method
python -m pytest tests/test_utils.py::TestValidateInterval::test_valid_intervals
```

### Using the Test Runner Script
```bash
# Run all tests with coverage
python run_tests.py --coverage

# Run unit tests only
python run_tests.py --unit

# Run with verbose output
python run_tests.py --verbose

# Install dependencies and run tests
python run_tests.py --install-deps --coverage

# Clean up test artifacts
python run_tests.py --clean
```

### Test Markers
Use pytest markers to run specific test categories:
```bash
# Run unit tests only
python -m pytest -m unit

# Run integration tests only
python -m pytest -m integration

# Skip slow tests
python -m pytest -m "not slow"

# Run API tests
python -m pytest -m api
```

## Coverage Reports

The test suite is configured to generate comprehensive coverage reports:

### HTML Coverage Report
```bash
python -m pytest --cov=dashboard --cov-report=html:htmlcov
```
Open `htmlcov/index.html` in your browser to view the detailed coverage report.

### XML Coverage Report
```bash
python -m pytest --cov=dashboard --cov-report=xml:coverage.xml
```
The XML report can be used by CI/CD systems and coverage analysis tools.

### Terminal Coverage Report
```bash
python -m pytest --cov=dashboard --cov-report=term-missing
```
Shows missing lines in the terminal output.

## Test Fixtures

The test suite uses pytest fixtures defined in `conftest.py`:

### Application Fixtures
- `app`: Flask application instance for testing
- `client`: Test client for making HTTP requests
- `runner`: CLI test runner

### Service Fixtures
- `mock_camera_service`: Mock camera service with predefined responses
- `mock_capture_service`: Mock capture service with predefined responses
- `mock_config_service`: Mock configuration service with predefined responses
- `mock_websocket_service`: Mock WebSocket service with predefined responses

### Data Fixtures
- `sample_camera_settings`: Sample camera settings for testing
- `sample_config_data`: Sample configuration data for testing
- `temp_file`: Temporary file for testing file operations

## Test Data

The test suite includes comprehensive test data covering:
- Valid and invalid input scenarios
- Edge cases and boundary conditions
- Error conditions and exception handling
- Security validation (path traversal, file extensions)
- Configuration validation (YAML syntax, required fields)

## Mocking Strategy

The test suite uses extensive mocking to isolate units under test:

### External Dependencies
- **Subprocess calls**: Mocked to avoid actual system commands
- **File system operations**: Mocked to avoid file system dependencies
- **WebSocket connections**: Mocked to avoid network dependencies
- **External services**: Mocked to ensure test isolation

### Service Dependencies
- **Service layer**: Mocked in route tests to focus on route logic
- **Configuration**: Mocked to use test-specific paths and settings
- **Database operations**: Mocked to avoid database dependencies

## Continuous Integration

The test suite is designed for CI/CD integration:

### Coverage Requirements
- Minimum coverage: 90%
- Coverage reports: HTML, XML, and terminal formats
- Coverage thresholds enforced by pytest-cov

### Test Categories
- **Unit tests**: Fast, isolated tests for individual components
- **Integration tests**: Tests for component interactions
- **API tests**: Tests for HTTP endpoints
- **Slow tests**: Marked for optional execution in CI

### CI Configuration
```yaml
# Example GitHub Actions configuration
- name: Run tests
  run: |
    pip install -r requirements-test.txt
    python -m pytest --cov=dashboard --cov-report=xml --cov-fail-under=90
```

## Best Practices

### Test Organization
- **One test file per module**: Each module has its own test file
- **Descriptive test names**: Test methods clearly describe what they test
- **Comprehensive coverage**: Tests cover success, failure, and edge cases
- **Isolated tests**: Each test is independent and can run in any order

### Test Data Management
- **Fixtures for common data**: Reusable test data through pytest fixtures
- **Temporary files**: Proper cleanup of test artifacts
- **Mock data**: Realistic but controlled test data

### Error Testing
- **Exception handling**: Tests verify proper exception handling
- **Validation errors**: Tests for input validation
- **Service failures**: Tests for service layer error conditions
- **Network errors**: Tests for external dependency failures

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure you're in the project root directory
cd /path/to/cinepi-dashboard

# Install dependencies
pip install -r requirements-test.txt
```

#### Coverage Issues
```bash
# Check if coverage is installed
pip install pytest-cov

# Run with coverage
python -m pytest --cov=dashboard --cov-report=term-missing
```

#### Mock Issues
```bash
# Check if pytest-mock is installed
pip install pytest-mock

# Run with mock debugging
python -m pytest -v --tb=long
```

### Debugging Tests
```bash
# Run single test with full traceback
python -m pytest tests/test_utils.py::TestValidateInterval::test_valid_intervals -v --tb=long

# Run with print statements
python -m pytest -s tests/test_utils.py::TestValidateInterval::test_valid_intervals

# Run with debugger
python -m pytest --pdb tests/test_utils.py::TestValidateInterval::test_valid_intervals
```

## Contributing

When adding new features to the dashboard:

1. **Write tests first**: Follow TDD principles
2. **Maintain coverage**: Ensure new code is covered by tests
3. **Update fixtures**: Add new fixtures as needed
4. **Document tests**: Add docstrings to test methods
5. **Run full suite**: Ensure all tests pass before committing

### Adding New Tests
```python
# Example: Adding a new test method
def test_new_feature(self, client, mock_service):
    """Test new feature functionality"""
    # Arrange
    mock_service.new_method.return_value = {'success': True}
    
    # Act
    response = client.post('/api/new-endpoint', json={'data': 'test'})
    
    # Assert
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
```

## Performance

The test suite is optimized for performance:
- **Fast execution**: Most tests complete in milliseconds
- **Parallel execution**: Tests can run in parallel (use `pytest-xdist`)
- **Selective execution**: Use markers to run specific test categories
- **Minimal dependencies**: Tests use minimal external dependencies

### Performance Tips
```bash
# Run tests in parallel (requires pytest-xdist)
python -m pytest -n auto

# Run only fast tests
python -m pytest -m "not slow"

# Profile test execution
python -m pytest --durations=10
``` 