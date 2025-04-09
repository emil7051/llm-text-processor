"""
Path utilities for tests.

This module provides consistent access to test file paths and directories.
"""

from pathlib import Path

# Base paths
ROOT_DIR = Path(__file__).parent.parent.parent
FIXTURES_DIR = Path(__file__).parent
SRC_DIR = ROOT_DIR / "src"

# Test data paths
HTML_DIR = FIXTURES_DIR / "html"
DOCS_DIR = FIXTURES_DIR / "docs"

def get_html_file(filename):
    """Get path to a test HTML file.
    
    Args:
        filename: Name of the HTML file
        
    Returns:
        Path to the HTML file
    """
    return HTML_DIR / filename

def get_doc_file(filename):
    """Get path to a test document file.
    
    Args:
        filename: Name of the document file
        
    Returns:
        Path to the document file
    """
    return DOCS_DIR / filename 