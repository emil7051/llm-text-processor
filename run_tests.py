#!/usr/bin/env python3
"""
Helper script to run tests with the correct Python path.

This script provides convenient shortcuts for running different test suites.
"""

import os
import sys
import subprocess
import argparse


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run tests for TextCleaner"
    )
    
    # Test selection options
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--unit", "-u",
        action="store_true",
        help="Run only unit tests"
    )
    group.add_argument(
        "--integration", "-i",
        action="store_true",
        help="Run only integration tests"
    )
    group.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all tests (default)"
    )
    
    # Coverage options
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage report"
    )
    
    # Output options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    # Specific tests
    parser.add_argument(
        "tests",
        nargs="*",
        help="Specific test files or directories to run"
    )
    
    return parser.parse_args()


def run_tests(args=None):
    """
    Run pytest with the specified arguments.
    
    Args:
        args: Command-line arguments (defaults to sys.argv if None)
        
    Returns:
        Exit code from pytest
    """
    if args is None:
        args = parse_arguments()
    
    # Base pytest command
    cmd = ["python3", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=textcleaner", "--cov-report=term", "--cov-report=html"])
    
    # Add test selection
    if args.unit:
        cmd.append("tests/unit")
    elif args.integration:
        cmd.append("tests/integration")
    
    # Add specific tests if provided
    if args.tests:
        cmd.extend(args.tests)
    elif not any([args.unit, args.integration]):
        # If no specific type or tests, run all tests
        cmd.append("tests/")
    
    # Run the tests
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
