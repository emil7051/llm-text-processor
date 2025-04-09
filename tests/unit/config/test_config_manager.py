"""
Unit tests for the ConfigManager class
"""

import os
import tempfile
import unittest
from pathlib import Path

import pytest
import yaml
from unittest.mock import patch, MagicMock, mock_open

from textcleaner.config.config_manager import ConfigManager


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
        # Load our test config and manually merge it
        test_config = self.config_manager._load_from_file(self.config_file)
        self.config_manager._merge_config(test_config)
        
        # Test that values from the file are used
        self.assertEqual(
            self.config_manager.get("processing.clean_level"), 
            "standard"
        )
        
        # Test that a default value is used for a non-existent key
        self.assertEqual(
            self.config_manager.get("non_existent", "default_value"), 
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
        
        # Create a new config manager for testing merge
        test_manager = ConfigManager()
        test_manager.config = base_config.copy()
        test_manager._merge_config(override_config)
        
        # Check that values are properly overridden
        self.assertEqual(test_manager.config["processing"]["clean_level"], "aggressive")
        
        # Check that non-overridden values remain
        self.assertTrue(test_manager.config["processing"]["preserve_structure"])
        self.assertEqual(test_manager.config["output"]["default_format"], "text")
        
        # Check that new sections are added
        self.assertEqual(test_manager.config["new_section"]["new_key"], "new_value")

    # --- Additional __init__ tests ---

    @patch('textcleaner.config.config_manager.ConfigManager._load_default_config')
    def test_init_with_initial_config(self, mock_load_default):
        """Test init uses initial_config directly without loading defaults or files."""
        initial = {"initial": True, "value": 1}
        manager = ConfigManager(initial_config=initial, config_path="ignore.yaml", overrides={"override": True})
        self.assertEqual(manager.config, initial)
        mock_load_default.assert_not_called()
        # Note: config_path and overrides are ignored when initial_config is provided

    @patch('textcleaner.config.config_manager.ConfigManager._load_from_file')
    @patch('textcleaner.config.config_manager.ConfigManager._load_default_config')
    def test_init_with_overrides_only(self, mock_load_default, mock_load_file):
        """Test init loads defaults and merges overrides when only overrides are given."""
        default_conf = {"default": True, "nested": {"a": 1}}
        overrides_conf = {"override": True, "nested": {"b": 2}}
        mock_load_default.return_value = default_conf
        
        manager = ConfigManager(overrides=overrides_conf)
        
        mock_load_default.assert_called_once()
        mock_load_file.assert_not_called() # No config_path given
        
        expected_config = {
            "default": True, 
            "override": True, 
            "nested": {"a": 1, "b": 2}
        }
        self.assertEqual(manager.config, expected_config)

    @patch('textcleaner.config.config_manager.ConfigManager._load_from_file')
    @patch('textcleaner.config.config_manager.ConfigManager._load_default_config')
    def test_init_with_path_and_overrides(self, mock_load_default, mock_load_file):
        """Test init loads defaults, file, and overrides in correct order."""
        default_conf = {"a": 1, "b": 10, "c": {"d": 100}}
        file_conf = {"b": 20, "c": {"e": 200}, "f": 2000}
        overrides_conf = {"a": 3, "c": {"d": 300}, "g": 3000}
        
        mock_load_default.return_value = default_conf
        # Since _load_default_config is mocked, _load_from_file is only called
        # once with the user config path. Set return_value directly.
        mock_load_file.return_value = file_conf
        
        manager = ConfigManager(config_path="user.yaml", overrides=overrides_conf)
        
        mock_load_default.assert_called_once()
        mock_load_file.assert_called_once_with("user.yaml")
        
        expected_config = {
            "a": 3, # from override
            "b": 20, # from file
            "c": {
                "d": 300, # from override
                "e": 200 # from file
            },
            "f": 2000, # from file
            "g": 3000 # from override
        }
        self.assertEqual(manager.config, expected_config)

    # --- _load_from_file Error Tests ---
    
    @patch('pathlib.Path.exists', return_value=False)
    def test_load_from_file_not_found(self, mock_exists):
        """Test _load_from_file raises FileNotFoundError."""
        manager = ConfigManager(initial_config={}) # Avoid default loading
        test_path = "nonexistent.yaml"
        with self.assertRaises(FileNotFoundError):
            manager._load_from_file(test_path)
        mock_exists.assert_called_once()

    @patch('pathlib.Path.exists', return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    @patch(f'{ConfigManager.__module__}.yaml.safe_load', side_effect=yaml.YAMLError("Bad YAML"))
    def test_load_from_file_yaml_error(self, mock_safe_load, mock_file_open, mock_exists):
        """Test _load_from_file raises YAMLError on parsing failure."""
        manager = ConfigManager(initial_config={})
        test_path = "invalid.yaml"
        with self.assertRaises(yaml.YAMLError):
            manager._load_from_file(test_path)
        mock_exists.assert_called_once()
        mock_file_open.assert_called_once_with(Path(test_path), 'r', encoding='utf-8')
        mock_safe_load.assert_called_once()
        
    # --- get() and get_section() Tests ---
    
    def test_get_nested_key(self):
        """Test get() retrieves a deeply nested key."""
        self.config_manager.config = {"level1": {"level2": {"level3": "value"}}}
        self.assertEqual(self.config_manager.get("level1.level2.level3"), "value")

    def test_get_non_existent_nested_key(self):
        """Test get() returns default for non-existent nested key."""
        self.config_manager.config = {"level1": {"level2": {}}}
        self.assertEqual(self.config_manager.get("level1.level2.nonexistent", "default"), "default")
        self.assertIsNone(self.config_manager.get("level1.level2.nonexistent"))

    def test_get_intermediate_not_dict(self):
        """Test get() returns default if an intermediate key is not a dictionary."""
        self.config_manager.config = {"level1": "not_a_dict"}
        self.assertEqual(self.config_manager.get("level1.level2", "default"), "default")
        
    def test_get_section_exists(self):
        """Test get_section() returns an existing section."""
        section_data = {"key1": "val1", "key2": True}
        self.config_manager.config = {"my_section": section_data, "other": {}}
        self.assertEqual(self.config_manager.get_section("my_section"), section_data)
        
    def test_get_section_not_exists(self):
        """Test get_section() returns an empty dict for non-existent section."""
        self.config_manager.config = {"other": {}}
        self.assertEqual(self.config_manager.get_section("non_existent_section"), {})
        
    # --- save_to_file() Tests ---
    
    @patch("builtins.open", new_callable=mock_open)
    @patch(f'{ConfigManager.__module__}.yaml.dump')
    def test_save_to_file_success(self, mock_dump, mock_file_open):
        """Test save_to_file calls open and yaml.dump correctly."""
        save_path = "output_config.yaml"
        current_config = {"save": "me"}
        self.config_manager.config = current_config
        
        self.config_manager.save_to_file(save_path)
        
        mock_file_open.assert_called_once_with(save_path, 'w', encoding='utf-8')
        mock_dump.assert_called_once_with(current_config, mock_file_open(), default_flow_style=False)
        
    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_save_to_file_io_error(self, mock_file_open):
        """Test save_to_file propagates IOError."""
        save_path = "locked_dir/config.yaml"
        with self.assertRaises(IOError):
            self.config_manager.save_to_file(save_path)
        mock_file_open.assert_called_once_with(save_path, 'w', encoding='utf-8')

    # --- __str__() Test ---
    
    @patch(f'{ConfigManager.__module__}.yaml.dump')
    def test_str_representation(self, mock_dump):
        """Test __str__ calls yaml.dump."""
        config_data = {"key": "value"}
        self.config_manager.config = config_data
        mock_dump.return_value = "yaml string representation"
        
        str_repr = str(self.config_manager)
        
        mock_dump.assert_called_once_with(config_data, default_flow_style=False)
        self.assertEqual(str_repr, "yaml string representation")


if __name__ == "__main__":
    unittest.main()
