"""Factory classes for creating TextCleaner processors and components."""

from typing import Dict, Any, Optional

from textcleaner.core.processor import TextProcessor
from textcleaner.core.file_registry import FileTypeRegistry
from textcleaner.config.config_factory import ConfigFactory
from textcleaner.converters.base import ConverterRegistry
from textcleaner.processors.processor_pipeline import ProcessorPipeline
from textcleaner.outputs.output_manager import OutputManager
from textcleaner.utils.logging_config import get_logger
from textcleaner.utils.security import SecurityUtils
from textcleaner.utils.parallel import ParallelProcessor
from textcleaner.core.directory_processor import DirectoryProcessor
from textcleaner.config.config_manager import ConfigManager


class TextProcessorFactory:
    """Factory for creating TextProcessor instances with appropriate configuration."""
    
    def __init__(self):
        """Initialize the factory."""
        self.logger = get_logger(__name__)
        self.config_factory = ConfigFactory()
        self._security_utils_instance: Optional[SecurityUtils] = None
    
    def _get_security_utils(self) -> SecurityUtils:
        """Return a cached instance of SecurityUtils."""
        if self._security_utils_instance is None:
            self._security_utils_instance = SecurityUtils()
        return self._security_utils_instance

    def create_processor(
        self,
        config_path: Optional[str] = None,
        config_type: str = "standard",
        custom_overrides: Optional[Dict[str, Any]] = None
    ) -> TextProcessor:
        """Create a TextProcessor with the specified configuration.
        
        Args:
            config_path: Optional path to a configuration file
            config_type: Type of configuration to use if no file is provided
            custom_overrides: Optional dictionary of configuration overrides
            
        Returns:
            Configured TextProcessor instance
        """
        self.logger.info(f"Creating TextProcessor with {'custom' if config_path else config_type} configuration")
        
        # Create configuration using factory
        config = self.config_factory.create_processor_config(
            config_path=config_path,
            config_type=config_type,
            custom_overrides=custom_overrides
        )
        
        # Create ConfigManager instance, passing the pre-loaded and merged config
        config_manager = ConfigManager(initial_config=config)
        # config_manager.config = config # Removed direct assignment

        # Create registries
        file_registry = FileTypeRegistry()
        
        # Create converter registry and populate it, passing ConfigManager
        converter_registry = ConverterRegistry(config=config_manager)
        converter_registry.populate_registry()
        
        # Create processor pipeline, passing ConfigManager
        processor_pipeline = ProcessorPipeline(config_manager)
        
        # Create output manager, passing ConfigManager
        output_manager = OutputManager(config_manager)
        
        # Create security and parallel processing utilities
        security_utils = self._get_security_utils()
        
        # Create and return text processor with all components injected
        return TextProcessor(
            config=config_manager, # Pass ConfigManager instance
            converter_registry=converter_registry,
            processor_pipeline=processor_pipeline,
            file_registry=file_registry,
            output_manager=output_manager,
            security_utils=security_utils,
        )
    
    def create_processor_from_preset(
        self,
        preset_name: str,
        additional_overrides: Optional[Dict[str, Any]] = None
    ) -> TextProcessor:
        """Create a TextProcessor using a predefined LLM preset.
        
        Args:
            preset_name: Name of the LLM preset to use
            additional_overrides: Additional configuration overrides
            
        Returns:
            Configured TextProcessor instance
        """
        self.logger.info(f"Creating TextProcessor with {preset_name} preset")
        
        # Combine preset with any additional overrides
        custom_overrides = {}
        if additional_overrides:
            custom_overrides.update(additional_overrides)
            
        # Create configuration using preset as the config_type
        return self.create_processor(
            config_type=preset_name,
            custom_overrides=custom_overrides
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

    def create_parallel_processor(
        self,
        max_workers: Optional[int] = None
    ) -> ParallelProcessor:
        """Create a ParallelProcessor instance.

        Args:
            max_workers: Maximum number of worker processes.

        Returns:
            Configured ParallelProcessor instance.
        """
        # Configuration for max_workers could potentially come from ConfigManager in the future
        return ParallelProcessor(max_workers=max_workers)

    def create_directory_processor(
        self,
        config_manager: ConfigManager,
        single_file_processor: TextProcessor,
        parallel_processor: ParallelProcessor
    ) -> DirectoryProcessor:
        """Create a DirectoryProcessor instance.

        Args:
            config_manager: The configuration manager.
            single_file_processor: The processor for individual files.
            parallel_processor: The parallel processor instance.

        Returns:
            Configured DirectoryProcessor instance.
        """
        security_utils = self._get_security_utils() # Reuse cached security instance
        return DirectoryProcessor(
            config=config_manager,
            security_utils=security_utils,
            parallel_processor=parallel_processor,
            single_file_processor=single_file_processor
        )
