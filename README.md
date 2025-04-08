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

- **Multiple Format Support**: Handles PDFs, Office documents, web content, plain text files, and more
- **Intelligent Cleaning**: Removes headers, footers, boilerplate content, and redundant information
- **Structure Preservation**: Maintains document hierarchy, lists, tables, and other semantic elements
- **Configurable Processing**: Adjustable cleaning levels from minimal to aggressive
- **Multiple Output Formats**: Export as plain text, Markdown, structured JSON, or CSV
- **Batch Processing**: Process entire directories of files with consistent settings
- **Performance Metrics**: Track token reduction and processing efficiency
- **Docker Support**: Run in a consistent environment across platforms
- **Python 3.9+ Compatible**: Works with a wide range of Python environments

## Installation

### Using pip

```bash
pip install llm-text-processor
```

### Using Docker

```bash
# Pull the Docker image
docker pull your-username/llm-text-processor:latest

# Or build from source
docker build -t llm-text-processor .

# Run using Docker
docker run -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output llm-text-processor process input/document.pdf output/document.md
```

### From Source

```bash
# Clone the repository
git clone https://github.com/your-username/llm-text-processor.git
cd llm-text-processor

# Install dependencies
pip install -e .
```

## Quick Start

```python
from llm_text_processor import TextProcessor

# Create processor with default settings
processor = TextProcessor()

# Process a single file
result = processor.process_file("document.pdf", output_format="markdown")
print(f"Output saved to: {result.output_path}")
print(f"Token reduction: {result.metrics.token_reduction_percent}%")

# Process a directory
results = processor.process_directory("documents/", output_format="json")
print(f"Processed {len(results)} files")
```

## Command Line Usage

```bash
# Process a single file
llm-preprocess input.pdf output.md

# Process with specific configuration
llm-preprocess --config my_config.yaml input.docx output.json

# Process a directory
llm-preprocess --batch --output-dir clean_texts/ documents/
```

## Development

### Prerequisites

- Python 3.9 or higher
- Required system dependencies (for PDF and Office document processing):
  - Tesseract OCR (optional, for image-based PDFs)
  - LibreOffice (optional, for advanced Office document handling)
  - Poppler-utils (for PDF processing)

### Project Structure

```
llm-text-processor/
├── src/llm_text_processor/      # Main package directory
│   ├── converters/              # File format converters
│   ├── processors/              # Text processing components
│   ├── outputs/                 # Output format writers
│   ├── config/                  # Configuration management
│   └── utils/                   # Utility functions
├── data/                        # Sample data files
│   ├── input/                   # Input files for testing
│   └── output/                  # Output directory for processed files
├── docker/                      # Docker configuration files
├── tests/                       # Test suite
└── docs/                        # Documentation
```

### Example Results

The tool converts various document formats into clean, structured text. For example, converting a PDF document with complex formatting will result in a clean Markdown file that preserves the document's structure while optimizing for token usage.

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
