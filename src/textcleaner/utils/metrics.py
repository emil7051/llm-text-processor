"""Metrics and statistics for text processing."""

import re
from typing import Any, Dict, Optional

# Import necessary components
from textcleaner.utils.logging_config import get_logger
from textcleaner.config.config_manager import ConfigManager

try:
    import tiktoken
    _tiktoken_available = True
except ImportError:
    _tiktoken_available = False

logger = get_logger(__name__)

# Cache for loaded tokenizers to avoid reloading
_tokenizer_cache: Dict[str, Any] = {}

def get_tokenizer(encoding_name: str):
    """Load and cache a tiktoken tokenizer."""
    if not _tiktoken_available:
        return None
        
    if encoding_name not in _tokenizer_cache:
        try:
            tokenizer = tiktoken.get_encoding(encoding_name)
            _tokenizer_cache[encoding_name] = tokenizer
            logger.info(f"Loaded tiktoken tokenizer: {encoding_name}")
        except Exception as e:
            logger.error(f"Failed to load tiktoken tokenizer '{encoding_name}': {e}. Falling back to estimation.")
            _tokenizer_cache[encoding_name] = None # Cache failure to avoid retries
            return None
            
    return _tokenizer_cache[encoding_name]

def _estimate_token_count_fallback(text: str) -> int:
    """Fallback token estimation if tiktoken is unavailable or fails."""
    if not text:
        return 0
    words = text.split()
    punct_count = len(re.findall(r'[.,!?;:]', text))
    return len(words) + punct_count

def count_tokens(text: str, config: ConfigManager) -> int:
    """Count tokens using tiktoken based on configuration, with fallback."""
    if not text:
        return 0
        
    encoding_name = config.get("metrics.tokenizer_encoding", "cl100k_base")
    tokenizer = get_tokenizer(encoding_name)
    
    if tokenizer:
        try:
            return len(tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Tiktoken encoding failed for text snippet (falling back to estimation): {e}")
            return _estimate_token_count_fallback(text)
    else:
        # Use fallback if tiktoken isn't available or failed to load
        return _estimate_token_count_fallback(text)

def calculate_metrics(
    raw_text: str,
    processed_text: str,
    processing_time: float,
    config: ConfigManager,
    input_file_stats: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Calculate metrics for the text processing, using tiktoken if available."""
    
    metrics = {
        "processing_time_seconds": processing_time,
        "original_text_length": len(raw_text),
        "processed_text_length": len(processed_text),
    }
    
    # Calculate reduction in text length
    if len(raw_text) > 0:
        reduction_percent = 100 - (len(processed_text) / len(raw_text) * 100)
        metrics["text_length_reduction_percent"] = round(reduction_percent, 2)
    else:
        metrics["text_length_reduction_percent"] = 0
        
    # Count tokens using the new function
    original_tokens = count_tokens(raw_text, config)
    processed_tokens = count_tokens(processed_text, config)
    
    # Update metric keys to reflect actual counting (or estimation if fallback used)
    token_key_suffix = "_estimate" if get_tokenizer(config.get("metrics.tokenizer_encoding", "cl100k_base")) is None else ""
    metrics[f"original_tokens{token_key_suffix}"] = original_tokens
    metrics[f"processed_tokens{token_key_suffix}"] = processed_tokens
    
    # Calculate token reduction
    if original_tokens > 0:
        token_reduction = 100 - (processed_tokens / original_tokens * 100)
        metrics[f"token_reduction_percent{token_key_suffix}"] = round(token_reduction, 2)
    else:
        metrics[f"token_reduction_percent{token_key_suffix}"] = 0
        
    # Calculate processing speed
    if processing_time > 0:
        if input_file_stats and "file_size_kb" in input_file_stats:
            kb_per_second = input_file_stats["file_size_kb"] / processing_time
            metrics["processing_speed_kb_per_second"] = round(kb_per_second, 2)
            
        chars_per_second = len(raw_text) / processing_time
        metrics["processing_speed_chars_per_second"] = round(chars_per_second, 2)
        
    # Include file stats if available
    if input_file_stats:
        metrics["input_file_stats"] = input_file_stats
        
    return metrics


def generate_metrics_report(metrics: Dict[str, Any]) -> str:
    """Generate a human-readable report from metrics.
    
    Args:
        metrics: Dictionary of metrics from calculate_metrics().
        
    Returns:
        Formatted report as a string.
    """
    report = "# Processing Metrics Report\n\n"
    
    # Processing time
    time_seconds = metrics.get("processing_time_seconds", 0)
    report += f"## Processing Time\n"
    report += f"- Total: {time_seconds:.2f} seconds\n"
    
    if "processing_speed_kb_per_second" in metrics:
        report += f"- Speed: {metrics['processing_speed_kb_per_second']:.2f} KB/second\n"
        
    # Text metrics
    report += f"\n## Text Metrics\n"
    report += f"- Original length: {metrics.get('original_text_length', 0):,} characters\n"
    report += f"- Processed length: {metrics.get('processed_text_length', 0):,} characters\n"
    
    if "text_length_reduction_percent" in metrics:
        report += f"- Length reduction: {metrics['text_length_reduction_percent']:.2f}%\n"
        
    # Token metrics
    report += f"\n## Token Metrics\n"
    # Dynamically adjust report labels based on whether estimation was used
    token_label_suffix = " (est.)" if "_estimate" in next(k for k in metrics if 'original_tokens' in k) else ""
    report += f"- Original tokens{token_label_suffix}: {metrics.get(f'original_tokens{token_key_suffix}', 0):,}\n"
    report += f"- Processed tokens{token_label_suffix}: {metrics.get(f'processed_tokens{token_key_suffix}', 0):,}\n"
    
    if f"token_reduction_percent{token_key_suffix}" in metrics:
        report += f"- Token reduction{token_label_suffix}: {metrics[f'token_reduction_percent{token_key_suffix}']:.2f}%\n"
        
    # File stats
    if "input_file_stats" in metrics:
        stats = metrics["input_file_stats"]
        report += f"\n## File Statistics\n"
        
        if "file_size_kb" in stats:
            report += f"- File size: {stats['file_size_kb']:.2f} KB\n"
            
        if "file_extension" in stats:
            report += f"- File type: {stats['file_extension']}\n"
            
    return report
