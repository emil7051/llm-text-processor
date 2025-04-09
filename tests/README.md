# TextCleaner Test Suite

This directory contains all the test code for TextCleaner.

## Directory Structure

```
tests/
├── fixtures/             # Test fixtures and sample data
│   ├── docs/             # Documents for testing 
│   ├── html/             # HTML files for testing
│   └── ...               # Other test data
├── integration/          # Integration tests
│   ├── test_cli.py       # Tests for the command-line interface
│   ├── test_converters.py # Tests for file conversion
│   └── ...               # Other integration tests
├── unit/                 # Unit tests for individual components
│   ├── core/             # Tests for core functionality
│   ├── converters/       # Tests for file conversion modules
│   ├── processors/       # Tests for text processing modules
│   └── ...               # Other unit tests
├── conftest.py           # Common pytest fixtures and configuration
└── README.md             # This file
```

## Running Tests

### Using run_tests.py

The `run_tests.py` script in the project root provides convenient ways to run tests:

```bash
# Run all tests
python run_tests.py

# Run unit tests only
python run_tests.py --unit

# Run integration tests only
python run_tests.py --integration

# Run with coverage
python run_tests.py --coverage
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run unit tests
pytest tests/unit

# Run integration tests
pytest tests/integration

# Run with coverage
pytest --cov=textcleaner --cov-report=term --cov-report=html
```

## Writing Tests

### Test Categories

- **Unit Tests**: Test individual components in isolation. Should be fast and not require external resources.
- **Integration Tests**: Test multiple components working together. May require external resources or file system access.

### Test Naming

- Test files should be named `test_*.py`
- Test functions should be named `test_*`
- Test classes should be named `Test*`

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_function():
    # Test code here

@pytest.mark.integration
def test_integration():
    # Test code here
```

Available markers:
- `unit`: Unit tests
- `integration`: Integration tests
- `slow`: Tests that take longer than 1 second
- `security`: Tests for security features
- `memory`: Tests for memory efficiency
- `parallel`: Tests for parallel processing
- `config`: Tests related to configuration
- `converters`: Tests for file converters
- `processors`: Tests for text processors
- `performance`: Tests for performance validation