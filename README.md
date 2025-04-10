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

- **Wide Format Support:** Converts PDF, DOCX, XLSX, PPTX, HTML, TXT, CSV, MD and more.
- **Intelligent Cleaning:** Removes headers/footers, page numbers, boilerplate text, duplicate content.
- **Structure Preservation:** Maintains headings, lists, tables, code blocks, and links where possible.
- **Content Optimization:** 
    - Simplifies citations and URLs.
    - Abbreviates common terms and domain-specific jargon (configurable).
    - Simplifies complex vocabulary using WordNet (default, requires NLTK data download on first run).
    - Condenses repetitive patterns and removes redundant phrases.
    - Optimizes line length (configurable).
- **Multiple Output Formats:** Generate clean Markdown, Plain Text, JSON, or CSV.
- **Metadata Extraction:** Includes relevant metadata (page count, author, etc.) in output.
- **Token Estimation:** Provides estimated token counts using `tiktoken`.
- **Configuration Presets:** Offers presets (`minimal`, `standard`, `llm_optimal`) for common use cases.
- **Parallel Processing:** Speeds up processing of multiple files.

## Installation

```bash
pip install textcleaner
```

This installs the core package with support for all standard formats (PDF, Office, HTML, etc.) and features, including vocabulary simplification.

**NLTK Data:** The first time you run the tool with vocabulary simplification enabled (which is the default), it will attempt to automatically download required NLTK data packages (`wordnet`, `omw-1.4`) if they are not found. This requires an internet connection.

**Development Installation:**

```bash
git clone https://github.com/your-username/textcleaner.git
cd textcleaner
pip install -e .[dev]
```

This installs the package in editable mode along with development dependencies (pytest, ruff, etc.).

## Core Dependencies

- `pypdf` & `pdfminer.six` (for PDF processing)
- `python-docx` (for DOCX)
- `openpyxl` & `xlrd` (for XLSX, XLS)
- `python-pptx` (for PPTX)
- `beautifulsoup4` & `lxml` (for HTML)
- `nltk` (for vocabulary simplification)
- `pyyaml` (for configuration)
- `click` (for CLI)
- `tqdm` (for progress bars)
- `pandas` (for CSV/Excel handling)
- `requests` (for potential web requests)
- `regex` (for advanced text matching)
- `psutil` (for system utilities)
- `tiktoken` (for token estimation)
- `markdown-it-py` (for Markdown parsing -> Plain Text/CSV)

## Basic Usage

```bash
textcleaner process <input_path> -o <output_dir> --format markdown
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
├── src/                       # Source code
│   └── textcleaner/           # Main package
│       ├── cli/               # Command-line interface
│       ├── config/            # Configuration handling
│       ├── converters/        # File format converters
│       ├── core/              # Core functionality
│       ├── outputs/           # Output formatters
│       ├── processors/        # Text processing modules
│       ├── tools/             # Utility tools
│       └── utils/             # Utility functions
├── tests/                     # Tests
│   ├── fixtures/              # Test fixtures
│   │   ├── docs/              # Test document files
│   │   └── html/              # Test HTML files
│   ├── integration/           # Integration tests
│   └── unit/                  # Unit tests
├── examples/                  # Usage examples
├── homebrew-formula/          # Homebrew installation scripts
└── ...                        # Other project files
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

## Recent Refactoring

The codebase has been refactored to improve organization and maintainability:

1. **Test organization**:
   - All test files are now properly organized in `tests/unit/` and `tests/integration/`
   - Unit tests are categorized by module (core, converters, config, utils)
   - Test fixtures are consolidated in `tests/fixtures/`

2. **Modular design**:
   - Removed redundant code across test files
   - Eliminated duplicate path handling code
   - Centralized test file path utilities
  
3. **Clean code principles**:
   - Improved code reusability with the fixtures module
   - Removed duplicate configuration code
   - Created consistent directory structure

4. **Simplified testing**:
   - Updated test runner script for simplicity
   - Improved documentation for tests
   - Added READMEs to explain directory organization

### Configuration File

You can customize the processing behavior extensively using a `config.yaml` file. Create one using:

```bash
textcleaner generate-config > my_config.yaml
```

Then edit `my_config.yaml`. To use it:

```bash
textcleaner process <input_path> -c my_config.yaml
```

Key configuration sections in `default_config.yaml` (generated or found in `src/textcleaner/config`):

- **`processors.content_cleaner`**: Flags to control basic cleaning steps (headers, whitespace, boilerplate, duplicates, footnotes).
- **`processors.content_optimizer`**: Flags for optimization steps.
    - `simplify_vocabulary`: Default `true`. Controls WordNet based simplification.
    - `abbreviate_common_terms`, `domain_abbreviations`, `simplify_citations`, `simplify_urls`, `condense_repetitive_patterns`, `remove_redundant_phrases`, `remove_excessive_punctuation`, `max_line_length`.
- **`output`**: Controls output format defaults, metadata inclusion.
- **`formats`**: Fine-tune extraction for specific input types (PDF, Office, Web).
- **`metrics`**: Control logging, reporting, token estimation.

(Note: Temporal optimization settings like `optimize_temporal` and `use_stanford_nlp` have been removed.)
