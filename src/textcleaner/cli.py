"""Command-line interface for the Text Cleaner.

This module provides the main CLI functionality.
The actual implementation has been moved to textcleaner.cli.commands.
"""

# Import from the new module structure
from textcleaner.cli.commands import cli, process, generate_config, list_formats, main

# This file exists to provide the main CLI interface
# All implementation is now in textcleaner.cli.commands

# Define main function for entry point compatibility
def main():
    """Entry point for the CLI."""
    cli()
