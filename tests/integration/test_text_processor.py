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
        
        # Initialize the processor
        self.processor = TextProcessor()
    
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
        self.assertTrue(result.success)
        self.assertEqual(result.output_path, output_path)
        self.assertTrue(output_path.exists())
        
        # Verify the content includes our markdown
        with open(output_path, "r") as f:
            content = f.read()
            self.assertIn("# Sample Document", content)
            self.assertIn("## Section 1", content)
            self.assertIn("## Section 2", content)
            self.assertIn("* Bullet point", content)
    
    def test_process_directory(self):
        """Test processing a directory of files"""
        # Create another test file
        second_file = self.input_dir / "sample2.txt"
        with open(second_file, "w") as f:
            f.write("# Second Sample\n\n")
            f.write("This is another sample document.\n")
        
        # Process the directory
        results = self.processor.process_directory(
            self.input_dir,
            self.output_dir,
            output_format="markdown"
        )
        
        # Verify the results
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.success for r in results))
        
        # Verify the output files exist
        self.assertTrue((self.output_dir / "sample.md").exists())
        self.assertTrue((self.output_dir / "sample2.md").exists())
    
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
        
        # Create processor with custom config
        custom_processor = TextProcessor(config_path=str(config_path))
        
        # Process a file
        output_path = self.output_dir / "custom_processed.txt"
        result = custom_processor.process_file(
            self.text_file,
            output_path=output_path
        )
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertTrue(output_path.exists())
        
        # Check that the default format is plain text
        config = custom_processor.config.get("output.default_format")
        self.assertEqual(config, "plain")


if __name__ == "__main__":
    unittest.main()
