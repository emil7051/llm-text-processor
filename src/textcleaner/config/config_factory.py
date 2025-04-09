"""Configuration factory for TextCleaner.

This module provides a factory for creating different types of configurations.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union

from textcleaner.utils.logging_config import get_logger
from textcleaner.config.presets import get_preset, get_preset_names


class ConfigFactory:
    """Factory for creating configuration objects."""
    
    DEFAULT_CONFIG_TYPES = ['minimal', 'standard', 'aggressive']
    
    def __init__(self):
        """Initialize the configuration factory."""
        self.logger = get_logger(__name__)
    
    def create_processor_config(
        self, 
        config_path: Optional[str] = None, 
        config_type: str = 'standard',
        custom_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a processor configuration.
        
        Args:
            config_path: Path to a custom configuration file
            config_type: Type of default configuration to use if no path provided
            custom_overrides: Custom configuration overrides to apply
            
        Returns:
            A configuration dictionary
        """
        config = {}
        
        if config_path:
            # Load from custom configuration file
            config = self.load_config(config_path)
            self.logger.info(f"Loaded configuration from {config_path}")
        else:
            # Use a default configuration
            config = self.create_default_config(config_type)
            self.logger.info(f"Using {config_type} configuration")
        
        # Apply custom overrides if provided
        if custom_overrides:
            config = self._apply_overrides(config, custom_overrides)
            self.logger.debug(f"Applied {len(custom_overrides)} custom overrides")
        
        return config
    
    def create_default_config(self, config_type: str = 'standard') -> Dict[str, Any]:
        """Create a default configuration of the specified type.
        
        Args:
            config_type: Type of configuration to create
            
        Returns:
            A configuration dictionary
        """
        if config_type not in self.DEFAULT_CONFIG_TYPES and config_type not in get_preset_names():
            self.logger.warning(f"Unknown configuration type: {config_type}, using 'standard'")
            config_type = 'standard'
        
        # Check if it's an LLM preset
        if config_type in get_preset_names():
            self.logger.info(f"Using LLM preset: {config_type}")
            preset_config = get_preset(config_type)
            base_config = self._get_config_template("standard")
            return self._apply_overrides(base_config, preset_config)
        
        # Otherwise use standard configuration types
        return self._get_config_template(config_type)
    
    def create_custom_config(
        self, 
        base_type: str = 'standard',
        overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a custom configuration based on a default type with overrides.
        
        Args:
            base_type: Base configuration type
            overrides: Custom overrides to apply
            
        Returns:
            A customized configuration dictionary
        """
        # Get base configuration
        config = self.create_default_config(base_type)
        
        # Apply overrides if provided
        if overrides:
            config = self._apply_overrides(config, overrides)
            
        return config
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load a configuration from a file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            A configuration dictionary
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file can't be parsed
        """
        try:
            path = Path(config_path)
            if not path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
                
            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            if not isinstance(config, dict):
                raise ValueError(f"Invalid configuration format in {config_path}")
                
            return config
        except Exception as e:
            self.logger.error(f"Error loading configuration from {config_path}: {str(e)}")
            raise
    
    def save_config(self, config: Dict[str, Any], output_path: str) -> None:
        """Save a configuration to a file.
        
        Args:
            config: Configuration dictionary
            output_path: Path to save the file
            
        Raises:
            ValueError: If the configuration can't be saved
        """
        try:
            path = Path(output_path)
            
            # Create directory if needed
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, sort_keys=False, default_flow_style=False)
                
            self.logger.info(f"Saved configuration to {output_path}")
        except Exception as e:
            self.logger.error(f"Error saving configuration to {output_path}: {str(e)}")
            raise ValueError(f"Failed to save configuration: {str(e)}")
    
    def _get_config_template(self, config_type: str) -> Dict[str, Any]:
        """Get a configuration template of the specified type.
        
        Args:
            config_type: Type of configuration template
            
        Returns:
            A configuration dictionary
        """
        templates_dir = Path(__file__).parent / 'templates'
        standard_template_path = templates_dir / "standard.yaml"
        specific_template_path = templates_dir / f"{config_type}.yaml"

        # Load standard template first
        base_config = {}
        if standard_template_path.exists():
            try:
                with open(standard_template_path, 'r', encoding='utf-8') as f:
                    base_config = yaml.safe_load(f)
            except Exception as e:
                self.logger.error(f"Error loading standard template {standard_template_path}: {str(e)}")
                # Fall back to minimal if standard fails
                base_config = self._get_builtin_minimal_config()
        else:
            # If standard doesn't exist, use minimal as base
            self.logger.warning("Standard template not found, using built-in minimal template as base")
            base_config = self._get_builtin_minimal_config()

        # If the requested type is standard, return the base config
        if config_type == "standard":
            return base_config

        # Load the specific template (e.g., aggressive)
        specific_config = {}
        if specific_template_path.exists():
            try:
                with open(specific_template_path, 'r', encoding='utf-8') as f:
                    specific_config = yaml.safe_load(f)
            except Exception as e:
                self.logger.error(f"Error loading specific template {specific_template_path}: {str(e)}. Using standard config.")
                return base_config # Return base if specific fails
        else:
            # If specific template doesn't exist, log and return base
            self.logger.warning(f"Template for {config_type} not found. Using standard config.")
            return base_config 

        # Merge specific config onto the base config
        return self._apply_overrides(base_config, specific_config)
    
    def _get_builtin_minimal_config(self) -> Dict[str, Any]:
        """Get a minimal built-in configuration.
        
        Returns:
            A minimal configuration dictionary
        """
        return {
            "general": {
                "output_dir": "processed_files",
                "remove_duplicate_lines": True,
                "remove_excessive_whitespace": True,
                "normalize_unicode": True
            },
            "html": {
                "remove_scripts": True,
                "remove_styles": True,
                "convert_tables": True
            },
            "pdf": {
                "merge_hyphenated_words": True
            }
        }
    
    def _apply_overrides(
        self, 
        config: Dict[str, Any], 
        overrides: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply overrides to a configuration.
        
        Args:
            config: Base configuration dictionary
            overrides: Overrides to apply
            
        Returns:
            The updated configuration
        """
        result = config.copy()
        
        # Handle flat keys like "general.remove_urls=true"
        flat_overrides = {}
        nested_overrides = {}
        
        for key, value in overrides.items():
            if isinstance(value, dict):
                nested_overrides[key] = value
            elif '.' in key:
                flat_overrides[key] = value
            else:
                # Top-level keys that aren't dictionaries
                result[key] = value
        
        # Apply nested overrides (merge dictionaries)
        for section, section_overrides in nested_overrides.items():
            if section not in result:
                result[section] = {}
                
            if isinstance(result[section], dict) and isinstance(section_overrides, dict):
                for key, value in section_overrides.items():
                    result[section][key] = value
            else:
                # If types don't match, just replace
                result[section] = section_overrides
        
        # Apply flat overrides
        for key, value in flat_overrides.items():
            parts = key.split('.')
            current = result
            
            # Navigate to the right level
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
                
            # Set the value
            current[parts[-1]] = value
            
        return result
