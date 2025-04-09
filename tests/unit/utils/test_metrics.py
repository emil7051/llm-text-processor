import pytest
from unittest.mock import patch, MagicMock

from textcleaner.config import ConfigManager
from textcleaner.utils.metrics import (
    _estimate_token_count_fallback,
    get_tokenizer,
    count_tokens,
    calculate_metrics,
    generate_metrics_report,
    _tiktoken_available, # Import for patching tests
    _tokenizer_cache # Import the cache for testing
)

# Mock the logger used in metrics.py
@pytest.fixture(autouse=True)
def mock_metrics_logger():
    """Fixture to mock the logger used within the metrics module."""
    # Correctly patch the logger instance used within metrics.py
    with patch('textcleaner.utils.metrics.logger') as mock_log:
        yield mock_log

# Mock ConfigManager for tests needing configuration
@pytest.fixture
def mock_config():
    config = MagicMock() # Removed spec=ConfigManager
    # Default setup for tokenizer encoding, can be overridden in tests
    config.get.return_value = "cl100k_base"
    return config

# --- Tests for _estimate_token_count_fallback ---

@pytest.mark.parametrize("text, expected_count", [
    ("", 0),
    ("Hello world", 2),
    ("One two three.", 4), # Word + punctuation
    ("Split words, count punctuation! Right?", 8), # Multiple punctuations
    ("   Leading and trailing spaces   ", 4),
    ("\nNewlines\n and tabs\t", 3)
])
def test_estimate_token_count_fallback(text, expected_count):
    """Test the fallback token estimation logic."""
    assert _estimate_token_count_fallback(text) == expected_count

# --- Placeholder for get_tokenizer Tests ---
# TODO: Add tests
# --- Tests for get_tokenizer ---

# Mock tiktoken globally for relevant tests
@pytest.fixture(autouse=True)
def mock_tiktoken_globally():
    # Clear the cache before each test using this fixture
    from textcleaner.utils.metrics import _tokenizer_cache
    _tokenizer_cache.clear()

    mock_tiktoken_module = MagicMock()
    mock_tokenizer_instance = MagicMock()
    mock_tokenizer_instance.encode.return_value = [1, 2, 3] # Dummy encode result

    # Default behavior: get_encoding succeeds
    mock_tiktoken_module.get_encoding.return_value = mock_tokenizer_instance

    with patch.dict('sys.modules', {'tiktoken': mock_tiktoken_module}):
        yield mock_tiktoken_module, mock_tokenizer_instance

    # Clear cache after test
    _tokenizer_cache.clear()

@patch('textcleaner.utils.metrics._tiktoken_available', True)
@patch('textcleaner.utils.metrics.tiktoken.get_encoding')
def test_get_tokenizer_success_and_cache(mock_get_encoding, mock_metrics_logger):
    """Test successful loading and caching of a tokenizer."""
    mock_tokenizer_instance = MagicMock(name="mock_tokenizer")
    mock_get_encoding.return_value = mock_tokenizer_instance
    encoding = "cl100k_base"

    # First call - should load
    tokenizer1 = get_tokenizer(encoding)
    assert tokenizer1 is mock_tokenizer_instance
    mock_get_encoding.assert_called_once_with(encoding)
    mock_metrics_logger.info.assert_called_once()
    assert encoding in _tokenizer_cache # Check cache population
    assert _tokenizer_cache[encoding] is mock_tokenizer_instance

    # Second call - should use cache
    mock_get_encoding.reset_mock()
    mock_metrics_logger.reset_mock()
    tokenizer2 = get_tokenizer(encoding)
    assert tokenizer2 is mock_tokenizer_instance
    mock_get_encoding.assert_not_called() # Should not call get_encoding again
    mock_metrics_logger.info.assert_not_called() # Should not log loading again

@patch('textcleaner.utils.metrics._tiktoken_available', True)
@patch('textcleaner.utils.metrics.tiktoken.get_encoding')
def test_get_tokenizer_load_failure(mock_get_encoding, mock_metrics_logger):
    """Test handling when tiktoken fails to load a specific encoding."""
    # mock_tiktoken_module, _ = mock_tiktoken_globally # No longer needed
    encoding = "invalid-encoding"
    error_message = "Encoding not found"
    # Set side effect directly on the patched get_encoding function
    mock_get_encoding.side_effect = ValueError(error_message) 

    # Clear cache specifically for this test encoding to ensure get_encoding is called
    from textcleaner.utils.metrics import _tokenizer_cache
    if encoding in _tokenizer_cache:
        del _tokenizer_cache[encoding]

    tokenizer = get_tokenizer(encoding)

    assert tokenizer is None
    # Assert the patched get_encoding was called
    mock_get_encoding.assert_called_once_with(encoding) 
    mock_metrics_logger.error.assert_called_once_with(
        f"Failed to load tiktoken tokenizer '{encoding}': {error_message}. Falling back to estimation."
    )

    # Check cache shows failure
    assert encoding in _tokenizer_cache
    assert _tokenizer_cache[encoding] is None

    # Verify subsequent calls also return None without trying to load again
    mock_get_encoding.reset_mock() # Reset the direct patch mock
    tokenizer_again = get_tokenizer(encoding)
    assert tokenizer_again is None
    mock_get_encoding.assert_not_called() # Assert the direct patch mock was not called again

@patch('textcleaner.utils.metrics._tiktoken_available', False)
def test_get_tokenizer_tiktoken_not_available(mock_metrics_logger):
    """Test get_tokenizer returns None immediately if tiktoken is not available."""
    # No need for mock_tiktoken_globally as it shouldn't be called
    with patch.dict('sys.modules', {'tiktoken': None}): # Ensure tiktoken isn't mock-imported
        tokenizer = get_tokenizer("any-encoding")
        assert tokenizer is None

    # Logger shouldn't be called either in this case
    mock_metrics_logger.info.assert_not_called()
    mock_metrics_logger.error.assert_not_called()

# --- Placeholder for count_tokens Tests ---
# TODO: Add tests
# --- Tests for count_tokens ---

@patch('textcleaner.utils.metrics.get_tokenizer')
def test_count_tokens_uses_tiktoken_when_available(mock_get_tokenizer, mock_config):
    """Test count_tokens uses tiktoken tokenizer if successfully loaded."""
    mock_tokenizer = MagicMock()
    mock_tokenizer.encode.return_value = [10, 20, 30, 40] # Simulate 4 tokens
    mock_get_tokenizer.return_value = mock_tokenizer
    text = "This text will be tokenized."

    token_count = count_tokens(text, mock_config)

    mock_config.get.assert_called_once_with("metrics.tokenizer_encoding", "cl100k_base")
    mock_get_tokenizer.assert_called_once_with("cl100k_base")
    mock_tokenizer.encode.assert_called_once_with(text)
    assert token_count == 4

@patch('textcleaner.utils.metrics.get_tokenizer', return_value=None) # Simulate tokenizer unavailable/failed
@patch('textcleaner.utils.metrics._estimate_token_count_fallback')
def test_count_tokens_uses_fallback_when_tokenizer_none(mock_fallback, mock_get_tokenizer, mock_config):
    """Test count_tokens uses fallback if get_tokenizer returns None."""
    mock_fallback.return_value = 5 # Simulate fallback result
    text = "Some input text."

    token_count = count_tokens(text, mock_config)

    mock_config.get.assert_called_once_with("metrics.tokenizer_encoding", "cl100k_base")
    mock_get_tokenizer.assert_called_once_with("cl100k_base")
    mock_fallback.assert_called_once_with(text)
    assert token_count == 5

@patch('textcleaner.utils.metrics.get_tokenizer')
@patch('textcleaner.utils.metrics._estimate_token_count_fallback')
def test_count_tokens_uses_fallback_on_encode_error(mock_fallback, mock_get_tokenizer, mock_config, mock_metrics_logger):
    """Test count_tokens uses fallback if tokenizer.encode() raises error."""
    mock_tokenizer = MagicMock()
    error_message = "Encoding error"
    mock_tokenizer.encode.side_effect = Exception(error_message)
    mock_get_tokenizer.return_value = mock_tokenizer
    mock_fallback.return_value = 6
    text = "Text causing issues."

    token_count = count_tokens(text, mock_config)

    mock_config.get.assert_called_once_with("metrics.tokenizer_encoding", "cl100k_base")
    mock_get_tokenizer.assert_called_once_with("cl100k_base")
    mock_tokenizer.encode.assert_called_once_with(text)
    mock_metrics_logger.warning.assert_called_once_with(
        f"Tiktoken encoding failed for text snippet (falling back to estimation): {error_message}"
    )
    mock_fallback.assert_called_once_with(text)
    assert token_count == 6

def test_count_tokens_empty_text(mock_config):
    """Test count_tokens returns 0 for empty text without calling tokenizer."""
    with patch('textcleaner.utils.metrics.get_tokenizer') as mock_get_tokenizer:
        token_count = count_tokens("", mock_config)
        assert token_count == 0
        mock_config.get.assert_not_called() # Shouldn't need config for empty text
        mock_get_tokenizer.assert_not_called()

@patch('textcleaner.utils.metrics.get_tokenizer')
def test_count_tokens_uses_config_encoding(mock_get_tokenizer, mock_config):
    """Test count_tokens uses the encoding specified in the config."""
    mock_tokenizer = MagicMock()
    mock_tokenizer.encode.return_value = [1, 2]
    mock_get_tokenizer.return_value = mock_tokenizer
    text = "Text."
    custom_encoding = "p50k_base"
    # Configure mock_config to return the custom encoding
    mock_config.get.side_effect = lambda key, default=None: custom_encoding if key == "metrics.tokenizer_encoding" else default

    count_tokens(text, mock_config)

    mock_config.get.assert_called_once_with("metrics.tokenizer_encoding", "cl100k_base")
    mock_get_tokenizer.assert_called_once_with(custom_encoding)
    mock_tokenizer.encode.assert_called_once_with(text)

# --- Placeholder for calculate_metrics Tests ---
# TODO: Add tests
# --- Tests for calculate_metrics ---

@patch('textcleaner.utils.metrics.count_tokens')
@patch('textcleaner.utils.metrics.get_tokenizer', return_value=True) # Simulate tokenizer available
def test_calculate_metrics_basic_tiktoken(mock_get_tokenizer, mock_count_tokens, mock_config):
    """Test basic metrics calculation when tiktoken is available."""
    raw_text = "This is the original long text."
    processed_text = "This is shorter."
    processing_time = 0.5
    mock_count_tokens.side_effect = [10, 5] # Original tokens, processed tokens
    input_stats = {"file_size_kb": 2.0}

    metrics = calculate_metrics(raw_text, processed_text, processing_time, mock_config, input_stats)

    assert metrics["processing_time_seconds"] == 0.5
    assert metrics["original_text_length"] == 31
    assert metrics["processed_text_length"] == 16
    assert metrics["text_length_reduction_percent"] == 48.39
    assert metrics["original_tokens"] == 10
    assert metrics["processed_tokens"] == 5
    assert metrics["token_reduction_percent"] == 50.0
    assert metrics["processing_speed_kb_per_second"] == 4.0
    assert metrics["processing_speed_chars_per_second"] == pytest.approx(31 / 0.5)
    assert metrics["input_file_stats"] == input_stats
    # Check keys don't have _estimate suffix
    assert "original_tokens_estimate" not in metrics
    assert "processed_tokens_estimate" not in metrics
    assert "token_reduction_percent_estimate" not in metrics

    mock_count_tokens.assert_any_call(raw_text, mock_config)
    mock_count_tokens.assert_any_call(processed_text, mock_config)
    assert mock_count_tokens.call_count == 2
    mock_get_tokenizer.assert_called_once_with("cl100k_base") # Checked for key suffix

@patch('textcleaner.utils.metrics.count_tokens')
@patch('textcleaner.utils.metrics.get_tokenizer', return_value=None) # Simulate tokenizer NOT available
def test_calculate_metrics_basic_fallback(mock_get_tokenizer, mock_count_tokens, mock_config):
    """Test basic metrics calculation using fallback estimation."""
    raw_text = "Original text, estimate tokens."
    processed_text = "Processed text."
    processing_time = 0.2
    mock_count_tokens.side_effect = [6, 3] # Estimated tokens

    metrics = calculate_metrics(raw_text, processed_text, processing_time, mock_config)

    assert metrics["processing_time_seconds"] == 0.2
    assert metrics["original_text_length"] == 31
    assert metrics["processed_text_length"] == 15
    assert metrics["text_length_reduction_percent"] == 51.61
    assert metrics["original_tokens_estimate"] == 6
    assert metrics["processed_tokens_estimate"] == 3
    assert metrics["token_reduction_percent_estimate"] == 50.0
    assert "processing_speed_kb_per_second" not in metrics # No file stats provided
    assert metrics["processing_speed_chars_per_second"] == pytest.approx(31 / 0.2)
    assert "input_file_stats" not in metrics
    # Check keys HAVE _estimate suffix
    assert "original_tokens" not in metrics
    assert "processed_tokens" not in metrics
    assert "token_reduction_percent" not in metrics

    mock_count_tokens.assert_any_call(raw_text, mock_config)
    mock_count_tokens.assert_any_call(processed_text, mock_config)
    assert mock_count_tokens.call_count == 2
    mock_get_tokenizer.assert_called_once_with("cl100k_base") # Checked for key suffix

@patch('textcleaner.utils.metrics.count_tokens', return_value=0)
def test_calculate_metrics_empty_input(mock_count_tokens, mock_config):
    """Test metrics calculation with empty raw text."""
    raw_text = ""
    processed_text = ""
    processing_time = 0.1

    metrics = calculate_metrics(raw_text, processed_text, processing_time, mock_config)

    assert metrics["original_text_length"] == 0
    assert metrics["processed_text_length"] == 0
    assert metrics["text_length_reduction_percent"] == 0
    # Token keys depend on tokenizer availability, assume fallback for simplicity
    assert metrics.get("original_tokens_estimate", 0) == 0
    assert metrics.get("processed_tokens_estimate", 0) == 0
    assert metrics.get("token_reduction_percent_estimate", 0) == 0
    assert "processing_speed_kb_per_second" not in metrics
    assert metrics["processing_speed_chars_per_second"] == 0 # len(raw_text) / time

    # count_tokens should still be called, returning 0
    assert mock_count_tokens.call_count == 2

@patch('textcleaner.utils.metrics.count_tokens', return_value=10)
def test_calculate_metrics_zero_time(mock_count_tokens, mock_config):
    """Test metrics calculation with zero processing time."""
    raw_text = "Some text"
    processed_text = "Less text"
    processing_time = 0.0
    input_stats = {"file_size_kb": 1.0}

    metrics = calculate_metrics(raw_text, processed_text, processing_time, mock_config, input_stats)

    assert metrics["processing_time_seconds"] == 0.0
    # Speed metrics should not be present if time is zero
    assert "processing_speed_kb_per_second" not in metrics
    assert "processing_speed_chars_per_second" not in metrics

# --- Placeholder for generate_metrics_report Tests ---
# TODO: Add tests
# --- Tests for generate_metrics_report ---

def test_generate_metrics_report_full_tiktoken():
    """Test report generation with full metrics, using tiktoken counts."""
    metrics = {
        "processing_time_seconds": 1.2345,
        "original_text_length": 1000,
        "processed_text_length": 500,
        "text_length_reduction_percent": 50.0,
        "original_tokens": 200,
        "processed_tokens": 100,
        "token_reduction_percent": 50.0,
        "processing_speed_kb_per_second": 10.555,
        "input_file_stats": {
            "file_size_kb": 13.03,
            "file_extension": ".txt"
        }
    }
    report = generate_metrics_report(metrics)

    assert "# Processing Metrics Report" in report
    assert "Total: 1.23 seconds" in report
    assert "Speed: 10.55 KB/second" in report
    assert "Original length: 1,000 characters" in report
    assert "Processed length: 500 characters" in report
    assert "Length reduction: 50.00%" in report
    assert "Original tokens: 200" in report
    assert "Processed tokens: 100" in report
    assert "Token reduction: 50.00%" in report
    assert "File size: 13.03 KB" in report
    assert "File type: .txt" in report
    assert "(est.)" not in report # Ensure estimate suffix is NOT present

def test_generate_metrics_report_full_estimated():
    """Test report generation with full metrics, using estimated counts."""
    metrics = {
        "processing_time_seconds": 0.8,
        "original_text_length": 500,
        "processed_text_length": 400,
        "text_length_reduction_percent": 20.0,
        "original_tokens_estimate": 120,
        "processed_tokens_estimate": 90,
        "token_reduction_percent_estimate": 25.0,
        "processing_speed_chars_per_second": 625.00, # No KB speed
        "input_file_stats": {
            # Missing file_size_kb
            "file_extension": ".md"
        }
    }
    report = generate_metrics_report(metrics)

    assert "Total: 0.80 seconds" in report
    assert "KB/second" not in report # KB speed missing
    assert "Original length: 500 characters" in report
    assert "Processed length: 400 characters" in report
    assert "Length reduction: 20.00%" in report
    assert "Original tokens (est.): 120" in report
    assert "Processed tokens (est.): 90" in report
    assert "Token reduction (est.): 25.00%" in report
    assert "File size:" not in report # File size missing
    assert "File type: .md" in report

def test_generate_metrics_report_minimal():
    """Test report generation with minimal metrics provided."""
    metrics = {
        "processing_time_seconds": 0.1,
        "original_text_length": 10,
        "processed_text_length": 10,
        # Missing reductions, tokens, speeds, file stats
    }
    report = generate_metrics_report(metrics)

    assert "Total: 0.10 seconds" in report
    assert "Speed:" not in report
    assert "Original length: 10 characters" in report
    assert "Processed length: 10 characters" in report
    assert "Length reduction:" not in report
    assert "Token Metrics" not in report # Updated: Section should NOT be present if no token data
    assert "Original tokens" not in report # But values missing
    assert "Processed tokens" not in report
    assert "Token reduction" not in report
    assert "File Statistics" not in report # Section missing
