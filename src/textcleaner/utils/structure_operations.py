"""Utilities for document structure operations."""

import re

def standardize_lists(content: str) -> str:
    """Standardize list item markers (e.g., bullets, dashes) to use Markdown asterisks."""
    # Pattern for various bullet point symbols
    bullet_pattern = r'^\s*[•·⦿⦾⦿⁃⁌⁍◦▪▫◘◙◦➢➣➤●○◼◻►▻▷▹➔→⇒⟹⟾⟶⇝⇢⤷⟼⟿⤳⤻⤔⟴]+ *'
    content = re.sub(bullet_pattern, '* ', content, flags=re.MULTILINE)
    # Pattern for dash/hyphen bullet points
    dash_pattern = r'^\s*[-–—] *'
    content = re.sub(dash_pattern, '* ', content, flags=re.MULTILINE)
    return content

def format_headings(content: str) -> str:
    """Identify potential headings and format them using Markdown."""
    lines = content.split('\n')
    potential_headings_indices = []
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Skip lines already formatted or empty or list items
        if not line_stripped or line_stripped.startswith(('#', '*', '-')):
            continue
            
        # Potential heading: relatively short line, not list item
        if len(line_stripped) < 80:
            # Check context: preceded or followed by an empty line
            prev_line_empty = (i == 0) or (i > 0 and not lines[i-1].strip())
            next_line_empty = (i == len(lines) - 1) or (i+1 < len(lines) and not lines[i+1].strip())
            
            # Heuristic: require surrounding empty lines or be short & preceded by empty
            if (prev_line_empty and next_line_empty) or (prev_line_empty and len(line_stripped) < 60):
                potential_headings_indices.append(i)

    # Apply heading formats after identifying all potential candidates
    if potential_headings_indices:
        temp_lines = list(lines) # Work on a copy
        for i in potential_headings_indices:
            line_stripped = temp_lines[i].strip()
            # Determine header level based on length
            if len(line_stripped) < 25:
                lines[i] = f"## {line_stripped}"
            elif len(line_stripped) < 60:
                lines[i] = f"### {line_stripped}"
            # Note: Longer lines identified as potential headings are not modified
        
        content = '\n'.join(lines)
    
    return content 