
"""
Pytest configuration and shared fixtures
"""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def sample_files():
    """Create sample files for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a directory structure for sample files
        root_dir = Path(temp_dir)
        
        # Plain text samples
        txt_dir = root_dir / "text"
        txt_dir.mkdir()
        
        simple_txt = txt_dir / "simple.txt"
        with open(simple_txt, "w") as f:
            f.write("This is a simple text file.\n")
            f.write("It has multiple lines.\n")
            f.write("For testing purposes.\n")
        
        # Markdown samples
        md_dir = root_dir / "markdown"
        md_dir.mkdir()
        
        markdown_file = md_dir / "sample.md"
        with open(markdown_file, "w") as f:
            f.write("# Sample Markdown\n\n")
            f.write("This is a *markdown* file with **formatting**.\n\n")
            f.write("## Section 1\n\n")
            f.write("- Item 1\n")
            f.write("- Item 2\n\n")
        
        # Yield the created directory structure
        yield {
            "root_dir": root_dir,
            "text_dir": txt_dir,
            "markdown_dir": md_dir,
            "simple_txt": simple_txt,
            "markdown_file": markdown_file
        }


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test use"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_config_file(temp_directory):
    """Create a sample configuration file"""
    config_file = temp_directory / "test_config.yaml"
    
    with open(config_file, "w") as f:
        f.write("""
        processing:
          clean_level: standard
          preserve_structure: true
          remove_headers_footers: true
          token_optimization: true
        output:
          default_format: markdown
          include_metadata: true
          metadata_format: yaml
        """)
    
    return config_file
