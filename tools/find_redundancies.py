#!/usr/bin/env python3
"""
Find potential code redundancies in the codebase.

This script analyzes Python files in the codebase to detect potentially
redundant code patterns that could be refactored for better maintainability.
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict, Counter

# Directories to check
DIRS_TO_CHECK = ["src", "tests"]

# Patterns to look for
PATTERNS = {
    "path_manipulation": r"(Path\(__file__\)\.parent|os\.path\.dirname\(__file__\))",
    "test_boilerplate": r"(def setup_method|def teardown_method)",
    "duplicate_imports": r"^import\s+([a-zA-Z0-9_.]+)|^from\s+([a-zA-Z0-9_.]+)\s+import",
    "magic_numbers": r"[^\"']\b\d{3,}\b[^\"']",
    "large_functions": r"def\s+([a-zA-Z0-9_]+)\s*\(",
    "multiple_assert_patterns": r"assert\s+[^,]+,\s*\".*\""
}

def analyze_file(file_path):
    """Analyze a single Python file for redundancy patterns."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
        
    results = {}
    
    # Check patterns
    for pattern_name, pattern in PATTERNS.items():
        matches = re.findall(pattern, content)
        if matches:
            results[pattern_name] = Counter(matches)
    
    # Count function lengths
    if 'large_functions' in results:
        function_lines = {}
        current_function = None
        line_count = 0
        indent_level = 0
        
        for line in lines:
            if re.match(r'\s*def\s+([a-zA-Z0-9_]+)\s*\(', line):
                current_function = re.search(r'def\s+([a-zA-Z0-9_]+)\s*\(', line).group(1)
                line_count = 1
                indent_level = len(line) - len(line.lstrip())
            elif current_function and line.strip():
                line_indent = len(line) - len(line.lstrip())
                if line_indent <= indent_level and line.strip() and not line.strip().startswith('#'):
                    function_lines[current_function] = line_count
                    current_function = None
                else:
                    line_count += 1
        
        # Add any final function
        if current_function:
            function_lines[current_function] = line_count
            
        # Filter to only include large functions (more than 30 lines)
        large_functions = {name: lines for name, lines in function_lines.items() if lines > 30}
        if large_functions:
            results['large_functions'] = large_functions
    
    return results


def find_redundancies():
    """Find redundant code patterns in Python files."""
    root_dir = Path(__file__).parent.parent
    
    all_results = {}
    pattern_counts = defaultdict(int)
    files_by_pattern = defaultdict(list)
    
    for dir_name in DIRS_TO_CHECK:
        dir_path = root_dir / dir_name
        for file_path in dir_path.glob('**/*.py'):
            # Skip venv files
            if 'venv' in str(file_path):
                continue
                
            rel_path = file_path.relative_to(root_dir)
            results = analyze_file(file_path)
            
            if results:
                all_results[str(rel_path)] = results
                for pattern_name in results:
                    pattern_counts[pattern_name] += 1
                    files_by_pattern[pattern_name].append(str(rel_path))
    
    print("=== Potential Code Redundancies ===\n")
    
    # Report by pattern
    for pattern_name, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"\n## {pattern_name} ({count} files)")
        
        if pattern_name == 'large_functions':
            # Special handling for large functions
            large_funcs = []
            for file_path in files_by_pattern[pattern_name]:
                for func_name, lines in all_results[file_path]['large_functions'].items():
                    large_funcs.append((file_path, func_name, lines))
            
            # Display top 10 largest functions
            for file_path, func_name, lines in sorted(large_funcs, key=lambda x: x[2], reverse=True)[:10]:
                print(f"  {file_path} - {func_name}() - {lines} lines")
        else:
            # Display files with most matches for this pattern
            top_files = sorted(
                [(file, len(all_results[file][pattern_name])) for file in files_by_pattern[pattern_name]],
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            for file_path, matches in top_files:
                print(f"  {file_path} - {matches} matches")
    
    print("\n=== Recommendations ===\n")
    if pattern_counts.get('path_manipulation', 0) > 3:
        print("- Consider creating a centralized paths module for path manipulation")
    
    if pattern_counts.get('test_boilerplate', 0) > 3:
        print("- Consider using pytest fixtures instead of setup/teardown methods")
    
    if pattern_counts.get('large_functions', 0) > 3:
        print("- Break down large functions into smaller, more focused functions")
    
    if pattern_counts.get('magic_numbers', 0) > 3:
        print("- Replace magic numbers with named constants")
    
    return len(pattern_counts) > 0


if __name__ == "__main__":
    has_redundancies = find_redundancies()
    sys.exit(1 if has_redundancies else 0) 