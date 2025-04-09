#!/usr/bin/env python3
"""
Utility to check for import issues with the textcleaner package.

This script tests various import patterns to detect circular imports and
other import-related issues in the textcleaner package.
"""

import sys
import importlib
import argparse
from pathlib import Path
import time


def test_basic_imports():
    """Test basic imports from the package."""
    print("Testing basic imports...")
    
    imports = [
        ("textcleaner", "textcleaner package"),
        ("textcleaner.ConfigManager", "ConfigManager class"),
        ("textcleaner.TextProcessor", "TextProcessor class"),
        ("textcleaner.ProcessingResult", "ProcessingResult class")
    ]
    
    success = True
    for module_path, description in imports:
        try:
            print(f"  Importing {description}...")
            module_parts = module_path.split(".")
            if len(module_parts) > 1:
                # Import from package
                module = importlib.import_module(".".join(module_parts[:-1]))
                getattr(module, module_parts[-1])
            else:
                # Import entire package
                importlib.import_module(module_path)
            print("    ✓ Success")
        except ImportError as e:
            print(f"    ✗ Failed: {e}")
            success = False
        except AttributeError as e:
            print(f"    ✗ Failed to find attribute: {e}")
            success = False
    
    return success


def test_instances():
    """Test creating instances of key classes."""
    print("\nTesting class instantiation...")
    
    success = True
    try:
        print("  Creating a TextProcessor instance...")
        from textcleaner import TextProcessor
        processor = TextProcessor()
        print("    ✓ Success")
        
        print("  Creating a ConfigManager instance...")
        from textcleaner import ConfigManager
        config = ConfigManager()
        print("    ✓ Success")
    except Exception as e:
        print(f"    ✗ Failed: {e}")
        success = False
    
    return success


def test_module_groups():
    """Test importing various module groups."""
    print("\nTesting key module groups...")
    
    module_groups = [
        ("textcleaner.core.models", "Core models"),
        ("textcleaner.core.file_registry", "File registry"),
        ("textcleaner.converters", "Converters"),
        ("textcleaner.processors.processor_pipeline", "Processor pipeline"),
        ("textcleaner.cli.commands", "CLI commands"),
        ("textcleaner.utils.security", "Security utilities"),
        ("textcleaner.utils.parallel", "Parallel processing"),
        ("textcleaner.config.config_manager", "Configuration manager")
    ]
    
    success = True
    for module_path, description in module_groups:
        try:
            print(f"  Importing {description}...")
            importlib.import_module(module_path)
            print("    ✓ Success")
        except ImportError as e:
            print(f"    ✗ Failed: {e}")
            success = False
        except Exception as e:
            print(f"    ✗ Failed with error: {e}")
            success = False
    
    return success


def test_import_time():
    """Measure import time for various modules."""
    print("\nMeasuring import times...")
    
    modules = [
        "textcleaner",
        "textcleaner.core.processor",
        "textcleaner.utils.parallel",
        "textcleaner.converters"
    ]
    
    for module_path in modules:
        # Clear the module from sys.modules if it's already imported
        if module_path in sys.modules:
            del sys.modules[module_path]
        
        # Measure import time
        start_time = time.time()
        try:
            importlib.import_module(module_path)
            end_time = time.time()
            import_time = (end_time - start_time) * 1000  # Convert to milliseconds
            print(f"  {module_path}: {import_time:.2f}ms")
        except ImportError as e:
            print(f"  {module_path}: Failed - {e}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Check for import issues in the textcleaner package'
    )
    
    parser.add_argument(
        '--time',
        action='store_true',
        help='Include import time measurements'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Include more detailed output'
    )
    
    return parser.parse_args()


def main():
    """Main function to run import checks."""
    args = parse_arguments()
    
    print("TextCleaner Import Checker")
    print("=========================\n")
    
    # Add src directory to Python path if not installed
    if importlib.util.find_spec("textcleaner") is None:
        src_dir = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(src_dir))
        print(f"Added {src_dir} to Python path\n")
    
    # Run the tests
    basic_success = test_basic_imports()
    instance_success = test_instances()
    modules_success = test_module_groups()
    
    # Measure import times if requested
    if args.time:
        test_import_time()
    
    # Print overall summary
    print("\nImport Check Summary")
    print("===================")
    print(f"Basic imports: {'✓ Pass' if basic_success else '✗ Fail'}")
    print(f"Class instantiation: {'✓ Pass' if instance_success else '✗ Fail'}")
    print(f"Module groups: {'✓ Pass' if modules_success else '✗ Fail'}")
    
    overall_success = basic_success and instance_success and modules_success
    print(f"\nOverall result: {'✓ All tests passed!' if overall_success else '✗ Some tests failed'}")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main()) 