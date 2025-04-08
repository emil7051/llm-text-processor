"""Configuration factory for the LLM Text Processor."""

from pathlib import Path
from typing import Dict, Optional, Any

from textcleaner.config.config_manager import ConfigManager
from textcleaner.utils.logging_config import get_logger


class ConfigFactory:
    """Factory for creating and customizing configurations."""

    def __init__(self):
        """Initialize the configuration factory."""
        self.logger = get_logger(__name__)
        self._default_configs = {
            "minimal": self._create_minimal_config,
            "standard": self._create_standard_config,
            "aggressive": self._create_aggressive_config,
        }
    
    def create_config(self, 
                     config_path: Optional[str] = None, 
                     config_type: str = "standard") -> ConfigManager:
        """Create a configuration manager.
        
        Args:
            config_path: Optional path to a configuration file
            config_type: Type of default configuration if no file is provided
            
        Returns:
            Initialized ConfigManager
        """
        # Create config manager
        if config_path:
            # Load from file
            self.logger.info(f"Loading configuration from {config_path}")
            config = ConfigManager(config_file=config_path)
        else:
            # Create default config based on specified type
            self.logger.info(f"Creating {config_type} configuration")
            config = ConfigManager()
            
            if config_type in self._default_configs:
                self._default_configs[config_type](config)
            else:
                self.logger.warning(f"Unknown config type '{config_type}', using standard")
                self._create_standard_config(config)
        
        return config
    
    def _create_minimal_config(self, config: ConfigManager) -> None:
        """Create a minimal configuration with light processing.
        
        Args:
            config: Configuration manager to customize
        """
        # Minimal cleaning preserves most structure
        config.config["processing"]["cleaning_level"] = "minimal"
        
        config.config["structure"]["preserve_headings"] = True
        config.config["structure"]["preserve_lists"] = True
        config.config["structure"]["preserve_tables"] = True
        config.config["structure"]["preserve_links"] = True
        
        config.config["cleaning"]["remove_headers_footers"] = False
        config.config["cleaning"]["remove_watermarks"] = False
        config.config["cleaning"]["clean_whitespace"] = True
        
        config.config["optimization"]["abbreviate_common_terms"] = False
        config.config["optimization"]["simplify_citations"] = False
        config.config["optimization"]["simplify_references"] = False
        
        self.logger.info("Created minimal configuration")
    
    def _create_standard_config(self, config: ConfigManager) -> None:
        """Create a standard configuration with balanced processing.
        
        Args:
            config: Configuration manager to customize
        """
        # Standard cleaning balances structure and efficiency
        config.config["processing"]["cleaning_level"] = "standard"
        
        config.config["structure"]["preserve_headings"] = True
        config.config["structure"]["preserve_lists"] = True
        config.config["structure"]["preserve_tables"] = True
        config.config["structure"]["preserve_links"] = False
        
        config.config["cleaning"]["remove_headers_footers"] = True
        config.config["cleaning"]["remove_watermarks"] = True
        config.config["cleaning"]["clean_whitespace"] = True
        
        config.config["optimization"]["abbreviate_common_terms"] = False
        config.config["optimization"]["simplify_citations"] = True
        config.config["optimization"]["simplify_references"] = True
        
        self.logger.info("Created standard configuration")
    
    def _create_aggressive_config(self, config: ConfigManager) -> None:
        """Create an aggressive configuration with maximum optimization.
        
        Args:
            config: Configuration manager to customize
        """
        # Aggressive cleaning maximizes token efficiency
        config.config["processing"]["cleaning_level"] = "aggressive"
        
        config.config["structure"]["preserve_headings"] = True
        config.config["structure"]["preserve_lists"] = True
        config.config["structure"]["preserve_tables"] = False
        config.config["structure"]["preserve_links"] = False
        
        config.config["cleaning"]["remove_headers_footers"] = True
        config.config["cleaning"]["remove_watermarks"] = True
        config.config["cleaning"]["remove_boilerplate"] = True
        config.config["cleaning"]["remove_duplicate_content"] = True
        
        config.config["optimization"]["abbreviate_common_terms"] = True
        config.config["optimization"]["simplify_citations"] = True
        config.config["optimization"]["simplify_references"] = True
        config.config["optimization"]["simplify_urls"] = True
        
        self.logger.info("Created aggressive configuration")
    
    def create_custom_config(self, 
                           base_type: str = "standard", 
                           overrides: Dict[str, Any] = None) -> ConfigManager:
        """Create a custom configuration with specific overrides.
        
        Args:
            base_type: Base configuration type to start with
            overrides: Dictionary of custom configuration overrides
            
        Returns:
            Customized ConfigManager
        """
        # Start with a default config
        config = self.create_config(config_type=base_type)
        
        # Apply overrides if provided
        if overrides:
            self.logger.info(f"Applying custom overrides to {base_type} configuration")
            self._apply_overrides(config, overrides)
        
        return config
    
    def _apply_overrides(self, 
                        config: ConfigManager, 
                        overrides: Dict[str, Any]) -> None:
        """Apply configuration overrides.
        
        Args:
            config: Configuration manager to customize
            overrides: Dictionary of overrides to apply
        """
        for key, value in overrides.items():
            if "." in key:
                # Handle nested keys (e.g., "cleaning.remove_watermarks")
                section, option = key.split(".", 1)
                if section in config.config:
                    config.config[section][option] = value
                    self.logger.debug(f"Applied override: {section}.{option} = {value}")
            else:
                # Handle top-level keys
                config.config[key] = value
                self.logger.debug(f"Applied override: {key} = {value}")
    
    def save_config(self, 
                   config: ConfigManager, 
                   output_path: str) -> None:
        """Save a configuration to file.
        
        Args:
            config: Configuration manager to save
            output_path: Path where the configuration should be saved
        """
        self.logger.info(f"Saving configuration to {output_path}")
        config.save_to_file(output_path)
        self.logger.info(f"Configuration saved to {output_path}")
