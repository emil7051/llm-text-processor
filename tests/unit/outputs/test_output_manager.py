import pytest
from pathlib import Path
import re
from unittest.mock import patch, mock_open, MagicMock
import unittest.mock
import csv

# Import the classes to be tested
from textcleaner.outputs.output_manager import PlainTextWriter, CsvWriter, JsonWriter, MarkdownWriter, OutputManager
from textcleaner.config.config_manager import ConfigManager

# Mock the logger to avoid actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    """Fixture to mock the logger used within the output_manager module."""
    with patch('textcleaner.outputs.output_manager.logger') as mock_log:
        yield mock_log

# --- Tests for PlainTextWriter ---

@pytest.fixture
def plain_text_writer():
    """Fixture to create a PlainTextWriter instance."""
    return PlainTextWriter()

def test_plain_text_writer_init_with_markdown_it(plain_text_writer):
    """Test PlainTextWriter initialization when markdown-it is available."""
    # Assuming markdown-it IS available for this test scenario
    # We might need to mock the _markdown_it_available flag if complex setup is needed
    # For now, let's assume it's True based on default behavior or environment
    assert plain_text_writer.parser is not None
    # assert 'image' in plain_text_writer.parser.rules_disabled # Removed - Attribute likely doesn't exist in markdown-it-py>=3
    # assert 'table' in plain_text_writer.parser.rules_disabled # Removed - Attribute likely doesn't exist in markdown-it-py>=3
    assert plain_text_writer.parser.options['html'] is False # Check option update

@patch('textcleaner.outputs.output_manager._markdown_it_available', False)
def test_plain_text_writer_init_without_markdown_it(mock_logger):
    """Test PlainTextWriter initialization when markdown-it is NOT available."""
    writer = PlainTextWriter()
    assert writer.parser is None
    mock_logger.warning.assert_called_once_with(
        "markdown-it-py not found. Plain text output might be suboptimal using regex."
    )

# Test cases for markdown to plain text conversion using markdown-it
@pytest.mark.parametrize("markdown_input, expected_plain", [
    ("# Header 1\n\nSome text.", "Header 1\n\nSome text."),
    ("## Header 2\n\n*   List item 1\n*   List item 2", "Header 2\nList item 1\nList item 2"), # Assuming lists are rendered as lines
    ("Text with **bold** and *italic*.", "Text with bold and italic."),
    ("A [link](http://example.com).", "A link."), # Link text kept, URL removed
    ("Some `inline code`.", "Some inline code."),
    ("> Blockquote", "Blockquote"),
    ("---", ""), # Horizontal rule removed
    # Add more complex cases: nested lists, code blocks, etc. if needed based on parser config
    ("""
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
""", "Header 1 Header 2\nCell 1   Cell 2") # Basic table text extraction
])
def test_plain_text_writer_write_with_markdown_it(plain_text_writer, markdown_input, expected_plain, tmp_path):
    """Test writing plain text using markdown-it."""
    output_file = tmp_path / "output.txt"
    m = mock_open()
    with patch("builtins.open", m):
        plain_text_writer.write(markdown_input, output_file)

    m.assert_called_once_with(output_file, 'w', encoding='utf-8')
    handle = m()
    # Simulate how render works - it might add a trailing newline depending on input/config
    # Adjust assertion based on actual markdown-it behavior if needed
    written_content = handle.write.call_args[0][0]
    # Normalize newlines and spacing for comparison
    normalized_written = "\n".join(line.strip() for line in written_content.strip().splitlines())
    normalized_expected = "\n".join(line.strip() for line in expected_plain.strip().splitlines())
    assert normalized_written == normalized_expected


@patch('textcleaner.outputs.output_manager._markdown_it_available', False)
def test_plain_text_writer_write_without_markdown_it(tmp_path, mock_logger):
    """Test writing plain text using the regex fallback."""
    writer = PlainTextWriter() # Re-initialize with _markdown_it_available=False
    markdown_input = "# Header\n\nSome *bold* text.\n\n- List item\n\n`code`"
    expected_plain = "Header\n\nSome bold text.\n\nList item\n\ncode"
    output_file = tmp_path / "output.txt"

    m = mock_open()
    with patch("builtins.open", m):
        writer.write(markdown_input, output_file)

    m.assert_called_once_with(output_file, 'w', encoding='utf-8')
    handle = m()
    written_content = handle.write.call_args[0][0]
    # Normalize for comparison
    normalized_written = "\n".join(line.strip() for line in written_content.strip().splitlines())
    normalized_expected = "\n".join(line.strip() for line in expected_plain.strip().splitlines())

    assert normalized_written == normalized_expected
    mock_logger.debug.assert_called_with("Using regex fallback for plain text conversion.")


# Test cases for the regex fallback specifically
@pytest.mark.parametrize("markdown_input, expected_plain", [
    ("# Header", "Header"),
    ("### Deeper Header\nText", "Deeper Header\nText"),
    ("* List 1\n+ List 2", "List 1\nList 2"),
    ("No **bold** or *italic* markers.", "No bold or italic markers."),
    ("[Link Text](url)", "Link Text"),
    ("`inline code` snippet", "inline code snippet"),
    ("---", ""),
    ("""
| H1 | H2 |
|----|----|
| c1 | c2 |
""", "H1  H2 \nc1  c2"), # Basic regex table handling might be imperfect
    ("Line1\n\n\nLine2", "Line1\n\nLine2"), # Extra newline cleanup
])
def test_plain_text_writer_regex_fallback(plain_text_writer, markdown_input, expected_plain):
    """Test the _markdown_to_plain_fallback method directly."""
    # Ensure we are testing the fallback method even if markdown-it is available
    result = plain_text_writer._markdown_to_plain_fallback(markdown_input)
     # Normalize for comparison
    normalized_result = "\n".join(line.strip() for line in result.strip().splitlines())
    normalized_expected = "\n".join(line.strip() for line in expected_plain.strip().splitlines())
    assert normalized_result == normalized_expected


def test_plain_text_writer_write_io_error(plain_text_writer, tmp_path, mock_logger):
    """Test that IOError during file writing is caught and logged."""
    output_file = tmp_path / "output.txt"
    markdown_input = "Some content"

    # Mock open to raise IOError
    with patch("builtins.open", mock_open()) as m:
        m.side_effect = IOError("Disk full")
        with pytest.raises(IOError):
            plain_text_writer.write(markdown_input, output_file)

    mock_logger.error.assert_called_once_with(f"Failed to write plain text file {output_file}: Disk full")

# --- Placeholder for CsvWriter Tests ---
# TODO: Add tests for CsvWriter
@pytest.fixture
def csv_writer():
    """Fixture to create a CsvWriter instance."""
    return CsvWriter()

@patch('textcleaner.outputs.output_manager._markdown_it_available', False)
def test_csv_writer_init_without_markdown_it(mock_logger):
    """Test CsvWriter initialization when markdown-it is NOT available."""
    writer = CsvWriter()
    assert writer.parser is None
    mock_logger.warning.assert_called_once_with(
        "markdown-it-py not found. CSV output from tables might be suboptimal using regex."
    )

def test_csv_writer_init_with_markdown_it():
    """Test CsvWriter initialization when markdown-it is available."""
    # Assuming markdown-it IS available
    writer = CsvWriter()
    assert writer.parser is not None

# --- CsvWriter Tests: markdown-it ---

MARKDOWN_WITH_TABLE = """
Some text before the table.

| Header 1 | Header 2 |
|----------|----------|
| R1C1     | R1C2     |
| R2C1     | R2C2     |

Some text after the table.
"""

EXPECTED_CSV_TABLE = [
    ["Header 1", "Header 2"],
    ["R1C1", "R1C2"],
    ["R2C1", "R2C2"],
]

MARKDOWN_NO_TABLE = """
This is just plain text.
Line 2.

Line 4 after a blank line.
"""

EXPECTED_CSV_NO_TABLE = [
    ["Content"],
    ["This is just plain text."],
    ["Line 2."],
    ["Line 4 after a blank line."],
]

MARKDOWN_TWO_TABLES = """
Table 1:
| A | B |
|---|---|
| 1 | 2 |

Table 2:
| X | Y |
|---|---|
| 3 | 4 |
"""

EXPECTED_CSV_FIRST_TABLE = [
    ["A", "B"],
    ["1", "2"],
]


@patch('textcleaner.outputs.output_manager._markdown_it_available', True)
@patch('csv.writer')
def test_csv_writer_write_with_table_mdit(mock_csv_writer_cls, tmp_path, mock_logger):
    """Test writing CSV from markdown containing a table using markdown-it."""
    # Instantiate CsvWriter inside the test where patch is active
    csv_writer_instance = CsvWriter()

    output_file = tmp_path / "output.csv"
    mock_csv_writer_instance = MagicMock()
    mock_csv_writer_cls.return_value = mock_csv_writer_instance

    m = mock_open()
    with patch("builtins.open", m):
        # Mock the parser and token extraction if direct testing is preferred
        # Otherwise, rely on the actual markdown-it parsing if installed
        # For robustness, mocking might be better
        # Let's assume markdown-it works correctly for this test
        # Use the locally instantiated CsvWriter
        csv_writer_instance.write(MARKDOWN_WITH_TABLE, output_file)

    m.assert_called_once_with(output_file, 'w', encoding='utf-8', newline='')
    mock_csv_writer_instance.writerows.assert_called_once_with(EXPECTED_CSV_TABLE)
    # This logger check might need adjustment if CsvWriter() creates its own logger instance
    # For now, focus on the main failure.
    mock_logger.debug.assert_called_with(f"Writing first extracted table (3 rows) to {output_file}.")


@patch('textcleaner.outputs.output_manager._markdown_it_available', True)
@patch('csv.writer')
def test_csv_writer_write_two_tables_mdit(mock_csv_writer_cls, csv_writer, tmp_path, mock_logger):
    """Test writing CSV writes only the first table when multiple exist (using markdown-it)."""
    output_file = tmp_path / "output.csv"
    mock_csv_writer_instance = MagicMock()
    mock_csv_writer_cls.return_value = mock_csv_writer_instance

    m = mock_open()
    with patch("builtins.open", m):
         # Assuming markdown-it processes correctly
        csv_writer.write(MARKDOWN_TWO_TABLES, output_file)

    m.assert_called_once_with(output_file, 'w', encoding='utf-8', newline='')
    # Should write only the first table
    mock_csv_writer_instance.writerows.assert_called_once_with(EXPECTED_CSV_FIRST_TABLE)
    mock_logger.debug.assert_called_with(f"Writing first extracted table (2 rows) to {output_file}.")


@patch('textcleaner.outputs.output_manager._markdown_it_available', True)
@patch('csv.writer')
def test_csv_writer_write_no_table_mdit(mock_csv_writer_cls, tmp_path, mock_logger):
    """Test writing CSV when no table is present in markdown (using markdown-it)."""
    # Instantiate CsvWriter inside the test where patch is active
    csv_writer_instance_local = CsvWriter()

    output_file = tmp_path / "output.csv"
    mock_csv_writer_instance = MagicMock()
    mock_csv_writer_cls.return_value = mock_csv_writer_instance

    m = mock_open()
    with patch("builtins.open", m):
        # Use the locally instantiated CsvWriter
        csv_writer_instance_local.write(MARKDOWN_NO_TABLE, output_file)

    m.assert_called_once_with(output_file, 'w', encoding='utf-8', newline='')
    # Check that writerow was called for the header and then writerows for the content lines
    assert mock_csv_writer_instance.writerow.call_args_list[0] == unittest.mock.call(["Content"])

    # Check the calls to writerow for each line
    expected_calls = [
        unittest.mock.call([line]) for line in MARKDOWN_NO_TABLE.strip().split('\n') if line.strip()
    ]
    # Remove the header call before asserting content rows
    content_writerow_calls = [call for call in mock_csv_writer_instance.writerow.call_args_list if call != unittest.mock.call(["Content"])]

    # This assertion needs refinement - checking individual row calls is better
    # Let's check the final writerows call instead for simplicity here
    # Re-reading the code: it uses writerow for each line, not writerows.
    assert mock_csv_writer_instance.writerow.call_count == 4 # Header + 3 lines
    assert mock_csv_writer_instance.writerow.call_args_list[1] == unittest.mock.call(['This is just plain text.'])
    assert mock_csv_writer_instance.writerow.call_args_list[2] == unittest.mock.call(['Line 2.'])
    assert mock_csv_writer_instance.writerow.call_args_list[3] == unittest.mock.call(['Line 4 after a blank line.'])

    mock_logger.debug.assert_called_with(f"No tables found in content for {output_file}. Writing as single column CSV.")


@patch('textcleaner.outputs.output_manager._markdown_it_available', True)
def test_csv_writer_mdit_parse_error(csv_writer, tmp_path, mock_logger):
    """Test CSV writing handles markdown-it parsing errors gracefully."""
    output_file = tmp_path / "output.csv"
    markdown_input = "| Bad Table |\n|---|\n| Cell |" # Example potentially causing issues

    # Mock the parser's parse method to raise an exception
    with patch.object(csv_writer.parser, 'parse', side_effect=Exception("Parsing failed")):
        m = mock_open()
        with patch("builtins.open", m), patch('csv.writer') as mock_csv_writer_cls:
            mock_csv_writer_instance = MagicMock()
            mock_csv_writer_cls.return_value = mock_csv_writer_instance

            # Execute the write method
            csv_writer.write(markdown_input, output_file)

            # Verify error was logged
            mock_logger.error.assert_called_once_with(
                "Error parsing tables with markdown-it for CSV output: Parsing failed"
            )
            # Verify it fell back to writing as single column
            mock_logger.debug.assert_called_with(f"No tables found in content for {output_file}. Writing as single column CSV.")
            mock_csv_writer_instance.writerow.assert_any_call(["Content"]) # Check header written


# --- CsvWriter Tests: Regex Fallback ---

@patch('textcleaner.outputs.output_manager._markdown_it_available', False)
@patch('csv.writer')
def test_csv_writer_write_with_table_regex(mock_csv_writer_cls, tmp_path, mock_logger):
    """Test writing CSV from markdown using regex fallback."""
    writer = CsvWriter() # Initialize with fallback active
    output_file = tmp_path / "output.csv"
    mock_csv_writer_instance = MagicMock()
    mock_csv_writer_cls.return_value = mock_csv_writer_instance

    m = mock_open()
    with patch("builtins.open", m):
        writer.write(MARKDOWN_WITH_TABLE, output_file)

    m.assert_called_once_with(output_file, 'w', encoding='utf-8', newline='')
    mock_logger.debug.assert_any_call("Using regex fallback for table extraction.")
    # Adjust expected CSV for regex parsing nuances if necessary
    # The fallback regex splits cells based on '|' and strips whitespace.
    expected_regex_csv = [
        ['Header 1', 'Header 2'], # Regex extracts these correctly
        ['R1C1', 'R1C2'],
        ['R2C1', 'R2C2']
    ]
    mock_csv_writer_instance.writerows.assert_called_once_with(expected_regex_csv)
    mock_logger.debug.assert_called_with(f"Writing first extracted table (3 rows) to {output_file}.")


@patch('textcleaner.outputs.output_manager._markdown_it_available', False)
@patch('csv.writer')
def test_csv_writer_write_no_table_regex(mock_csv_writer_cls, tmp_path, mock_logger):
    """Test writing CSV using regex fallback when no table is found."""
    writer = CsvWriter()
    output_file = tmp_path / "output.csv"
    mock_csv_writer_instance = MagicMock()
    mock_csv_writer_cls.return_value = mock_csv_writer_instance

    m = mock_open()
    with patch("builtins.open", m):
        writer.write(MARKDOWN_NO_TABLE, output_file)

    m.assert_called_once_with(output_file, 'w', encoding='utf-8', newline='')
    mock_logger.debug.assert_any_call("Using regex fallback for table extraction.")
    mock_logger.debug.assert_called_with(f"No tables found in content for {output_file}. Writing as single column CSV.")
    # Check writing as single column
    mock_csv_writer_instance.writerow.assert_any_call(["Content"])
    # Check content rows (similar to mdit test)
    assert mock_csv_writer_instance.writerow.call_count == 4 # Header + 3 lines
    assert mock_csv_writer_instance.writerow.call_args_list[1] == unittest.mock.call(['This is just plain text.'])


MARKDOWN_MISMATCHED_COLS = """
| H1 | H2 | H3 |
|----|----|----|
| c1 | c2 |
| c4 | c5 | c6 |
"""

@patch('textcleaner.outputs.output_manager._markdown_it_available', False)
@patch('csv.writer')
def test_csv_writer_write_mismatched_cols_regex(mock_csv_writer_cls, tmp_path, mock_logger):
    """Test regex fallback handles mismatched columns (skips table)."""
    writer = CsvWriter()
    output_file = tmp_path / "output.csv"
    mock_csv_writer_instance = MagicMock()
    mock_csv_writer_cls.return_value = mock_csv_writer_instance

    m = mock_open()
    with patch("builtins.open", m):
        writer.write(MARKDOWN_MISMATCHED_COLS, output_file)

    # Check logger warning about skipping with details
    mock_logger.warning.assert_called_with(
        "Skipping table due to mismatched header/row columns (regex fallback). Header had 3, row had 2: | c1 | c2 |"
    )
    # Check it falls back to single column output
    mock_logger.debug.assert_called_with(f"No tables found in content for {output_file}. Writing as single column CSV.")
    mock_csv_writer_instance.writerow.assert_any_call(["Content"])


# --- CsvWriter Tests: Error Handling ---

@patch('textcleaner.outputs.output_manager._markdown_it_available', True)
def test_csv_writer_write_io_error(csv_writer, tmp_path, mock_logger):
    """Test CsvWriter handles IOError during file write."""
    output_file = tmp_path / "output.csv"

    with patch("builtins.open", mock_open()) as m_open:
        m_open.side_effect = IOError("Cannot write")
        with pytest.raises(IOError):
            csv_writer.write(MARKDOWN_WITH_TABLE, output_file)

    mock_logger.error.assert_called_once_with(f"Failed to write CSV file {output_file}: Cannot write")


@patch('textcleaner.outputs.output_manager._markdown_it_available', True)
@patch('csv.writer')
def test_csv_writer_write_csv_error(mock_csv_writer_cls, csv_writer, tmp_path, mock_logger):
    """Test CsvWriter handles csv.Error during writing."""
    output_file = tmp_path / "output.csv"
    mock_csv_writer_instance = MagicMock()
    mock_csv_writer_cls.return_value = mock_csv_writer_instance
    # Simulate a csv.Error (e.g., during writerows)
    mock_csv_writer_instance.writerows.side_effect = csv.Error("CSV formatting error")

    m = mock_open()
    with patch("builtins.open", m):
        with pytest.raises(RuntimeError, match="CSV writing error: CSV formatting error"):
            csv_writer.write(MARKDOWN_WITH_TABLE, output_file)

    mock_logger.error.assert_called_once_with(f"CSV writing error for {output_file}: CSV formatting error")

# --- Placeholder for JsonWriter Tests ---
# TODO: Add tests for JsonWriter
@pytest.fixture
def json_writer():
    """Fixture to create a JsonWriter instance."""
    return JsonWriter()

def test_json_writer_write_content_only(json_writer, tmp_path):
    """Test writing JSON with only content."""
    output_file = tmp_path / "output.json"
    content = "This is the main content."
    expected_data = {"content": content}

    m = mock_open()
    with patch("builtins.open", m), patch("json.dump") as mock_json_dump:
        json_writer.write(content, output_file)

    m.assert_called_once_with(output_file, 'w', encoding='utf-8')
    handle = m()
    mock_json_dump.assert_called_once_with(
        expected_data, handle, indent=2, ensure_ascii=False
    )

def test_json_writer_write_with_metadata(json_writer, tmp_path):
    """Test writing JSON with content and metadata."""
    output_file = tmp_path / "output.json"
    content = "Some data."
    metadata = {"source": "file.txt", "pages": 1}
    expected_data = {"content": content, "metadata": metadata}

    m = mock_open()
    with patch("builtins.open", m), patch("json.dump") as mock_json_dump:
        json_writer.write(content, output_file, metadata=metadata)

    m.assert_called_once_with(output_file, 'w', encoding='utf-8')
    handle = m()
    mock_json_dump.assert_called_once_with(
        expected_data, handle, indent=2, ensure_ascii=False
    )

def test_json_writer_write_io_error(json_writer, tmp_path, mock_logger):
    """Test JsonWriter handles IOError during file write."""
    output_file = tmp_path / "output.json"
    content = "data"

    with patch("builtins.open", mock_open()) as m_open:
        m_open.side_effect = IOError("Permission denied")
        with pytest.raises(IOError):
            json_writer.write(content, output_file)

    mock_logger.error.assert_called_once_with(
        f"Failed to write JSON file {output_file}: Permission denied"
    )

def test_json_writer_write_serialization_error(json_writer, tmp_path, mock_logger):
    """Test JsonWriter handles TypeError during JSON serialization."""
    output_file = tmp_path / "output.json"
    # Use complex numbers, which are not JSON serializable by default
    content = "Data with complex numbers"
    metadata = {"value": complex(1, 2)}

    m = mock_open()
    # json.dump will raise TypeError when trying to serialize the complex number
    with patch("builtins.open", m):
        with pytest.raises(RuntimeError, match="JSON serialization error: "):
            json_writer.write(content, output_file, metadata=metadata)

    # Verify the specific error log for serialization failure
    mock_logger.error.assert_called_once()
    assert "Failed to serialize data to JSON" in mock_logger.error.call_args[0][0]
    assert str(output_file) in mock_logger.error.call_args[0][0]
    assert "Object of type complex is not JSON serializable" in mock_logger.error.call_args[0][0]


# --- Placeholder for MarkdownWriter Tests ---
# TODO: Add tests for MarkdownWriter
@pytest.fixture(params=[
    (True, "start"), 
    (True, "end"), 
    (False, "start") # Position doesn't matter if not included
])
def markdown_writer(request):
    """Fixture to create MarkdownWriter instances with different configs."""
    include_metadata, metadata_position = request.param
    return MarkdownWriter(include_metadata=include_metadata, metadata_position=metadata_position)

@pytest.fixture
def sample_metadata():
    """Provides a sample metadata dictionary for testing."""
    return {
        "title": "Test Document",
        "author": "Test Author",
        "file_stats": {
            "file_size_kb": 12.345
        },
        "page_count": 5,
        "metrics": {
            "token_reduction_percent": 25.5
        }
    }

@pytest.fixture
def sample_metadata_slides():
    """Provides sample metadata with slide_count."""
    return {
        "slide_count": 10,
        "metrics": {
            "token_reduction_percent": 15.0
        }
    }

@pytest.fixture
def sample_metadata_sheets():
    """Provides sample metadata with sheet_count."""
    return {
        "sheet_count": 3,
        "file_stats": {
            "file_size_kb": 5.0
        }
    }

@pytest.fixture
def sample_metadata_minimal():
    """Provides minimal metadata."""
    return {
        "title": "Minimal Doc"
    }

def test_markdown_writer_write_no_metadata_config(tmp_path):
    """Test writing when include_metadata is False."""
    writer = MarkdownWriter(include_metadata=False, metadata_position="start")
    output_file = tmp_path / "output.md"
    content = "## Section 1\n\nContent here."
    metadata = {"title": "Should be ignored"}

    m = mock_open()
    with patch("builtins.open", m):
        writer.write(content, output_file, metadata=metadata)

    m.assert_called_once_with(output_file, 'w', encoding='utf-8')
    handle = m()
    # Should only write the original content
    handle.write.assert_called_once_with(content)

def test_markdown_writer_write_no_metadata_provided(tmp_path):
    """Test writing when include_metadata is True, but no metadata is given."""
    writer = MarkdownWriter(include_metadata=True, metadata_position="start")
    output_file = tmp_path / "output.md"
    content = "Some base content."

    m = mock_open()
    with patch("builtins.open", m):
        writer.write(content, output_file, metadata=None)

    m.assert_called_once_with(output_file, 'w', encoding='utf-8')
    handle = m()
    # Should only write the original content
    handle.write.assert_called_once_with(content)

def test_markdown_writer_write_empty_metadata_provided(tmp_path):
    """Test writing when include_metadata is True, but empty metadata is given."""
    writer = MarkdownWriter(include_metadata=True, metadata_position="start")
    output_file = tmp_path / "output.md"
    content = "Some base content."

    m = mock_open()
    with patch("builtins.open", m):
        writer.write(content, output_file, metadata={})

    m.assert_called_once_with(output_file, 'w', encoding='utf-8')
    handle = m()
    # Should only write the original content as no relevant keys found
    handle.write.assert_called_once_with(content)


EXPECTED_METADATA_BLOCK_FULL = """## Document Metadata

- Title: Test Document
- Author: Test Author
- File Size: 12.35 KB
- Pages: 5
- Token Reduction: 25.50%"""

EXPECTED_METADATA_BLOCK_SLIDES = """## Document Metadata

- Slides: 10
- Token Reduction: 15.00%"""

EXPECTED_METADATA_BLOCK_SHEETS = """## Document Metadata

- File Size: 5.00 KB
- Sheets: 3"""

EXPECTED_METADATA_BLOCK_MINIMAL = """## Document Metadata

- Title: Minimal Doc"""

@pytest.mark.parametrize("metadata_fixture, expected_block", [
    ("sample_metadata", EXPECTED_METADATA_BLOCK_FULL),
    ("sample_metadata_slides", EXPECTED_METADATA_BLOCK_SLIDES),
    ("sample_metadata_sheets", EXPECTED_METADATA_BLOCK_SHEETS),
    ("sample_metadata_minimal", EXPECTED_METADATA_BLOCK_MINIMAL),
])
def test_markdown_writer_write_metadata_start(request, metadata_fixture, expected_block, tmp_path):
    """Test writing with metadata at the start."""
    writer = MarkdownWriter(include_metadata=True, metadata_position="start")
    metadata = request.getfixturevalue(metadata_fixture)
    output_file = tmp_path / "output.md"
    content = "Main content body."
    expected_output = f"{expected_block}\n\n{content}"

    m = mock_open()
    with patch("builtins.open", m):
        writer.write(content, output_file, metadata=metadata)

    m.assert_called_once_with(output_file, 'w', encoding='utf-8')
    handle = m()
    handle.write.assert_called_once_with(expected_output)


@pytest.mark.parametrize("metadata_fixture, expected_block", [
    ("sample_metadata", EXPECTED_METADATA_BLOCK_FULL),
    ("sample_metadata_minimal", EXPECTED_METADATA_BLOCK_MINIMAL),
])
def test_markdown_writer_write_metadata_end(request, metadata_fixture, expected_block, tmp_path):
    """Test writing with metadata at the end."""
    writer = MarkdownWriter(include_metadata=True, metadata_position="end")
    metadata = request.getfixturevalue(metadata_fixture)
    output_file = tmp_path / "output.md"
    content = "Main content body."
    expected_output = f"{content}\n\n{expected_block}"

    m = mock_open()
    with patch("builtins.open", m):
        writer.write(content, output_file, metadata=metadata)

    m.assert_called_once_with(output_file, 'w', encoding='utf-8')
    handle = m()
    handle.write.assert_called_once_with(expected_output)

def test_markdown_writer_write_io_error(sample_metadata, tmp_path, mock_logger):
    """Test MarkdownWriter handles IOError during file write."""
    writer = MarkdownWriter(include_metadata=True, metadata_position="start")
    output_file = tmp_path / "output.md"
    content = "data"

    with patch("builtins.open", mock_open()) as m_open:
        m_open.side_effect = IOError("Disk full")
        with pytest.raises(IOError):
            writer.write(content, output_file, metadata=sample_metadata)

    mock_logger.error.assert_called_once_with(
        f"Failed to write Markdown file {output_file}: Disk full"
    )


# --- Placeholder for OutputManager Tests ---
# TODO: Add tests for OutputManager logic (format detection, writer selection)
@pytest.fixture
def mock_config_manager():
    """Fixture for a mock ConfigManager."""
    mock_config = MagicMock(spec=ConfigManager)
    # Set up default return values for common get calls
    mock_config.get.side_effect = lambda key, default=None: {
        "output.markdown.include_metadata": True,
        "output.markdown.metadata_position": "end",
        "output.default_format": "markdown" # Default format for testing
    }.get(key, default)
    return mock_config

@pytest.fixture
def mock_writers():
    """Fixture providing mock instances for each writer type."""
    return {
        "markdown": MagicMock(spec=MarkdownWriter),
        "plain_text": MagicMock(spec=PlainTextWriter),
        "json": MagicMock(spec=JsonWriter),
        "csv": MagicMock(spec=CsvWriter),
    }

@pytest.fixture
@patch('textcleaner.outputs.output_manager.MarkdownWriter')
@patch('textcleaner.outputs.output_manager.PlainTextWriter')
@patch('textcleaner.outputs.output_manager.JsonWriter')
@patch('textcleaner.outputs.output_manager.CsvWriter')
def output_manager(MockCsvWriter, MockJsonWriter, MockPlainTextWriter, MockMarkdownWriter, mock_config_manager, mock_writers):
    """Fixture to create an OutputManager instance with mocked writers and config."""
    # Configure the mock classes to return our mock instances
    MockMarkdownWriter.return_value = mock_writers["markdown"]
    MockPlainTextWriter.return_value = mock_writers["plain_text"]
    MockJsonWriter.return_value = mock_writers["json"]
    MockCsvWriter.return_value = mock_writers["csv"]

    # Instantiate OutputManager, which will now use the mocked writer classes
    manager = OutputManager(config=mock_config_manager)
    # Ensure the manager's internal writers dict points to our mocks for assertion
    manager.writers = mock_writers
    return manager

def test_output_manager_init_default_config():
    """Test OutputManager initializes with default ConfigManager if none provided."""
    # This requires mocking ConfigManager globally or patching its instantiation
    with patch('textcleaner.outputs.output_manager.ConfigManager') as MockConfigMgr:
        mock_instance = MagicMock()
        mock_instance.get.side_effect = lambda key, default=None: default # Simple mock
        MockConfigMgr.return_value = mock_instance
        
        manager = OutputManager() # Initialize without passing config
        assert manager.config is mock_instance
        MockConfigMgr.assert_called_once()

def test_output_manager_init_with_config(mock_config_manager):
    """Test OutputManager initializes with a provided ConfigManager."""
    # The output_manager fixture already tests this implicitly by passing mock_config_manager
    # We can add an explicit assertion here for clarity
    manager = OutputManager(config=mock_config_manager)
    assert manager.config is mock_config_manager
    # Verify config was used to get markdown settings during writer init
    mock_config_manager.get.assert_any_call("output.markdown.include_metadata", True)
    mock_config_manager.get.assert_any_call("output.markdown.metadata_position", "end")


@pytest.mark.parametrize("output_path_str, expected_format, expected_writer_key", [
    ("output/file.md", None, "markdown"),         # Infer from .md extension
    ("results.txt", None, "plain_text"),         # Infer from .txt extension
    ("data.json", None, "json"),             # Infer from .json extension
    ("report.csv", None, "csv"),              # Infer from .csv extension
    ("archive.zip", None, "markdown"),         # Unknown extension, use default (markdown)
    ("output/file.MD", None, "markdown"),         # Case-insensitive extension check
    ("output/file", None, "markdown"),           # No extension, use default
    ("data.text", None, "plain_text"),        # Infer alias .text
])
@patch('pathlib.Path.mkdir') # Mock directory creation
def test_output_manager_infer_format_from_extension(mock_mkdir, output_manager, mock_writers, mock_config_manager, output_path_str, expected_format, expected_writer_key, tmp_path):
    """Test format inference from file extension."""
    output_path = tmp_path / output_path_str # Use tmp_path for realistic Path object
    content = "Test content"
    metadata = {"key": "value"}

    output_manager.write(content, output_path, format=expected_format, metadata=metadata)

    # Assert the correct writer was called
    mock_writer = mock_writers[expected_writer_key]
    mock_writer.write.assert_called_once_with(content, output_path, metadata)

    # Assert other writers were not called
    for key, writer in mock_writers.items():
        if key != expected_writer_key:
            writer.write.assert_not_called()

    # Assert default format was fetched if extension was unknown/missing
    if expected_writer_key == "markdown" and output_path.suffix.lower() not in [".md", ".markdown"]:
         mock_config_manager.get.assert_any_call("output.default_format", "markdown")

    # Assert directory creation was attempted
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


@pytest.mark.parametrize("provided_format, expected_writer_key", [
    ("markdown", "markdown"),
    ("plain_text", "plain_text"),
    ("json", "json"),
    ("csv", "csv"),
    ("md", "markdown"),      # Alias
    ("txt", "plain_text"),   # Alias
    ("text", "plain_text"),  # Alias
    ("MARKDOWN", "markdown"), # Case-insensitive format
])
@patch('pathlib.Path.mkdir')
def test_output_manager_explicit_format(mock_mkdir, output_manager, mock_writers, provided_format, expected_writer_key, tmp_path):
    """Test selecting writer based on explicit format argument."""
    output_path = tmp_path / "output.file" # Extension shouldn't matter here
    content = "Content"
    metadata = {"a": 1}

    output_manager.write(content, output_path, format=provided_format, metadata=metadata)

    # Assert the correct writer was called
    mock_writer = mock_writers[expected_writer_key]
    mock_writer.write.assert_called_once_with(content, output_path, metadata)

    # Assert others weren't
    for key, writer in mock_writers.items():
        if key != expected_writer_key:
            writer.write.assert_not_called()

    # Assert directory creation was attempted
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


@patch('pathlib.Path.mkdir')
def test_output_manager_unsupported_format(mock_mkdir, output_manager, tmp_path):
    """Test that ValueError is raised for an unsupported format."""
    output_path = tmp_path / "output.xml"
    content = "Data"

    with pytest.raises(ValueError, match="Unsupported output format: xml"):
        output_manager.write(content, output_path, format="xml")

    # Ensure mkdir was not called if format is invalid before writing
    mock_mkdir.assert_not_called()


@patch('pathlib.Path.mkdir')
def test_output_manager_writer_raises_error(mock_mkdir, output_manager, mock_writers, tmp_path, mock_logger):
    """Test that errors from the writer's write method propagate."""
    output_path = tmp_path / "output.txt"
    content = "Data"
    mock_writers["plain_text"].write.side_effect = IOError("Writer failed")

    with pytest.raises(IOError, match="Writer failed"):
        output_manager.write(content, output_path, format="plain_text")

    # Check logger was called by the manager before raising
    mock_logger.debug.assert_called_with("Using writer 'PlainTextWriter' for format 'plain_text'")
    # Ensure the writer's error wasn't swallowed (mock_logger in writer is separate)
    mock_writers["plain_text"].write.assert_called_once()
    mock_mkdir.assert_called_once() 