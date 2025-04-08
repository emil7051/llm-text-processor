"""Text utility functions for the text processor."""

import re
import unicodedata
from typing import List, Optional, Set, Tuple


def clean_whitespace(text: str) -> str:
    """Clean excessive whitespace from text.
    
    Args:
        text: Text to clean.
        
    Returns:
        Text with cleaned whitespace.
    """
    if not text:
        return text
        
    # Replace multiple spaces with a single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Replace multiple newlines with at most two
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove trailing whitespace on each line
    text = re.sub(r' +$', '', text, flags=re.MULTILINE)
    
    return text


def normalize_unicode(text: str) -> str:
    """Normalize Unicode characters in text.
    
    Args:
        text: Text to normalize.
        
    Returns:
        Text with normalized Unicode characters.
    """
    if not text:
        return text
        
    # NFKC normalization: compatibility decomposition, followed by canonical composition
    return unicodedata.normalize('NFKC', text)


def identify_headings(lines: List[str]) -> List[Tuple[int, int]]:
    """Identify potential headings in a list of text lines.
    
    Args:
        lines: List of text lines to analyze.
        
    Returns:
        List of (line_index, heading_level) tuples.
    """
    headings = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Check if already a markdown heading
        if line.startswith('#'):
            continue
            
        # Potential heading: short line (not starting with * or - for lists)
        if len(line) < 60 and not line.startswith('*') and not line.startswith('-'):
            # Check if next line is empty or if previous line is empty (heading pattern)
            if (i+1 < len(lines) and not lines[i+1].strip()) or (i > 0 and not lines[i-1].strip()):
                # Determine header level based on length
                if len(line) < 20:
                    headings.append((i, 2))  # ## Heading
                else:
                    headings.append((i, 3))  # ### Heading
    
    return headings


def format_as_markdown_headings(lines: List[str], headings: List[Tuple[int, int]]) -> List[str]:
    """Format identified headings as Markdown headings.
    
    Args:
        lines: List of text lines.
        headings: List of (line_index, heading_level) tuples.
        
    Returns:
        List of text lines with formatted headings.
    """
    # Make a copy to avoid modifying the original
    result = lines.copy()
    
    # Format each heading (process in reverse to avoid index shifts)
    for line_idx, level in reversed(headings):
        hashes = '#' * level
        result[line_idx] = f"{hashes} {lines[line_idx].strip()}"
    
    return result


def detect_and_format_lists(text: str) -> str:
    """Detect and format list items consistently.
    
    Args:
        text: Text to process.
        
    Returns:
        Text with consistently formatted lists.
    """
    if not text:
        return text
        
    # Convert various bullet characters to Markdown list format
    bullet_chars = r'[•·⦿⦾⦿⁃⁌⁍◦▪▫◘◙◦➢➣➤●○◼◻►▻▷▹➔→⇒⟹⟾⟶⇝⇢⤷⟼⟿⤳⤻⤔⟴]'
    text = re.sub(f"^\\s*{bullet_chars}\\s*", "* ", text, flags=re.MULTILINE)
    
    # Convert dashes at start of lines to list items
    text = re.sub(r'^\s*[-–—]\s+', '* ', text, flags=re.MULTILINE)
    
    return text


def tokenize_text(text: str) -> List[str]:
    """Split text into tokens for analysis.
    
    This is a simple tokenizer for analysis purposes.
    For actual NLP tasks, a more sophisticated tokenizer should be used.
    
    Args:
        text: Text to tokenize.
        
    Returns:
        List of tokens.
    """
    if not text:
        return []
        
    # First split by whitespace
    words = re.findall(r'\S+', text)
    
    # Then handle punctuation
    tokens = []
    for word in words:
        # Split out trailing punctuation
        match = re.match(r'(.+?)([.,!?;:]+)$', word)
        if match:
            word_part, punct = match.groups()
            tokens.append(word_part)
            tokens.append(punct)
        else:
            tokens.append(word)
            
    return tokens


def remove_redundant_text(text: str, threshold: float = 0.8) -> str:
    """Remove redundant paragraphs of text.
    
    Uses a simple approach to detect and remove paragraphs that are
    highly similar to previous paragraphs.
    
    Args:
        text: Text to process.
        threshold: Similarity threshold for considering paragraphs redundant.
        
    Returns:
        Text with redundant paragraphs removed.
    """
    if not text:
        return text
        
    # Split into paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    
    # Skip if there's only one paragraph
    if len(paragraphs) <= 1:
        return text
        
    # Keep track of seen paragraphs and their tokens
    unique_paragraphs = []
    paragraph_tokens = []
    
    for paragraph in paragraphs:
        # Skip empty paragraphs
        if not paragraph.strip():
            continue
            
        # Tokenize paragraph
        tokens = set(tokenize_text(paragraph.lower()))
        
        # Skip if too short
        if len(tokens) < 5:
            unique_paragraphs.append(paragraph)
            paragraph_tokens.append(tokens)
            continue
            
        # Check if this paragraph is redundant
        redundant = False
        for i, existing_tokens in enumerate(paragraph_tokens):
            # Skip if lengths are too different
            if len(tokens) < len(existing_tokens) * 0.5 or len(tokens) > len(existing_tokens) * 2:
                continue
                
            # Calculate Jaccard similarity
            intersection = len(tokens.intersection(existing_tokens))
            union = len(tokens.union(existing_tokens))
            
            if intersection / union > threshold:
                redundant = True
                break
                
        if not redundant:
            unique_paragraphs.append(paragraph)
            paragraph_tokens.append(tokens)
    
    # Join unique paragraphs back together
    return '\n\n'.join(unique_paragraphs)


def extract_main_content(text: str) -> str:
    """Attempt to extract the main content from text, removing boilerplate.
    
    Uses heuristics to identify and extract the main content.
    
    Args:
        text: Text to process.
        
    Returns:
        Main content extracted from the text.
    """
    if not text:
        return text
        
    # Split into paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    
    # Skip if there's only one paragraph
    if len(paragraphs) <= 1:
        return text
        
    # Calculate the length of each paragraph
    paragraph_lengths = [len(p.strip()) for p in paragraphs]
    
    # Find the longest paragraph
    max_length = max(paragraph_lengths)
    
    # Keep paragraphs that are at least 25% of the longest paragraph
    # or that appear to be headings
    main_content_paragraphs = []
    
    for i, paragraph in enumerate(paragraphs):
        p_stripped = paragraph.strip()
        
        # Keep if it's a heading
        if re.match(r'^#+\s+', p_stripped):
            main_content_paragraphs.append(paragraph)
            continue
            
        # Keep if it's a list item
        if re.match(r'^\s*[\*\-]\s+', p_stripped):
            main_content_paragraphs.append(paragraph)
            continue
            
        # Keep if it's substantial content
        if len(p_stripped) >= max_length * 0.25:
            main_content_paragraphs.append(paragraph)
            
    # Join the main content paragraphs
    return '\n\n'.join(main_content_paragraphs)
