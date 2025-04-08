#!/usr/bin/env python3
"""
Debug script to check for import issues with the textcleaner package.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import key modules to check for circular imports
print("Testing imports...")

try:
    print("1. Importing textcleaner package...")
    import textcleaner
    print("   Success!")
    
    print("2. Importing ConfigManager...")
    from textcleaner import ConfigManager
    print("   Success!")
    
    print("3. Importing TextProcessor...")
    from textcleaner import TextProcessor
    print("   Success!")
    
    print("4. Importing ProcessingResult...")
    from textcleaner import ProcessingResult
    print("   Success!")
    
    print("5. Creating a TextProcessor instance...")
    processor = TextProcessor()
    print("   Success!")
    
    print("6. Testing core modules...")
    from textcleaner.core.models import ProcessingResult
    from textcleaner.core.file_registry import FileTypeRegistry
    print("   Success!")
    
    print("7. Testing converter modules...")
    from textcleaner.converters import register_converters
    print("   Success!")
    
    print("8. Testing processor pipeline...")
    from textcleaner.processors.processor_pipeline import ProcessorPipeline
    print("   Success!")
    
    print("9. Testing CLI modules...")
    from textcleaner.cli.commands import cli, process
    print("   Success!")
    
    print("\nAll imports successful! No circular import issues detected.")
    
except ImportError as e:
    print(f"\nImport error: {e}")
    print("Circular import or missing module detected!")
    sys.exit(1)
    
except Exception as e:
    print(f"\nError: {e}")
    sys.exit(1) 