"""Unit tests for the CSVConverter."""

import pytest
from pathlib import Path
from textcleaner.converters.csv_converter import CSVConverter
from textcleaner.config.config_manager import ConfigManager

# Fixture for creating temporary CSV files
@pytest.fixture
def temp_csv_file(tmp_path: Path):
    def _create_csv(content: str, filename="test.csv") -> Path:
        file_path = tmp_path / filename
        file_path.write_text(content)
        return file_path
    return _create_csv

# Fixture for CSVConverter instance
@pytest.fixture
def csv_converter():
    return CSVConverter(config=ConfigManager()) # Use default config for basic tests

# Test cases
def test_csv_converter_basic(csv_converter: CSVConverter, temp_csv_file):
    """Test basic CSV conversion with header included."""
    content = "Header1,Header2\nValue1,Value2\nValue A,Value B"
    file_path = temp_csv_file(content)
    
    raw_content, metadata = csv_converter.convert(file_path)
    
    expected_content = "Header1 Header2\nValue1 Value2\nValue A Value B"
    assert raw_content == expected_content
    assert metadata['converter'] == 'CSVConverter'
    assert metadata['original_rows'] == 3
    assert metadata['processed_rows'] == 3
    assert metadata['included_header'] is True
    assert metadata.get('header') is None
    assert metadata.get('truncated') is None

def test_csv_converter_no_header(temp_csv_file):
    """Test CSV conversion with header excluded via config."""
    config_data = {
        "formats": {
            "csv": {"include_header": False}
        }
    }
    config = ConfigManager(initial_config=config_data)
    converter = CSVConverter(config=config)
    
    content = "Header1,Header2\nValue1,Value2"
    file_path = temp_csv_file(content)
    
    raw_content, metadata = converter.convert(file_path)
    
    expected_content = "Value1 Value2"
    assert raw_content == expected_content
    assert metadata['original_rows'] == 2
    assert metadata['processed_rows'] == 1
    assert metadata['included_header'] is False
    assert metadata['header'] == ["Header1", "Header2"]

def test_csv_converter_different_delimiter(temp_csv_file):
    """Test CSV conversion with a different delimiter."""
    config_data = {
        "formats": {
            "csv": {"delimiter": ";"}
        }
    }
    config = ConfigManager(initial_config=config_data)
    converter = CSVConverter(config=config)
    
    content = "Header1;Header2\nValue1;Value2"
    file_path = temp_csv_file(content)
    
    raw_content, metadata = converter.convert(file_path)
    
    expected_content = "Header1 Header2\nValue1 Value2"
    assert raw_content == expected_content
    assert metadata['delimiter'] == ";"

def test_csv_converter_max_rows(temp_csv_file):
    """Test CSV conversion with max_rows limit."""
    config_data = {
        "formats": {
            "csv": {"max_rows": 2} # Include header + 1 data row
        }
    }
    config = ConfigManager(initial_config=config_data)
    converter = CSVConverter(config=config)
    
    content = "H1,H2\nR1C1,R1C2\nR2C1,R2C2\nR3C1,R3C2"
    file_path = temp_csv_file(content)
    
    raw_content, metadata = converter.convert(file_path)
    
    expected_content = "H1 H2\nR1C1 R1C2" # Only header and first data row
    assert raw_content == expected_content
    assert metadata['original_rows'] == 3 # Should stop reading after max_rows, but original count includes the row that triggered break
    assert metadata['processed_rows'] == 2
    assert metadata['truncated'] is True

def test_csv_converter_empty_file(csv_converter: CSVConverter, temp_csv_file):
    """Test conversion of an empty CSV file."""
    file_path = temp_csv_file("")
    raw_content, metadata = csv_converter.convert(file_path)
    assert raw_content == ""
    assert metadata['original_rows'] == 0
    assert metadata['processed_rows'] == 0

def test_csv_converter_file_not_found(csv_converter: CSVConverter):
    """Test conversion attempt on a non-existent file."""
    with pytest.raises(FileNotFoundError):
        csv_converter.convert("non_existent_file.csv")

def test_csv_converter_unsupported_extension(csv_converter: CSVConverter, tmp_path: Path):
    """Test handling of unsupported file extensions."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("this is not a csv")
    with pytest.raises(ValueError):
        csv_converter.convert(file_path)

# TODO: Add tests for quotechar, different encodings, CSV errors (malformed rows) 