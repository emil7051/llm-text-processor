"""
Unit tests for TextCleaner presets functionality.
"""

import pytest
from pathlib import Path

from textcleaner.config.presets import get_preset_names, get_preset_description, get_preset
from textcleaner.core.factories import TextProcessorFactory
from textcleaner.utils.performance import calculate_token_estimate


def test_presets_list():
    """Test that presets can be listed."""
    preset_names = get_preset_names()
    assert isinstance(preset_names, list), "Preset names should be a list"
    assert len(preset_names) > 0, "There should be at least one preset defined"


def test_preset_structure():
    """Test that all presets have proper structure."""
    preset_names = get_preset_names()
    
    for name in preset_names:
        preset = get_preset(name)
        desc = get_preset_description(name)
        
        # Basic structure
        assert isinstance(preset, dict), f"Preset {name} should be a dictionary"
        assert isinstance(desc, str), f"Description for {name} should be a string"
        assert len(desc) > 0, f"Description for {name} should not be empty"
        
        # Required keys
        assert "optimize_for" in preset, f"Preset {name} should have 'optimize_for' key"
        
        # Optional but common keys
        if "token_limit" in preset:
            assert isinstance(preset["token_limit"], (int, type(None))), f"token_limit should be int or None"
        
        # Verify key sections exist with proper type
        sections = ["general", "html", "pdf", "docx", "text"]
        for section in sections:
            if section in preset:
                assert isinstance(preset[section], dict), f"Section '{section}' should be a dictionary"


def test_factory_with_presets():
    """Test that the TextProcessorFactory correctly uses presets."""
    factory = TextProcessorFactory()
    
    for name in get_preset_names():
        processor = factory.create_processor_from_preset(name)
        assert processor is not None, f"Processor for preset {name} should not be None"
        
        # Verify that the preset was applied to the configuration
        optimize_for = processor.config.get("optimize_for")
        assert optimize_for is not None, f"Preset {name} should set 'optimize_for'"


def test_token_counting():
    """Test token counting utilities."""
    # Test basic token counting
    test_text = "This is a short test sentence."
    tokens = calculate_token_estimate(test_text)
    assert tokens > 0, "Token count should be positive"
    assert tokens < len(test_text), "Token count should be less than character count"
    
    # Test with different models
    tokens_gpt = calculate_token_estimate(test_text, model="gpt-3.5")
    tokens_claude = calculate_token_estimate(test_text, model="claude")
    # Models might have different token counts but should be in a reasonable range
    assert tokens_gpt > 0, "GPT token count should be positive"
    assert tokens_claude > 0, "Claude token count should be positive"
    
    # Test longer text scales properly
    long_text = "This is a much longer test text that should have significantly more tokens than the previous example. " * 10
    long_tokens = calculate_token_estimate(long_text)
    assert long_tokens > tokens, "Longer text should have more tokens"
    
    # Test that token count scales approximately with text length
    ratio = long_tokens / tokens
    text_ratio = len(long_text) / len(test_text)
    assert 0.5 * text_ratio < ratio < 1.5 * text_ratio, "Token count should scale approximately with text length"


def test_token_counting_cache():
    """Test that token counting cache is working."""
    test_text = "This is a text for testing the token counting cache."
    
    # First call should calculate
    tokens1 = calculate_token_estimate(test_text)
    
    # Patch the function temporarily to verify cache is used
    import time
    
    # Store original implementation
    original_func = calculate_token_estimate.__wrapped__
    
    # Replace with version that would fail if called
    def patched_func(*args, **kwargs):
        assert False, "This should not be called if cache is working"
    
    calculate_token_estimate.__wrapped__ = patched_func
    
    try:
        # This should use cache and not call the patched function
        tokens2 = calculate_token_estimate(test_text)
        assert tokens1 == tokens2, "Cached token count should match original"
    finally:
        # Restore original implementation
        calculate_token_estimate.__wrapped__ = original_func 