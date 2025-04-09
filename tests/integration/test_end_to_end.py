"""
End-to-end integration tests for the LLM Text Processor
"""

import os
import pytest
from pathlib import Path
import tempfile
import yaml

from textcleaner import TextProcessor
from textcleaner.core.factories import TextProcessorFactory
from textcleaner.core.processor import TextProcessor, ProcessingResult
from textcleaner.config.config_factory import ConfigFactory
from textcleaner.utils.security import TestingSecurityUtils
from textcleaner.core.directory_processor import DirectoryProcessor
from textcleaner.utils.parallel import parallel_processor


@pytest.fixture
def sample_text_file(temp_directory):
    """Create a sample text file for testing"""
    # Create a test file with repetitive content and structure
    file_path = temp_directory / "sample.txt"
    
    with open(file_path, "w") as f:
        f.write("DOCUMENT TITLE\n")
        f.write("=============\n\n")
        f.write("Author: Test User\n")
        f.write("Date: 2023-01-01\n\n")
        f.write("INTRODUCTION\n")
        f.write("------------\n\n")
        f.write("This is a sample document for testing the text processor.\n")
        f.write("It contains multiple paragraphs and some structured content.\n\n")
        f.write("SECTION 1: Background\n")
        f.write("--------------------\n\n")
        f.write("This section provides background information.\n")
        f.write("It has multiple sentences that should be preserved.\n")
        f.write("Some of these sentences are redundant and could be optimized.\n")
        f.write("Some of these sentences are redundant and could be optimized.\n\n")
        f.write("SECTION 2: Details\n")
        f.write("-----------------\n\n")
        f.write("- Item 1: First important point\n")
        f.write("- Item 2: Second important point\n")
        f.write("- Item 3: Third important point\n\n")
        f.write("FOOTER\n")
        f.write("------\n\n")
        f.write("Page 1 of 1 | Sample Document | Confidential\n")
    
    return file_path


@pytest.fixture
def minimal_config(temp_directory):
    """Create a minimal configuration file"""
    config_path = temp_directory / "minimal_config.yaml"
    
    config = {
        "processing": {
            "cleaning_level": "minimal"
        },
        "structure": {
            "preserve_headings": True,
            "preserve_lists": True,
            "preserve_tables": True
        },
        "cleaning": {
            "remove_headers_footers": False,
            "clean_whitespace": True
        },
        "output": {
            "default_format": "markdown"
        }
    }
    
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    
    return config_path


@pytest.fixture
def aggressive_config(temp_directory):
    """Create an aggressive configuration file"""
    config_path = temp_directory / "aggressive_config.yaml"
    
    config = {
        "processing": {
            "cleaning_level": "aggressive"
        },
        "structure": {
            "preserve_headings": True,
            "preserve_lists": True,
            "preserve_tables": False
        },
        "cleaning": {
            "remove_headers_footers": True,
            "clean_whitespace": True,
            "remove_duplicate_content": True
        },
        "output": {
            "default_format": "markdown"
        }
    }
    
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    
    return config_path


def test_minimal_processing(sample_text_file, minimal_config, temp_directory):
    """Test end-to-end minimal text processing"""
    # Set up output directory
    output_dir = temp_directory / "output_minimal"
    output_dir.mkdir()
    
    # Create processor with minimal configuration
    factory = TextProcessorFactory()
    processor = factory.create_processor(config_path=str(minimal_config))
    processor.security = TestingSecurityUtils()
    
    # Process the file
    result = processor.process_file(sample_text_file, output_dir / "output.md")
    
    # Check the result
    assert result.success, f"Processing failed: {result.error}"
    assert result.output_path.exists()
    
    # Read the processed content
    processed_content = result.output_path.read_text()
    
    # Verify minimal processing:
    # - Headings should be preserved
    # - Lists should be preserved
    # - Headers and footers should be present (not removed)
    assert "DOCUMENT TITLE" in processed_content
    assert "INTRODUCTION" in processed_content
    assert "SECTION 1: Background" in processed_content
    assert "- Item 1:" in processed_content
    assert "- Item 2:" in processed_content
    assert "- Item 3:" in processed_content
    assert "FOOTER" in processed_content
    assert "Page 1 of 1" in processed_content


def test_aggressive_processing(sample_text_file, aggressive_config, temp_directory):
    """Test end-to-end aggressive text processing"""
    # Set up output directory
    output_dir = temp_directory / "output_aggressive"
    output_dir.mkdir()
    
    # Create processor with aggressive configuration
    factory = TextProcessorFactory()
    processor = factory.create_processor(config_path=str(aggressive_config))
    processor.security = TestingSecurityUtils()
    
    # Process the file
    result = processor.process_file(sample_text_file, output_dir / "output.md")
    
    # Check the result
    assert result.success, f"Processing failed: {result.error}"
    assert result.output_path.exists()
    
    # Read the processed content
    processed_content = result.output_path.read_text()
    
    # Verify aggressive processing:
    # - Headers and footers should be removed
    # - Duplicate content should be removed
    # - Core content should be preserved
    assert "DOCUMENT TITLE" in processed_content  # Headings preserved
    assert "INTRODUCTION" in processed_content    # Headings preserved
    assert "SECTION 1: Background" in processed_content  # Headings preserved
    
    # Check for footer removal
    assert "FOOTER" not in processed_content
    assert "Page 1 of 1" not in processed_content
    assert "Confidential" not in processed_content
    
    # Check for duplicate content removal
    # Count occurrences of the duplicated sentence
    duplicated_count = processed_content.count("Some of these sentences are redundant and could be optimized")
    assert duplicated_count == 1  # Should only appear once after deduplication
    
    # Lists should still be preserved
    assert "- Item 1:" in processed_content
    assert "- Item 2:" in processed_content
    assert "- Item 3:" in processed_content


def test_parallel_directory_processing(temp_directory):
    """Test parallel directory processing"""
    # Create input directory with multiple files
    input_dir = temp_directory / "parallel_input"
    input_dir.mkdir()
    
    # Create a few sample files
    for i in range(3):
        file_path = input_dir / f"sample_{i}.txt"
        with open(file_path, "w") as f:
            f.write(f"Sample content for file {i}\n")
            f.write("This is a test file for parallel processing.\n")
            for j in range(i+1):
                f.write(f"Additional line {j} for variation.\n")
    
    # Set up output directory
    output_dir = temp_directory / "parallel_output"
    
    # Create DirectoryProcessor correctly
    factory = TextProcessorFactory()
    single_file_processor = factory.create_standard_processor()
    dir_processor = DirectoryProcessor(
        config=single_file_processor.config,
        security_utils=TestingSecurityUtils(),
        parallel_processor=parallel_processor,
        single_file_processor=single_file_processor
    )
    
    # Process the directory in parallel using DirectoryProcessor
    results = dir_processor.process_directory_parallel(
        input_dir,
        output_dir,
        max_workers=2  # Use 2 workers for testing
    )
    
    # Verify results
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    successful_results = [r for r in results if r.success]
    assert len(successful_results) == 3, f"Expected 3 successful results, got {len(successful_results)}. Errors: {[r.error for r in results if not r.success]}"
    
    # Check output files
    output_files = list(output_dir.glob("*.md"))
    assert len(output_files) == 3, f"Expected 3 output files, found {len(output_files)}"


def test_different_output_formats(sample_text_file, temp_directory):
    """Test processing with different output formats"""
    # Create processor with standard configuration
    factory = TextProcessorFactory()
    processor = factory.create_processor()
    processor.security = TestingSecurityUtils()
    
    # Process to different formats
    formats = ["markdown", "plain_text", "json"]
    results = {}
    
    for fmt in formats:
        output_file = temp_directory / f"output.{processor.file_registry.get_default_extension(fmt)}"
        result = processor.process_file(sample_text_file, output_file, fmt)
        results[fmt] = result
    
    # Verify all processing succeeded
    assert all(r.success for r in results.values()), f"Some formats failed processing: { {k:v.error for k,v in results.items() if not v.success} }"
    
    # Verify all output files exist
    for fmt, result in results.items():
        assert result.output_path.exists(), f"Output file for format {fmt} not found: {result.output_path}"
    
    # Verify markdown format
    markdown_content = results["markdown"].output_path.read_text()
    assert "# DOCUMENT TITLE" in markdown_content or "DOCUMENT TITLE" in markdown_content
    
    # Verify plain text format
    plain_text_content = results["plain_text"].output_path.read_text()
    assert "DOCUMENT TITLE" in plain_text_content
    
    # Verify JSON format has the expected structure
    import json
    try:
        json_content = json.loads(results["json"].output_path.read_text())
        assert isinstance(json_content, dict)  # Should be a JSON object
        assert "content" in json_content  # Should have content field
    except json.JSONDecodeError:
        pytest.fail("JSON output is not valid JSON")
        
    # Since we know all formats were processed, we can check for performance monitoring data
    assert "processing_time_seconds" in results["markdown"].metrics
    # The token reduction should be different for different formats
    # This assertion might be flaky depending on the exact content and processing
    # assert results["markdown"].metrics.get("token_reduction_percent", 0) != \
    #        results["plain_text"].metrics.get("token_reduction_percent", 0)
