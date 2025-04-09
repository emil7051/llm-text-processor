"""Configuration presets for specific LLM models.

This module provides pre-defined configuration settings optimized for
different Large Language Models, token limits, and use cases.
"""

from typing import Dict, Any

# Define presets for different LLMs and use cases
LLM_PRESETS: Dict[str, Dict[str, Any]] = {
    # GPT-4 preset - balanced approach for 8K context
    "gpt4": {
        "token_limit": 8192,
        "optimize_for": "gpt4",
        "general": {
            "remove_duplicate_lines": True,
            "remove_urls": False,
            "trim_long_sentences": True,
            "max_sentence_length": 300,
            "preserve_code_blocks": True,
            "preserve_lists": True
        },
        "html": {
            "remove_scripts": True,
            "remove_styles": True,
            "remove_navigation": True,
            "convert_tables": True,
            "preserve_headings": True
        },
        "pdf": {
            "extract_images_text": False,
            "merge_hyphenated_words": True,
            "remove_headers_footers": True
        }
    },
    
    # Claude preset - optimized for long context
    "claude": {
        "token_limit": 100000,
        "optimize_for": "claude",
        "general": {
            "remove_duplicate_lines": True,
            "remove_urls": False,
            "trim_long_sentences": False,
            "preserve_code_blocks": True,
            "preserve_lists": True,
            "preserve_tables": True
        },
        "html": {
            "remove_scripts": True,
            "remove_styles": True,
            "remove_navigation": True,
            "convert_tables": False,  # Keep original table format
            "preserve_headings": True
        },
        "pdf": {
            "extract_images_text": True,
            "merge_hyphenated_words": True,
            "remove_headers_footers": True
        }
    },
    
    # Llama preset - optimized for 4K context
    "llama": {
        "token_limit": 4096,
        "optimize_for": "llama",
        "general": {
            "remove_duplicate_lines": True,
            "remove_urls": True,
            "trim_long_sentences": True,
            "max_sentence_length": 200,
            "preserve_code_blocks": True,
            "preserve_lists": True,
            "aggressive_whitespace": True
        },
        "html": {
            "remove_scripts": True,
            "remove_styles": True,
            "remove_navigation": True,
            "convert_tables": True,
            "simplify_structure": True
        },
        "pdf": {
            "extract_images_text": False,
            "merge_hyphenated_words": True,
            "remove_headers_footers": True,
            "aggressive_cleaning": True
        }
    },
    
    # ChatGPT preset - optimized for 4K context with better readability
    "chatgpt": {
        "token_limit": 4096,
        "optimize_for": "gpt3.5",
        "general": {
            "remove_duplicate_lines": True,
            "remove_urls": False,
            "trim_long_sentences": True,
            "max_sentence_length": 250,
            "preserve_code_blocks": True,
            "preserve_lists": True
        },
        "html": {
            "remove_scripts": True,
            "remove_styles": True,
            "remove_navigation": True,
            "convert_tables": True
        },
        "pdf": {
            "extract_images_text": False,
            "merge_hyphenated_words": True,
            "remove_headers_footers": True
        }
    },
    
    # RAG preset - optimized for vector database ingestion
    "rag": {
        "token_limit": 2048,
        "optimize_for": "embedding",
        "general": {
            "remove_duplicate_lines": True,
            "remove_urls": False,
            "trim_long_sentences": True,
            "max_sentence_length": 512,
            "preserve_code_blocks": True,
            "chunk_by_heading": True,
            "normalize_whitespace": True
        },
        "html": {
            "remove_scripts": True,
            "remove_styles": True,
            "remove_navigation": True,
            "extract_main_content": True
        },
        "pdf": {
            "extract_images_text": False,
            "merge_hyphenated_words": True,
            "remove_headers_footers": True,
            "extract_structured_data": True
        }
    },
    
    # Minimal preset - very light processing
    "minimal": {
        "token_limit": None,
        "optimize_for": "preservation",
        "general": {
            "remove_duplicate_lines": False,
            "remove_urls": False,
            "trim_long_sentences": False,
            "preserve_code_blocks": True,
            "preserve_lists": True,
            "preserve_tables": True,
            "normalize_whitespace": True
        },
        "html": {
            "remove_scripts": True,
            "remove_styles": True,
            "convert_tables": False
        },
        "pdf": {
            "extract_images_text": False,
            "merge_hyphenated_words": True,
            "remove_headers_footers": False
        }
    }
}


def get_preset(name: str) -> Dict[str, Any]:
    """Get a preset configuration by name.
    
    Args:
        name: Name of the preset
        
    Returns:
        Configuration dictionary
        
    Raises:
        ValueError: If preset name is not recognized
    """
    name = name.lower()
    if name not in LLM_PRESETS:
        raise ValueError(f"Unknown preset: {name}. Available presets: {', '.join(LLM_PRESETS.keys())}")
    
    return LLM_PRESETS[name]


def get_preset_names() -> list:
    """Get a list of available preset names.
    
    Returns:
        List of preset names
    """
    return list(LLM_PRESETS.keys())


def get_preset_description(name: str) -> str:
    """Get a human-readable description of a preset.
    
    Args:
        name: Name of the preset
        
    Returns:
        Description string
        
    Raises:
        ValueError: If preset name is not recognized
    """
    name = name.lower()
    if name not in LLM_PRESETS:
        raise ValueError(f"Unknown preset: {name}")
    
    preset = LLM_PRESETS[name]
    
    descriptions = {
        "gpt4": "Balanced approach for GPT-4 with 8K token context",
        "claude": "Optimized for Claude's long context window (100K tokens)",
        "llama": "Aggressive optimization for 4K context window models",
        "chatgpt": "Optimized for ChatGPT with 4K token context",
        "rag": "Designed for RAG/embedding vector database ingestion",
        "minimal": "Very light processing, preserves most content"
    }
    
    token_limit = preset.get("token_limit", "unlimited")
    token_text = f"{token_limit} tokens" if token_limit else "unlimited tokens"
    
    return f"{descriptions.get(name, 'Custom preset')}, targeting {token_text}" 