"""Metrics and statistics for text processing."""

import re
from typing import Any, Dict, Optional


def estimate_token_count(text: str) -> int:
    """Estimate the number of tokens in a text string.
    
    This is a rough approximation based on common tokenization practices.
    For more accurate counts, a specific tokenizer should be used.
    
    Args:
        text: Text to analyze.
        
    Returns:
        Estimated token count.
    """
    if not text:
        return 0
        
    # Split on whitespace
    words = text.split()
    
    # Count punctuation that would be separate tokens
    punct_count = len(re.findall(r'[.,!?;:]', text))
    
    # Estimate token count (words + punctuation)
    # This is a very rough estimate assuming:
    # - Each word is roughly one token
    # - Some punctuation marks are separate tokens
    # - Some words will be split into multiple tokens
    return len(words) + punct_count


def calculate_metrics(
    raw_text: str,
    processed_text: str,
    processing_time: float,
    input_file_stats: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Calculate metrics for the text processing.
    
    Args:
        raw_text: Raw text before processing.
        processed_text: Processed text after all transformations.
        processing_time: Time taken for processing in seconds.
        input_file_stats: Statistics about the input file.
        
    Returns:
        Dictionary of metrics.
    """
    # Basic metrics
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
        
    # Estimate token counts
    original_tokens = estimate_token_count(raw_text)
    processed_tokens = estimate_token_count(processed_text)
    
    metrics["original_token_estimate"] = original_tokens
    metrics["processed_token_estimate"] = processed_tokens
    
    # Calculate token reduction
    if original_tokens > 0:
        token_reduction = 100 - (processed_tokens / original_tokens * 100)
        metrics["token_reduction_percent"] = round(token_reduction, 2)
    else:
        metrics["token_reduction_percent"] = 0
        
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
    report += f"- Original tokens (est.): {metrics.get('original_token_estimate', 0):,}\n"
    report += f"- Processed tokens (est.): {metrics.get('processed_token_estimate', 0):,}\n"
    
    if "token_reduction_percent" in metrics:
        report += f"- Token reduction: {metrics['token_reduction_percent']:.2f}%\n"
        
    # File stats
    if "input_file_stats" in metrics:
        stats = metrics["input_file_stats"]
        report += f"\n## File Statistics\n"
        
        if "file_size_kb" in stats:
            report += f"- File size: {stats['file_size_kb']:.2f} KB\n"
            
        if "file_extension" in stats:
            report += f"- File type: {stats['file_extension']}\n"
            
    return report
