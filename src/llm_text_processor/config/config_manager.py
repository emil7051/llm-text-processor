"""Configuration management for the text processor."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union


class ConfigManager:
    """Manages configuration for the LLM text processor.
    
    Handles loading configuration from files, merging with defaults,
    and providing access to configuration settings.
    """
    
    def __init__(
        self, 
        config_path: Optional[str] = None, 
        overrides: Optional[Dict[str, Any]] = None
    ):
        """Initialize the configuration manager.
        
        Args:
            config_path: Optional path to a YAML configuration file.
            overrides: Optional dictionary of configuration overrides.
        """
        self.config = self._load_default_config()
        
        if config_path:
            user_config = self._load_from_file(config_path)
            self._merge_config(user_config)
            
        if overrides:
            self._merge_config(overrides)
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load the default configuration."""
        default_path = Path(__file__).parent / "default_config.yaml"
        return self._load_from_file(default_path)
    
    def _load_from_file(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from a YAML file.
        
        Args:
            path: Path to the configuration file.
            
        Returns:
            Dict containing the configuration.
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            yaml.YAMLError: If the configuration file is invalid.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _merge_config(self, config: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries.
        
        Args:
            config: Configuration to merge into the current configuration.
        """
        self._merge_dicts(self.config, config)
    
    def _merge_dicts(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge two dictionaries.
        
        Args:
            base: Base dictionary to merge into.
            override: Dictionary with values to override in the base.
        """
        for key, value in override.items():
            if (
                key in base and 
                isinstance(base[key], dict) and 
                isinstance(value, dict)
            ):
                self._merge_dicts(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.
        
        Keys can be nested using dot notation (e.g., 'processing.cleaning_level').
        
        Args:
            key: Configuration key to retrieve.
            default: Default value to return if the key doesn't exist.
            
        Returns:
            The configuration value, or the default if not found.
        """
        parts = key.split('.')
        current = self.config
        
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
            
        return current
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section.
        
        Args:
            section: Section name to retrieve.
            
        Returns:
            Dictionary containing the section configuration.
            Empty dict if the section doesn't exist.
        """
        return self.get(section, {})
    
    def save_to_file(self, path: str) -> None:
        """Save the current configuration to a file.
        
        Args:
            path: Path to save the configuration to.
            
        Raises:
            IOError: If the file cannot be written.
        """
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def __str__(self) -> str:
        """Return a string representation of the configuration."""
        return yaml.dump(self.config, default_flow_style=False)
