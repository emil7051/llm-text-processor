"""Factory classes for creating text processor components."""

from typing import Optional, Dict, Any

from textcleaner.core.processor import TextProcessor
from textcleaner.core.file_registry import FileTypeRegistry
from textcleaner.config.config_factory import ConfigFactory
from textcleaner.converters.base import ConverterRegistry
from textcleaner.processors.processor_pipeline import ProcessorPipeline
from textcleaner.outputs.output_manager import OutputManager
from textcleaner.utils.logging_config import get_logger


class TextProcessorFactory:
    """Factory for creating TextProcessor instances with different configurations."""
    
    def __init__(self):
        """Initialize the text processor factory."""
        self.logger = get_logger(__name__)
        self.config_factory = ConfigFactory()
    
    def create_processor(self, 
                       config_path: Optional[str] = None,
                       config_type: str = "standard",
                       config_overrides: Optional[Dict[str, Any]] = None) -> TextProcessor:
        """Create a text processor with the specified configuration.
        
        Args:
            config_path: Optional path to a configuration file
            config_type: Type of default configuration if no file is provided
            config_overrides: Optional dictionary of configuration overrides
            
        Returns:
            Initialized TextProcessor
        """
        # Create configuration
        if config_overrides:
            config = self.config_factory.create_custom_config(config_type, config_overrides)
            self.logger.info(f"Created custom {config_type} configuration with overrides")
        else:
            config = self.config_factory.create_config(config_path, config_type)
            
        # Create registries
        file_registry = FileTypeRegistry()
        
        # Create converter registry
        from textcleaner.converters import register_converters
        converter_registry = register_converters()
        converter_registry.set_config(config)
        
        # Create processor pipeline
        processor_pipeline = ProcessorPipeline(config)
        
        # Create output manager
        output_manager = OutputManager(config)
        
        # Create and return text processor with all components injected
        return TextProcessor(
            config_path=config_path,
            config_type=config_type,
            converter_registry=converter_registry,
            processor_pipeline=processor_pipeline,
            file_registry=file_registry,
            output_manager=output_manager
        )
    
    def create_minimal_processor(self) -> TextProcessor:
        """Create a text processor with minimal processing configuration.
        
        Returns:
            TextProcessor with minimal processing configuration
        """
        return self.create_processor(config_type="minimal")
    
    def create_standard_processor(self) -> TextProcessor:
        """Create a text processor with standard processing configuration.
        
        Returns:
            TextProcessor with standard processing configuration
        """
        return self.create_processor(config_type="standard")
    
    def create_aggressive_processor(self) -> TextProcessor:
        """Create a text processor with aggressive processing configuration.
        
        Returns:
            TextProcessor with aggressive processing configuration
        """
        return self.create_processor(config_type="aggressive")
