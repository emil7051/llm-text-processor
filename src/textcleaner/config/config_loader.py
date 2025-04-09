import yaml
import logging
from typing import Dict, Any, Set, Tuple, List
from pathlib import Path

from textcleaner.processors import BaseProcessor, ContentCleaner, OCRProcessor

logger = logging.getLogger(__name__)

# Default configuration template path
DEFAULT_CONFIG_PATH = Path(__file__).parent / 'templates' / 'standard.yaml'

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Config file not found at {config_path}. Using default config.")
        path = DEFAULT_CONFIG_PATH
        if not path.exists():
            raise ConfigError(f"Default config file not found at {DEFAULT_CONFIG_PATH}")
            
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded configuration from: {path}")
        return config if config else {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing YAML config file {path}: {e}")
    except Exception as e:
        raise ConfigError(f"Error loading config file {path}: {e}")

def validate_config_keys(processor_name: str, config_section: Dict[str, Any], valid_keys: Set[str]):
    """Validate that only expected keys are present in a config section."""
    extra_keys = set(config_section.keys()) - valid_keys
    if extra_keys:
        logger.warning(f"Ignoring unexpected keys in {processor_name} config: {', '.join(extra_keys)}")
        # Optionally, raise an error instead:
        # raise ConfigError(f"Unexpected keys in {processor_name} config: {', '.join(extra_keys)}")

def load_processor_config(config_dict: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load and validate the processor configuration from a dictionary."""
    content_cleaner_config = config_dict.get('content_cleaner', {})
    validate_config_keys('ContentCleaner', content_cleaner_config,
                         {'remove_headers_footers', 'remove_page_numbers',
                          'remove_watermarks', 'clean_whitespace',
                          'normalize_unicode', 'remove_boilerplate',
                          'remove_duplicate_content', 'remove_irrelevant_metadata',
                          'merge_short_paragraphs', 'remove_footnotes',
                          'join_paragraph_lines'})
    
    ocr_processor_config = config_dict.get('ocr_processor', {})
    validate_config_keys('OCRProcessor', ocr_processor_config,
                         {'language', 'dpi', 'extract_images'})
    
    return content_cleaner_config, ocr_processor_config

def load_processors(config: Dict[str, Any]) -> List[BaseProcessor]:
    """Load and instantiate processors based on the configuration."""
    processors = []
    content_cleaner_config, ocr_processor_config = load_processor_config(config)
    
    # Instantiate ContentCleaner with all expected arguments from config
    processors.append(ContentCleaner(
        remove_headers_footers=content_cleaner_config.get('remove_headers_footers', False),
        remove_page_numbers=content_cleaner_config.get('remove_page_numbers', False),
        remove_watermarks=content_cleaner_config.get('remove_watermarks', False),
        clean_whitespace=content_cleaner_config.get('clean_whitespace', True),
        normalize_unicode=content_cleaner_config.get('normalize_unicode', True),
        remove_boilerplate=content_cleaner_config.get('remove_boilerplate', True),
        remove_duplicate_content=content_cleaner_config.get('remove_duplicate_content', True),
        remove_irrelevant_metadata=content_cleaner_config.get('remove_irrelevant_metadata', False),
        merge_short_paragraphs=content_cleaner_config.get('merge_short_paragraphs', False),
        remove_footnotes=content_cleaner_config.get('remove_footnotes', True),
        join_paragraph_lines=content_cleaner_config.get('join_paragraph_lines', True)
    ))
    
    # Instantiate OCRProcessor if needed 
    # Example check: Instantiate if 'language' is specified or if OCR section exists
    # Modify this logic based on how you determine if OCR is needed
    if ocr_processor_config and ocr_processor_config.get('language'): 
        processors.append(OCRProcessor(
            language=ocr_processor_config.get('language', 'eng'), # Default language if needed
            dpi=ocr_processor_config.get('dpi', 300),
            extract_images=ocr_processor_config.get('extract_images', False) 
        ))
        logger.info(f"OCR Processor loaded with language: {ocr_processor_config.get('language')}")
    elif ocr_processor_config:
        logger.info("OCR Processor config section found but no language specified; OCR processor not loaded.")

    if not processors:
        raise ConfigError("No processors were loaded. Check configuration.")
        
    logger.info(f"Loaded {len(processors)} processors.")
    return processors 