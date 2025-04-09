# Unit Tests

This directory contains unit tests for the TextCleaner package. The tests are organized by module:

## Directory Structure

```
unit/
├── core/                 # Tests for core functionality
│   ├── test_processor.py        # Tests for the main TextProcessor class
│   ├── test_memory_efficiency.py # Tests for memory efficiency
│   ├── test_parallel.py         # Tests for parallel processing
│   └── test_presets.py          # Tests for processing presets
├── converters/           # Tests for file format converters
│   └── test_html_converter.py   # Tests for HTML/XML conversion
├── config/               # Tests for configuration handling
│   └── test_config_manager.py   # Tests for configuration management
└── utils/                # Tests for utility functions
    ├── test_security.py         # Tests for security utilities
    ├── test_enhanced_security.py # Tests for enhanced security features
    ├── test_file_utils.py       # Tests for file utilities
    ├── test_file_registry.py    # Tests for file registry
    └── test_property_based.py   # Property-based tests
```

## Running Tests

You can run all unit tests with:

```bash
python run_tests.py --unit
```

Or run tests for a specific module:

```bash
python -m pytest tests/unit/core/test_processor.py
```

## Adding New Tests

When adding new tests:

1. Place the test in the appropriate subdirectory
2. Follow the naming convention: `test_*.py`
3. Use the `@pytest.mark.unit` decorator for all unit tests
4. Keep tests focused on testing a single component
5. Use fixtures from `tests/fixtures/` for common test data 