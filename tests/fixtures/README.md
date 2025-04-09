# Test Fixtures

This directory contains fixtures for TextCleaner tests, including:

## Structure

```
fixtures/
├── docs/      # Test document files (PDF, DOCX, etc.)
├── html/      # Test HTML files
└── paths.py   # Utilities for accessing test file paths
```

## Using Fixtures

### Path Utilities

The `paths.py` module provides consistent access to test file paths:

```python
from tests.fixtures.paths import get_html_file, get_doc_file

# Get path to a test HTML file
html_path = get_html_file("simple_article.html")

# Get path to a test document file
doc_path = get_doc_file("sample.pdf")
```

### pytest Fixtures

Common pytest fixtures are defined in the main `tests/conftest.py` file, including:

- `security_utils`: SecurityUtils instance
- `test_security_utils`: TestSecurityUtils instance
- `temp_directory`: A temporary directory for testing
- `sample_files`: Sample test files created on-the-fly
- `sample_config_file`: A sample configuration file created for testing

## HTML Fixtures
The HTML fixtures in the `html/` directory were consolidated from the previous `test_html_files` directory in the project root. These files are used to test HTML parsing and conversion functionality.

## Sample Text Files
Sample text files and various formats can be found in examples/sample_data.

## Note on External Test Data
Previously, the project had test documents in `/Users/ed/dev/text-cleaning/test_docs` and processed outputs in `/Users/ed/dev/text-cleaning/processed_files`. For production use, it's recommended to use the fixtures within this test directory structure to ensure consistency and portability of tests.
