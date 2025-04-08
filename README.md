# LLM Text Preprocessing Tool

A versatile system for converting various file formats into clean, structured text optimized for Large Language Models (LLMs).

## Overview

This tool converts files from various formats (PDF, Office documents, web content, etc.) into clean, token-efficient text while preserving essential information and structure. It helps reduce unnecessary tokens, leading to more cost-effective and context-efficient LLM interactions.

### Why Use This Tool?

- **Reduce Token Usage**: Lower your API costs by preprocessing text to remove redundant content
- **Optimize Context Windows**: Make the most of limited context windows by focusing on essential content
- **Preserve Semantic Structure**: Keep document hierarchy and structure intact for better understanding
- **Consistent Processing**: Apply standard cleaning strategies across all your documents

## Features

- **Expanded Format Support**: Now with enhanced support for HTML, XML, Markdown, and plain text files in addition to PDFs and Office documents
- **HTML/XML Processing**: Intelligent extraction from HTML/XML with structure preservation and automatic cleaning of scripts, styles, and comments
- **Markdown Handling**: Process Markdown files with frontmatter extraction and preservation of formatting
- **Intelligent Cleaning**: Removes headers, footers, boilerplate content, and redundant information
- **Structure Preservation**: Maintains document hierarchy, lists, tables, and other semantic elements
- **Comprehensive Logging**: Detailed logging throughout the application with configurable log levels
- **Configurable Processing**: Adjustable cleaning levels from minimal to aggressive
- **Multiple Output Formats**: Export as plain text, Markdown, structured JSON, or CSV
- **Batch Processing**: Process entire directories of files with consistent settings
- **Performance Metrics**: Track token reduction and processing efficiency
- **Docker Support**: Run in a consistent environment across platforms
- **Python 3.9+ Compatible**: Works with a wide range of Python environments

## Installation

### Using Homebrew (macOS)

Install with the snappier name `textcleaner`:

```bash
# Add the tap
brew tap emil7051/textcleaner https://github.com/emil7051/textcleaner

# Install
brew install textcleaner

# Use the tool with the simple command
textcleaner process myfile.pdf
```

### Using pip

```bash
pip install textcleaner
```

### Using Docker

```bash
# Pull the Docker image
docker pull your-username/textcleaner:latest

# Or build from source
docker build -t textcleaner .

# Run using Docker
docker run -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output textcleaner process input/document.pdf output/document.md
```

### From Source

```bash
# Clone the repository
git clone https://github.com/your-username/textcleaner.git
cd textcleaner

# Install dependencies
pip install -e .
```

## Quick Start

```python
from textcleaner import TextProcessor

# Create processor with default settings
processor = TextProcessor()

# Process a single file
result = processor.process_file("document.pdf", output_format="markdown")
print(f"Output saved to: {result.output_path}")
print(f"Token reduction: {result.metrics.token_reduction_percent}%")

# Process HTML content
result = processor.process_file("webpage.html", output_format="markdown")
print(f"Extracted {result.metrics.get('raw_character_count', 0)} characters")

# Process a directory containing mixed file types
results = processor.process_directory("documents/", output_format="markdown")
print(f"Processed {len(results)} files")
```

## Command Line Usage

```bash
# Process a single file
python -m textcleaner.cli process input.pdf output.md

# Process with specific configuration and logging
python -m textcleaner.cli --log-level DEBUG --log-file processing.log process --config my_config.yaml input.docx output.json

# Process a directory
python -m textcleaner.cli process --format markdown documents/
```

## Development

### Prerequisites

- Python 3.9 or higher
- Required system dependencies (for PDF and Office document processing):
  - Tesseract OCR (optional, for image-based PDFs)
  - LibreOffice (optional, for advanced Office document handling)
  - Poppler-utils (for PDF processing)
  - lxml (for XML processing with proper features)

### Testing

The project includes extensive tests for all supported file types. Run the tests with:

```bash
python -m pytest
```

For more verbose test output:

```bash
python -m pytest -v
```

To run specific tests:

```bash
python -m pytest tests/integration/test_all_file_types.py -v
```

### Project Structure

```
textcleaner/
├── src/textcleaner/      # Main package directory
│   ├── converters/              # File format converters
│   │   ├── base.py             # Base converter class and registry
│   │   ├── html_converter.py   # HTML/XML document converter
│   │   ├── text_converter.py   # Plain text document converter
│   │   ├── markdown_converter.py # Markdown document converter with frontmatter support
│   │   └── ...                 # Other format converters
│   ├── processors/              # Text processing components
│   ├── outputs/                 # Output format writers
│   ├── config/                  # Configuration management 
│   │   └── config_manager.py   # Configuration loading and access
│   ├── utils/                   # Utility functions
│   ├── text_processor.py        # Main processor orchestration
│   └── cli.py                   # Command line interface
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests for individual components
│   └── integration/             # Integration tests across file types
│       └── test_all_file_types.py # Tests for all supported formats
├── test_html_files/             # Test files for HTML/XML processing
├── processed_files/             # Output directory for processed files
└── docs/                        # Documentation
```

### Example Results

The tool converts various document formats into clean, structured text:

- **HTML/XML** documents are cleaned of scripts, styles, and comments while preserving semantic structure
- **Markdown** files maintain their formatting while extracting metadata from frontmatter
- **Plain text** files are processed with minimal transformation while preserving content
- **PDF** documents with complex formatting result in clean Markdown that preserves structure while optimizing for token usage

All conversions include rich metadata extraction for downstream processing and analysis.

## Docker Containerization

The tool is available as a Docker container, which provides a consistent environment with all dependencies pre-installed.

```bash
# Use the provided shell script to run the container
./docker-run.sh input_file.pdf output_file.md
```

Or manually with Docker Compose:

```bash
docker-compose run --rm app process input/file.pdf output/file.md
```

## License

MIT
