"""Utilities for specific content cleaning tasks."""

import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

# Common patterns for headers/footers
HEADER_FOOTER_PATTERNS = [
    r'^\s*\d+\s*$', # Standalone page numbers
    # Allow specific extra content after Page X of Y, be stricter, handle markdown
    r'(?i)^\s*(?:##?#? )?Page\s+\d+(\s+of\s+\d+)?(\s*[|/\\-]\s*.*)?$', # Added optional markdown ##
    # Common labels, case-insensitive, handle markdown
    r'(?i)^\s*(?:##?#? )?(Confidential|Draft|Internal Use Only|Copyright|All rights reserved)\s*$', # Added optional markdown ##
    r'^\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s*$', # Date stamps
    r'^\s*(Ref|Reference|Doc|Document)\s*[#:]?\s*[\w-]+', # Document refs
    r'^\s*(From|To|Cc|Subject|Sent|Date):' # Email headers
    # Catch simple "HEADER" or "FOOTER" lines, possibly with separators or markdown
    # Make these more specific to avoid matching code comments
    r'(?i)^##\s*FOOTER\s*$', # Specific pattern for markdown '## FOOTER'
    r'(?i)^\s*(?:##?#? )?\s*(FOOTER|HEADER)\s*$', # Simplified pattern, added optional markdown ##
    # r'(?i)^\s*(?:##?#? )?(FOOTER|HEADER)\s*[-=]{3,}\s*$' # Commented out for now
    # Removed the generic separator pattern: r'^\s*[-=]{3,}\s*$'
]

# Common patterns for boilerplate text
BOILERPLATE_PATTERNS = [
    r'(?i)all rights reserved\.?.*',
    r'(?i)confidentiality notice:.*',
    r'(?i)this (email|document) (contains|is) confidential.*',
    r'(?i)disclaimer:.*',
    r'(?i)if you (have received|are not).*in error.*',
    r'(?i)sent from my (iphone|ipad|android|mobile device)',
    r'(?i)(tel|phone|fax|email):\s*[\w.@+-]+',
    r'(?i)copyright\s+©?\s*\d{4}.*',
    r'(?i)privacy policy.*',
    r'(?i)please (find|see) (the attached|attached) (file|document)'
]

def remove_headers_footers(content: str) -> str:
    """Remove common headers, footers, and page numbers."""
    lines = content.splitlines()
    cleaned_lines = []
    repeated_lines = {} # Track frequency of lines
    header_footer_candidate_threshold = 3 # How many times a line must repeat
    max_hf_length = 100 # Max length for a line to be considered header/footer by repetition
    
    for line in lines:
        line_stripped = line.strip()
        
        if not line_stripped:
            cleaned_lines.append('') # Keep empty lines for structure
            continue
        
        # DEBUG: Inspect the line being checked
        if "FOOTER" in line_stripped:
            print(f"DEBUG H/F: Checking line: {repr(line_stripped)}") # Use repr to see hidden chars

        skip_line = False
        # Check against predefined patterns
        for pattern in HEADER_FOOTER_PATTERNS:
            # DEBUG: Show pattern being checked for FOOTER line
            if "FOOTER" in line_stripped:
                print(f"DEBUG H/F: Checking pattern {repr(pattern)} against line {repr(line_stripped)}")

            # Use re.search instead of re.match to find pattern anywhere in the line
            # Although patterns use ^/$, this might handle subtle cases differently
            if re.search(pattern, line_stripped, re.IGNORECASE):
                print(f"DEBUG H/F: Matched pattern '{pattern}' on line: {line_stripped[:50]}...") # DEBUG
                skip_line = True
                break
        if skip_line: continue
        
        # Check for repetition
        repeated_lines[line_stripped] = repeated_lines.get(line_stripped, 0) + 1
        if repeated_lines[line_stripped] >= header_footer_candidate_threshold and len(line_stripped) < max_hf_length:
            print(f"DEBUG H/F: Skipping repeated line: {line_stripped[:50]}...") # DEBUG
            skip_line = True
            
        if not skip_line:
            cleaned_lines.append(line)
    
    # Safeguard: If almost all lines were removed, it might be a false positive (e.g., code file)
    # Revert to original content if cleaning was too aggressive.
    original_line_count = len(lines)
    cleaned_line_count = len([line for line in cleaned_lines if line.strip()]) # Count non-empty cleaned lines
    # Allow removing up to 95% of lines, but not more.
    if original_line_count > 0 and (cleaned_line_count / original_line_count) < 0.05:
        logger.warning(f"Header/footer removal seemed too aggressive (removed >95% of lines). Reverting for this file.")
        return content # Return original content
        
    return '\n'.join(cleaned_lines)

def remove_duplicates(content: str) -> str:
    """Remove duplicate paragraphs."""
    paragraphs = re.split(r'\n\s*\n', content)
    unique_paragraphs = []
    seen_paragraphs = set()
    min_duplicate_length = 20 # Only remove duplicates longer than this
    
    for para in paragraphs:
        para_stripped = para.strip()
        if not para_stripped: continue # Skip empty paragraphs

        normalized = re.sub(r'\s+', ' ', para_stripped.lower())
        if normalized in seen_paragraphs and len(normalized) > min_duplicate_length:
            continue
        
        unique_paragraphs.append(para_stripped) # Append original stripped para
        seen_paragraphs.add(normalized)
    
    return '\n\n'.join(unique_paragraphs)

def remove_boilerplate_text(content: str) -> str:
    """Remove common boilerplate patterns."""
    for pattern in BOILERPLATE_PATTERNS:
        content = re.sub(pattern, '', content)
    return content

def clean_whitespace(content: str) -> str:
    """Clean up excessive whitespace, tabs, and normalize line breaks."""
    content = content.replace('\t', ' ') # Replace tabs with spaces first
    content = re.sub(r' {2,}', ' ', content) # Collapse multiple spaces
    content = re.sub(r' +\n', '\n', content) # Remove trailing spaces on lines
    content = re.sub(r'\r\n', '\n', content) # Normalize line endings
    content = re.sub(r'\n{3,}', '\n\n', content) # Collapse multiple blank lines
    return content.strip() # Remove leading/trailing whitespace from the whole content

def merge_short_paragraphs(content: str) -> str:
    """Merge short consecutive paragraphs if they don't look like lists or headings."""
    paragraphs = re.split(r'(\n\s*\n)', content) # Keep separators
    merged_paragraphs = []
    i = 0
    min_para_length = 80 # Paragraphs shorter than this might be merged
    sentence_ending_punctuation = ('.', '!', '?', ':', ';')
    list_or_heading_starts = ('#', '-', '*', '>', '|')

    while i < len(paragraphs):
        current_para = paragraphs[i].strip()
        
        if not current_para: # Skip empty parts resulting from split
            i += 1
            continue

        # Lookahead logic needs careful index handling
        if i + 2 < len(paragraphs): # Need current, separator, and next
            separator = paragraphs[i+1]
            next_para = paragraphs[i+2].strip()
            
            if (len(current_para) < min_para_length and 
                not current_para.endswith(sentence_ending_punctuation) and
                not current_para.startswith(list_or_heading_starts) and
                next_para and # Ensure next paragraph is not empty
                not next_para.startswith(list_or_heading_starts)):
                
                # Merge: current + space + next
                merged_paragraphs.append(f"{current_para} {next_para}")
                i += 3 # Skip current, separator, next
                continue # Restart loop after merge

        # No merge condition met or end of list, add current paragraph
        merged_paragraphs.append(current_para)
        i += 1 # Move to the next element (could be separator or next para)

    # Join requires paragraphs, not the mix from split
    # Need to filter out separators before joining
    # A simpler approach might be better if this logic is complex
    
    # Simpler Re-implementation for merging:
    lines = content.splitlines()
    merged_lines = []
    buffer = ""
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line: # Blank line signals paragraph break
            if buffer: merged_lines.append(buffer)
            merged_lines.append("") # Preserve blank lines
            buffer = ""
        elif (len(buffer) > 0 and len(buffer) < min_para_length and 
              not buffer.endswith(sentence_ending_punctuation) and 
              not buffer.startswith(list_or_heading_starts) and
              not stripped_line.startswith(list_or_heading_starts)):
            buffer += " " + stripped_line # Merge
        else:
            if buffer: merged_lines.append(buffer) # Add previous buffer
            buffer = stripped_line # Start new buffer
    if buffer: merged_lines.append(buffer) # Add final buffer

    return '\n'.join(merged_lines)

def normalize_unicode(content: str) -> str:
    """Normalize unicode characters using NFC."""
    return unicodedata.normalize('NFC', content) 