import unittest
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import yaml

# Import the class to test
from textcleaner.config.config_factory import ConfigFactory

# Mock preset functions
MOCK_PRESETS = {
    "gpt-3.5": {"model_specific": True, "processing": {"clean_level": "preset_level"}},
    "claude-2": {"model_specific": True, "processing": {"preserve_structure": True}}
}
MOCK_PRESET_NAMES = list(MOCK_PRESETS.keys())

@pytest.mark.unit
class TestConfigFactory(unittest.TestCase):
    """Test suite for the ConfigFactory."""

    def setUp(self):
        """Set up test fixtures for each test."""
        # Patch preset functions globally for all tests
        self.get_preset_patcher = patch(
            f'{ConfigFactory.__module__}.get_preset', 
            side_effect=lambda name: MOCK_PRESETS.get(name, {})
        )
        self.get_preset_names_patcher = patch(
            f'{ConfigFactory.__module__}.get_preset_names', 
            return_value=MOCK_PRESET_NAMES
        )
        self.mock_get_preset = self.get_preset_patcher.start()
        self.mock_get_preset_names = self.get_preset_names_patcher.start()
        self.addCleanup(self.get_preset_patcher.stop)
        self.addCleanup(self.get_preset_names_patcher.stop)
        
        self.factory = ConfigFactory()
        self.test_config_path = "custom_config.yaml"
        self.base_config = {"base": True, "processing": {"clean_level": "base"}}
        self.override_config = {"override": True, "processing": {"preserve_structure": False}}

    # --- create_processor_config Tests ---

    @patch.object(ConfigFactory, 'load_config')
    @patch.object(ConfigFactory, 'create_default_config')
    @patch.object(ConfigFactory, '_apply_overrides')
    def test_create_processor_config_with_path(self, mock_apply, mock_create_default, mock_load):
        """Test create_processor_config loads from path and applies overrides."""
        loaded_config = {"loaded": True}
        final_config = {"final": True}
        mock_load.return_value = loaded_config
        mock_apply.return_value = final_config # Simulate override application
        
        result = self.factory.create_processor_config(
            config_path=self.test_config_path, 
            custom_overrides=self.override_config
        )
        
        mock_load.assert_called_once_with(self.test_config_path)
        mock_create_default.assert_not_called()
        mock_apply.assert_called_once_with(loaded_config, self.override_config)
        self.assertEqual(result, final_config)

    @patch.object(ConfigFactory, 'load_config')
    @patch.object(ConfigFactory, 'create_default_config')
    @patch.object(ConfigFactory, '_apply_overrides')
    def test_create_processor_config_no_path(self, mock_apply, mock_create_default, mock_load):
        """Test create_processor_config uses default type when no path is given."""
        default_config = {"default": "standard"}
        final_config = {"final": True}
        mock_create_default.return_value = default_config
        mock_apply.return_value = final_config # Simulate override application
        
        result = self.factory.create_processor_config(
            config_type='standard', 
            custom_overrides=self.override_config
        )
        
        mock_load.assert_not_called()
        mock_create_default.assert_called_once_with('standard')
        mock_apply.assert_called_once_with(default_config, self.override_config)
        self.assertEqual(result, final_config)

    @patch.object(ConfigFactory, 'load_config')
    @patch.object(ConfigFactory, 'create_default_config')
    @patch.object(ConfigFactory, '_apply_overrides')
    def test_create_processor_config_no_overrides(self, mock_apply, mock_create_default, mock_load):
        """Test create_processor_config doesn't apply overrides if none are given."""
        default_config = {"default": "minimal"}
        mock_create_default.return_value = default_config
        
        result = self.factory.create_processor_config(config_type='minimal') # No overrides
        
        mock_load.assert_not_called()
        mock_create_default.assert_called_once_with('minimal')
        mock_apply.assert_not_called()
        self.assertEqual(result, default_config) # Should be the direct result from create_default

    # --- create_default_config Tests ---

    @patch.object(ConfigFactory, '_get_config_template')
    def test_create_default_config_valid_type(self, mock_get_template):
        """Test create_default_config gets template for valid standard type."""
        template_config = {"type": "aggressive"}
        mock_get_template.return_value = template_config
        
        result = self.factory.create_default_config('aggressive')
        
        mock_get_template.assert_called_once_with('aggressive')
        self.assertEqual(result, template_config)
        self.mock_get_preset.assert_not_called()

    @patch.object(ConfigFactory, '_get_config_template')
    def test_create_default_config_invalid_type(self, mock_get_template):
        """Test create_default_config falls back to 'standard' for invalid type."""
        standard_config = {"type": "standard"}
        mock_get_template.return_value = standard_config
        
        result = self.factory.create_default_config('invalid_type')
        
        # Should call get_template with 'standard' after warning
        mock_get_template.assert_called_once_with('standard') 
        self.assertEqual(result, standard_config)
        self.mock_get_preset.assert_not_called()

    @patch.object(ConfigFactory, '_get_config_template')
    @patch.object(ConfigFactory, '_apply_overrides')
    def test_create_default_config_preset_type(self, mock_apply, mock_get_template):
        """Test create_default_config handles preset types correctly."""
        standard_template = {"base": True, "processing": {"clean_level": "standard"}}
        preset_override = MOCK_PRESETS["gpt-3.5"]
        final_merged_config = {"final": True}
        
        mock_get_template.return_value = standard_template
        mock_apply.return_value = final_merged_config
        
        result = self.factory.create_default_config('gpt-3.5')
        
        self.mock_get_preset.assert_called_once_with('gpt-3.5')
        # Should get the 'standard' template as base for presets
        mock_get_template.assert_called_once_with('standard') 
        # Should apply preset overrides onto the standard base
        mock_apply.assert_called_once_with(standard_template, preset_override)
        self.assertEqual(result, final_merged_config)

    # --- load_config Tests ---

    @patch('pathlib.Path.exists', return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="key: value\nvalid: true")
    @patch(f'{ConfigFactory.__module__}.yaml.safe_load')
    def test_load_config_success(self, mock_safe_load, mock_file, mock_exists):
        """Test load_config successfully loads and parses a valid YAML file."""
        expected_config = {"key": "value", "valid": True}
        mock_safe_load.return_value = expected_config
        
        result = self.factory.load_config(self.test_config_path)
        
        mock_exists.assert_called_once()
        mock_file.assert_called_once_with(Path(self.test_config_path), 'r', encoding='utf-8')
        mock_safe_load.assert_called_once()
        self.assertEqual(result, expected_config)

    @patch('pathlib.Path.exists', return_value=False)
    def test_load_config_not_found(self, mock_exists):
        """Test load_config raises FileNotFoundError if file doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            self.factory.load_config("nonexistent.yaml")
        mock_exists.assert_called_once()

    @patch('pathlib.Path.exists', return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="key: value\nvalid: true")
    @patch(f'{ConfigFactory.__module__}.yaml.safe_load', return_value="not_a_dict")
    def test_load_config_invalid_format(self, mock_safe_load, mock_file, mock_exists):
        """Test load_config raises ValueError if YAML doesn't parse to a dict."""
        with self.assertRaisesRegex(ValueError, "Invalid configuration format"):
            self.factory.load_config(self.test_config_path)
        mock_exists.assert_called_once()
        mock_file.assert_called_once()
        mock_safe_load.assert_called_once()

    # --- save_config Tests ---

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists', return_value=False) # Assume parent dir doesn't exist
    @patch("builtins.open", new_callable=mock_open)
    @patch(f'{ConfigFactory.__module__}.yaml.dump')
    def test_save_config_success_creates_dir(self, mock_dump, mock_file_open, mock_exists, mock_mkdir):
        """Test save_config creates parent directory if needed and saves."""
        config_to_save = {"data": 1}
        output_path = "new_dir/saved_config.yaml"
        
        self.factory.save_config(config_to_save, output_path)
        
        mock_exists.assert_called_once() # Called on parent path
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_file_open.assert_called_once_with(Path(output_path), 'w', encoding='utf-8')
        mock_dump.assert_called_once_with(config_to_save, mock_file_open(), sort_keys=False, default_flow_style=False)

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists', return_value=True) # Assume parent dir exists
    @patch("builtins.open", new_callable=mock_open)
    @patch(f'{ConfigFactory.__module__}.yaml.dump')
    def test_save_config_success_dir_exists(self, mock_dump, mock_file_open, mock_exists, mock_mkdir):
        """Test save_config saves correctly when parent directory exists."""
        config_to_save = {"data": 2}
        output_path = "existing_dir/saved_config.yaml"
        
        self.factory.save_config(config_to_save, output_path)
        
        mock_exists.assert_called_once()
        mock_mkdir.assert_not_called()
        mock_file_open.assert_called_once()
        mock_dump.assert_called_once()
        
    @patch('pathlib.Path.exists', return_value=True)
    @patch("builtins.open", side_effect=IOError("Disk full"))
    def test_save_config_io_error(self, mock_file_open, mock_exists):
        """Test save_config raises ValueError on file write error."""
        config_to_save = {"data": 3}
        output_path = "some_dir/config.yaml"
        
        with self.assertRaisesRegex(ValueError, "Failed to save configuration: Disk full"):
            self.factory.save_config(config_to_save, output_path)
        mock_exists.assert_called_once()
        mock_file_open.assert_called_once()

    # Placeholder test can be removed or replaced
    # def test_placeholder(self):
    #     """Placeholder test for ConfigFactory."""
    #     # TODO: Implement actual tests for ConfigFactory
    #     self.assertTrue(True) # Replace with real assertions


if __name__ == "__main__":
    unittest.main()
