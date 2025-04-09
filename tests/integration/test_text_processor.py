"""
Integration tests for the TextProcessor class
"""

import os
import tempfile
import unittest
from pathlib import Path

import pytest

from textcleaner.core.processor import TextProcessor
from textcleaner.config.config_manager import ConfigManager
from textcleaner.core.factories import TextProcessorFactory
from textcleaner.utils.security import TestSecurityUtils


@pytest.mark.integration
class TestTextProcessor(unittest.TestCase):
    """Integration test suite for the TextProcessor"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create test input and output directories
        self.input_dir = self.test_dir / "input"
        self.output_dir = self.test_dir / "output"
        self.input_dir.mkdir()
        self.output_dir.mkdir()
        
        # Create a simple text file for testing
        self.text_file = self.input_dir / "sample.txt"
        with open(self.text_file, "w") as f:
            f.write("# Sample Document\n\n")
            f.write("This is a sample document for testing the text processor.\n\n")
            f.write("## Section 1\n\n")
            f.write("This is the content of section 1.\n")
            f.write("It includes multiple lines of text.\n\n")
            f.write("## Section 2\n\n")
            f.write("This is the content of section 2.\n")
            f.write("* Bullet point 1\n")
            f.write("* Bullet point 2\n")
        
        # Initialize the processor using the factory and inject TestSecurityUtils
        factory = TextProcessorFactory()
        self.processor = factory.create_standard_processor()
        self.processor.security = TestSecurityUtils() # Inject test security utils
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.temp_dir.cleanup()
    
    def test_process_file_markdown(self):
        """Test processing a file to Markdown format"""
        output_path = self.output_dir / "sample.md"
        
        # Process the file
        result = self.processor.process_file(
            self.text_file, 
            output_path=output_path,
            output_format="markdown"
        )
        
        # Verify the result
        self.assertTrue(result.success, f"Processing failed: {result.error}") # Add error message
        self.assertEqual(result.output_path, output_path)
        self.assertTrue(output_path.exists())
        
        # Verify the content includes our markdown
        with open(output_path, "r") as f:
            content = f.read()
            self.assertIn("# Sample Document", content)
            self.assertIn("## Section 1", content)
            self.assertIn("## Section 2", content)
            self.assertIn("* Bullet point", content)
    
    # Note: TextProcessor itself doesn't handle directory processing anymore.
    # These tests should potentially be moved or adapted to test DirectoryProcessor.
    # Keeping them here for now but commenting out the direct call to process_directory.
    # def test_process_directory(self):
    #     """Test processing a directory of files"""
    #     # Create another test file
    #     second_file = self.input_dir / "sample2.txt"
    #     with open(second_file, "w") as f:
    #         f.write("# Second Sample\n\n")
    #         f.write("This is another sample document.\n")
    #
    #     # Process the directory - This method is deprecated/moved
    #     # results = self.processor.process_directory(
    #     #     self.input_dir,
    #     #     self.output_dir,
    #     #     output_format="markdown"
    #     # )
    #     # Replace with DirectoryProcessor instantiation and call if needed
    #     from textcleaner.core.directory_processor import DirectoryProcessor
    #     from textcleaner.utils.parallel import parallel_processor
    #     dir_processor = DirectoryProcessor(
    #         config=self.processor.config,
    #         security_utils=TestSecurityUtils(),
    #         parallel_processor=parallel_processor,
    #         single_file_processor=self.processor
    #     )
    #     results = dir_processor.process_directory(
    #         self.input_dir,
    #         self.output_dir,
    #         output_format="markdown"
    #     )
    #
    #     # Verify the results
    #     self.assertEqual(len(results), 2)
    #     self.assertTrue(all(r.success for r in results))
    #
    #     # Verify the output files exist
    #     self.assertTrue((self.output_dir / "sample.md").exists())
    #     self.assertTrue((self.output_dir / "sample2.md").exists())
    
    def test_custom_config(self):
        """Test processing with a custom configuration"""
        # Create a custom config
        config_path = self.test_dir / "custom_config.yaml"
        with open(config_path, "w") as f:
            f.write("""
            processing:
              clean_level: aggressive
              preserve_structure: true
              remove_headers_footers: true
            output:
              default_format: plain
              include_metadata: false
            """)
        
        # Create processor with custom config using factory
        factory = TextProcessorFactory()
        custom_processor = factory.create_processor(config_path=str(config_path))
        custom_processor.security = TestSecurityUtils() # Inject test security utils
        
        # Process a file
        output_path = self.output_dir / "custom_processed.txt"
        result = custom_processor.process_file(
            self.text_file,
            output_path=output_path
        )
        
        # Verify the result
        self.assertTrue(result.success, f"Processing failed: {result.error}") # Add error message
        self.assertTrue(output_path.exists())
        
        # Check that the default format is plain text
        config_val = custom_processor.config.get("output.default_format")
        self.assertEqual(config_val, "plain")


if __name__ == "__main__":
    unittest.main()
