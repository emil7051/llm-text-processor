# TextCleaner Tools

This directory contains utility tools for the TextCleaner package. These tools are designed to help with debugging, testing, and performing common tasks with the TextCleaner library.

## Available Tools

### Docs Processor

The `docs_processor.py` script is a command-line utility for processing documents in batch mode:

```bash
# Process all documents in a directory
python -m textcleaner.tools.docs_processor /path/to/documents

# Process with specific output directory
python -m textcleaner.tools.docs_processor /path/to/documents -o /path/to/output

# Use aggressive config
python -m textcleaner.tools.docs_processor /path/to/documents -c aggressive

# Process files in parallel
python -m textcleaner.tools.docs_processor /path/to/documents --parallel
```

### Debug Utility

The `debug.py` script helps with manually testing TextCleaner's functionality:

```bash
# Test with sample text content
python -m textcleaner.tools.debug -t text

# Test with sample HTML content
python -m textcleaner.tools.debug -t html

# Test with aggressive configuration
python -m textcleaner.tools.debug -c aggressive

# Process a specific file
python -m textcleaner.tools.debug -f /path/to/file.txt
```

### Import Checker

The `check_imports.py` script validates imports within the package:

```bash
# Check for import issues
python -m textcleaner.tools.check_imports

# Include import time measurements
python -m textcleaner.tools.check_imports --time

# Verbose output
python -m textcleaner.tools.check_imports --verbose
```

### Package Renamer

The `rename_script.py` script helps rename package references in a codebase:

```bash
# Rename package references
python -m textcleaner.tools.rename_script old_package_name new_package_name

# Specify directory to process
python -m textcleaner.tools.rename_script old_name new_name -d /path/to/dir

# Specify file extensions
python -m textcleaner.tools.rename_script old_name new_name -e py,md,txt

# Verbose output
python -m textcleaner.tools.rename_script old_name new_name -v
```

## Adding New Tools

When adding new tools to this directory:

1. Create a new Python script with a main function
2. Update the `__init__.py` file to include the new tool
3. Document the tool in this README 