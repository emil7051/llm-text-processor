"""
Unit tests for the ConfigManager class
"""

import os
import tempfile
import unittest
from pathlib import Path

import pytest
import yaml

from llm_text_processor.config.config_manager import ConfigManager


@pytest.mark.unit
class TestConfigManager(unittest.TestCase):
    """Test suite for the ConfigManager class"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = Path(self.temp_dir.name) / "test_config.yaml"
        
        # Create a test configuration file
        self.test_config = {
            "processing": {
                "clean_level": "standard",
                "preserve_structure": True,
                "remove_headers_footers": True,
            },
            "output": {
                "default_format": "markdown",
                "include_metadata": True,
            }
        }
        
        with open(self.config_file, "w") as f:
            yaml.dump(self.test_config, f)
        
        # Initialize the config manager with default settings
        self.config_manager = ConfigManager()
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.temp_dir.cleanup()
    
    def test_load_from_file(self):
        """Test loading configuration from a file"""
        config = self.config_manager._load_from_file(self.config_file)
        self.assertEqual(config["processing"]["clean_level"], "standard")
        self.assertTrue(config["processing"]["preserve_structure"])
        self.assertEqual(config["output"]["default_format"], "markdown")
    
    def test_get_config_with_defaults(self):
        """Test getting configuration with defaults"""
        # Load our test config
        self.config_manager.load_config(self.config_file)
        
        # Test that values from the file are used
        self.assertEqual(
            self.config_manager.get_config("processing.clean_level"), 
            "standard"
        )
        
        # Test that a default value is used for a non-existent key
        self.assertEqual(
            self.config_manager.get_config("non_existent", "default_value"), 
            "default_value"
        )
    
    def test_merge_configs(self):
        """Test merging configurations"""
        base_config = {
            "processing": {
                "clean_level": "minimal",
                "preserve_structure": True,
            },
            "output": {
                "default_format": "text",
            }
        }
        
        override_config = {
            "processing": {
                "clean_level": "aggressive",
            },
            "new_section": {
                "new_key": "new_value",
            }
        }
        
        merged = self.config_manager._merge_configs(base_config, override_config)
        
        # Check that values are properly overridden
        self.assertEqual(merged["processing"]["clean_level"], "aggressive")
        
        # Check that non-overridden values remain
        self.assertTrue(merged["processing"]["preserve_structure"])
        self.assertEqual(merged["output"]["default_format"], "text")
        
        # Check that new sections are added
        self.assertEqual(merged["new_section"]["new_key"], "new_value")


if __name__ == "__main__":
    unittest.main()
