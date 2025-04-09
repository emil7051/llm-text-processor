"""Utilities for specific content optimization tasks."""

import re
import textwrap

# Common redundant phrases that can be removed or simplified
REDUNDANT_PHRASES = [
    (r'(?i)at the present time', 'now'),
    (r'(?i)due to the fact that', 'because'),
    (r'(?i)for the purpose of', 'for'),
    (r'(?i)in the event that', 'if'),
    (r'(?i)in order to', 'to'),
    (r'(?i)a majority of', 'most'),
    (r'(?i)a number of', 'many'),
    (r'(?i)in spite of the fact that', 'although'),
    (r'(?i)in the near future', 'soon'),
    (r'(?i)it is clear that', ''),
    (r'(?i)it should be noted that', ''),
    (r'(?i)it is important to note that', ''),
    (r'(?i)it is worth noting that', ''),
    (r'(?i)needless to say', ''),
    (r'(?i)the fact that', 'that'),
]

def remove_redundant_phrases(content: str) -> str:
    """Remove common redundant phrases."""
    for pattern, replacement in REDUNDANT_PHRASES:
        content = re.sub(pattern, replacement, content)
    return content

def condense_repetitive_patterns(content: str) -> str:
    """Condense repeated words and duplicated headers."""
    # Collapse repeated words (e.g., "very very" -> "very")
    pattern = r'(\b\w+\b)(\s+\1\b)+'
    content = re.sub(pattern, r'\1', content, flags=re.IGNORECASE)
    
    # Collapse repeated section headers (simple case)
    lines = content.splitlines()
    cleaned_lines = []
    last_line_stripped = None
    for line in lines:
        line_stripped = line.strip()
        # Skip if identical to the previous non-empty stripped line
        if line_stripped and line_stripped == last_line_stripped:
            continue
        cleaned_lines.append(line)
        if line_stripped: # Update last non-empty line
            last_line_stripped = line_stripped
            
    return '\n'.join(cleaned_lines)

def remove_excessive_punctuation(content: str) -> str:
    """Remove excessively repeated punctuation."""
    content = re.sub(r'([.!?]){2,}', r'\1', content) # Example: "!!!" -> "!"
    content = re.sub(r'-{2,}', '-', content) # Example: "---" -> "-"
    content = re.sub(r'_{2,}', '_', content) # Example: "___" -> "_"
    return content

def simplify_citations(content: str) -> str:
    """Simplify common citation formats (e.g., APA style)."""
    # (Smith et al., 2020) -> [Smith et al. 2020]
    content = re.sub(r'\(([^),]+?et al\.?)?,?\s+(\d{4})[^)]*\)', r'[\1 \2]', content)
    # (Smith, 2020) -> [Smith 2020]
    content = re.sub(r'\(([A-Za-z\']+),?\s+(\d{4})[^)]*\)', r'[\1 \2]', content) # Corrected regex slightly
    # [1] or [23] style (leave as is, maybe remove brackets later?)
    # For now, just focus on APA-like
    return content

def simplify_urls(content: str) -> str:
    """Simplify URLs to domain and path, removing protocol and query params."""
    # Pattern: http(s)://(www.)domain.com/path/to/page?query=string#fragment
    # Replacement: domain.com/path/to/page
    simplified_content = re.sub(
        r'https?://(?:www\.)?([^/\s]+)([^?#\s]*)?(?:\?[^\s]*)?(?:#[^\s]*)?',
        r'\1\2',
        content
    )
    return simplified_content

def optimize_line_length(content: str, max_length: int) -> str:
    """Wrap lines to a maximum length, preserving structure like headings/lists."""
    lines = content.split('\n')
    wrapped_lines = []
    structure_prefixes = ('#', '* ', '- ', '| ') # Prefixes to not wrap
    
    for line in lines:
        line_stripped = line.strip()
        # Don't wrap structural lines or empty lines
        if not line_stripped or any(line.startswith(p) for p in structure_prefixes):
            wrapped_lines.append(line)
        else:
            wrapped = textwrap.fill(
                line,
                width=max_length,
                break_long_words=False,
                break_on_hyphens=True,
                replace_whitespace=True, # Collapses internal whitespace
                drop_whitespace=True # Removes leading/trailing whitespace from wrapped lines
            )
            wrapped_lines.append(wrapped)
    
    return '\n'.join(wrapped_lines) 