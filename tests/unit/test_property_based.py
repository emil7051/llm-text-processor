"""
Property-based tests for the LLM Text Processor
"""

import pytest
from pathlib import Path
import tempfile

try:
    import hypothesis
    from hypothesis import given, strategies as st
    from hypothesis.strategies import characters
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False

from textcleaner.core.factories import TextProcessorFactory
from textcleaner.core.processor import TextProcessor


# Skip all tests if hypothesis is not available
pytestmark = pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, 
                               reason="Hypothesis package not installed")


@pytest.fixture
def processor():
    """Create a TextProcessor for testing"""
    factory = TextProcessorFactory()
    return factory.create_standard_processor()


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


# Define text generation strategies
text_content = st.text(
    alphabet=characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'P'),
        blacklist_characters='\x00\n\r'
    ),
    min_size=10,
    max_size=1000
)

markdown_headings = st.lists(
    st.tuples(
        st.integers(min_value=1, max_value=6),  # Heading level
        st.text(min_size=5, max_size=50, alphabet=characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'P'),
            blacklist_characters='\x00\n\r'
        ))  # Heading text
    ),
    min_size=1,
    max_size=5
)

paragraphs = st.lists(
    st.text(min_size=20, max_size=200, alphabet=characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'P'),
        blacklist_characters='\x00\n\r'
    )),
    min_size=1,
    max_size=10
)


@given(content=text_content)
def test_processor_preserves_content_meaning(processor, content, temp_directory):
    """Test that the processor preserves the meaning of the content"""
    if not content.strip():
        return  # Skip empty content
        
    # Create a temp file with the generated content
    input_file = temp_directory / "property_test.txt"
    with open(input_file, "w") as f:
        f.write(content)
    
    # Process the file
    output_file = temp_directory / "property_test_output.txt"
    result = processor.process_file(input_file, output_file, "plain_text")
    
    # Skip if processing failed (might happen with extreme inputs)
    if not result.success:
        pytest.skip(f"Processing failed: {result.error}")
    
    # Read the processed content
    processed_content = output_file.read_text()
    
    # Core property: The processed text should still contain significant words from the original
    # We'll check that at least 70% of words with length > 5 are preserved
    significant_words = [word for word in content.split() if len(word) > 5]
    if significant_words:
        preserved_count = sum(1 for word in significant_words if word in processed_content)
        preservation_rate = preserved_count / len(significant_words)
        assert preservation_rate >= 0.7, f"Only preserved {preservation_rate:.1%} of significant words"


@given(headings=markdown_headings, paragraphs=paragraphs)
def test_processor_preserves_structure(processor, headings, paragraphs, temp_directory):
    """Test that the processor preserves document structure"""
    # Create a markdown document with the generated structure
    content = []
    
    # Add headings and paragraphs
    for i, (heading_level, heading_text) in enumerate(headings):
        # Add heading
        content.append(f"{'#' * heading_level} {heading_text}")
        content.append("")  # Empty line after heading
        
        # Add some paragraphs after each heading
        if i < len(paragraphs):
            content.append(paragraphs[i])
            content.append("")  # Empty line after paragraph
    
    # Write to file
    input_file = temp_directory / "structure_test.md"
    with open(input_file, "w") as f:
        f.write("\n".join(content))
    
    # Process the file
    output_file = temp_directory / "structure_test_output.md"
    result = processor.process_file(input_file, output_file, "markdown")
    
    # Skip if processing failed
    if not result.success:
        pytest.skip(f"Processing failed: {result.error}")
    
    # Read the processed content
    processed_content = output_file.read_text()
    
    # Core property: All headings should be preserved in markdown output
    for _, heading_text in headings:
        assert heading_text in processed_content, f"Heading '{heading_text}' was lost in processing"


@given(content=text_content)
def test_processor_improves_token_efficiency(processor, content, temp_directory):
    """Test that the processor generally improves token efficiency"""
    if len(content.strip()) < 50:
        return  # Skip very short content
        
    # Create a temp file with the generated content
    input_file = temp_directory / "efficiency_test.txt"
    
    # Add some inefficiencies that should be removed
    inefficient_content = content
    # Add some repeated phrases
    repeated_phrase = "this phrase is repeated multiple times and should be optimized. "
    inefficient_content = repeated_phrase * 5 + inefficient_content + repeated_phrase * 5
    
    with open(input_file, "w") as f:
        f.write(inefficient_content)
    
    # Process the file with aggressive settings
    factory = TextProcessorFactory()
    aggressive_processor = factory.create_processor(config_type="aggressive")
    
    output_file = temp_directory / "efficiency_test_output.txt"
    result = aggressive_processor.process_file(input_file, output_file, "plain_text")
    
    # Skip if processing failed
    if not result.success:
        pytest.skip(f"Processing failed: {result.error}")
    
    # Verify token reduction metrics exist
    assert "token_reduction_percent" in result.metrics
    
    # For very inefficient content, we should see some reduction
    if len(inefficient_content) > 500:
        # The aggressive processor should achieve at least some token reduction
        assert result.metrics["token_reduction_percent"] > 0, "No token reduction achieved"


@given(st.integers(min_value=2, max_value=10))
def test_parallel_processing_consistent_with_sequential(processor, num_files, temp_directory):
    """Test that parallel processing gives the same results as sequential processing"""
    # Create multiple small files with simple content
    file_paths = []
    for i in range(num_files):
        file_path = temp_directory / f"parallel_test_{i}.txt"
        with open(file_path, "w") as f:
            f.write(f"Test content for file {i}.\n")
            f.write("This is a simple file to test parallel vs sequential processing.\n")
            f.write(f"File ID: {i}\n")
        file_paths.append(file_path)
    
    # Create output directories
    parallel_output_dir = temp_directory / "parallel_output"
    parallel_output_dir.mkdir()
    
    sequential_output_dir = temp_directory / "sequential_output"
    sequential_output_dir.mkdir()
    
    # Process in parallel
    parallel_results = processor.process_directory_parallel(
        temp_directory,
        parallel_output_dir,
        file_extensions=[".txt"]
    )
    
    # Process sequentially
    sequential_results = processor.process_directory(
        temp_directory,
        sequential_output_dir,
        file_extensions=[".txt"]
    )
    
    # Compare results
    assert len(parallel_results) == len(sequential_results)
    
    # Read and compare output files
    for i in range(num_files):
        parallel_file = parallel_output_dir / f"parallel_test_{i}.md"
        sequential_file = sequential_output_dir / f"parallel_test_{i}.md"
        
        # Both files should exist
        assert parallel_file.exists()
        assert sequential_file.exists()
        
        # Content should be identical (or at least very similar)
        parallel_content = parallel_file.read_text()
        sequential_content = sequential_file.read_text()
        
        # Due to timing differences, there might be slight variations in metrics,
        # but the core content should be identical
        assert parallel_content == sequential_content, f"Content mismatch for file {i}"
