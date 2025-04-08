"""
Tests for the TextProcessor class using mocks
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from textcleaner.core.processor import TextProcessor, ProcessingResult
from textcleaner.core.file_registry import FileTypeRegistry
from textcleaner.converters.base import ConverterRegistry
from textcleaner.processors.processor_pipeline import ProcessorPipeline
from textcleaner.outputs.output_manager import OutputManager
from textcleaner.utils.security import SecurityUtils


@pytest.fixture
def mock_components():
    """Create mock components for testing TextProcessor"""
    # Create mock components
    mock_converter_registry = Mock(spec=ConverterRegistry)
    mock_processor_pipeline = Mock(spec=ProcessorPipeline)
    mock_file_registry = Mock(spec=FileTypeRegistry)
    mock_output_manager = Mock(spec=OutputManager)
    mock_security = Mock(spec=SecurityUtils)
    
    # Configure common mock behaviors
    mock_file_registry.should_process_file.return_value = True
    mock_file_registry.get_default_extension.return_value = "txt"
    
    mock_security.validate_path.return_value = (True, None)
    mock_security.validate_output_path.return_value = (True, None)
    mock_security.check_file_permissions.return_value = (True, None)
    
    return {
        "converter_registry": mock_converter_registry,
        "processor_pipeline": mock_processor_pipeline,
        "file_registry": mock_file_registry,
        "output_manager": mock_output_manager,
        "security": mock_security
    }


@pytest.fixture
def processor(mock_components):
    """Create a TextProcessor with mock components"""
    # Use a mock for the config factory to avoid actual config loading
    with patch("textcleaner.config.config_factory.ConfigFactory") as mock_config_factory:
        # Configure mock config factory
        mock_config = Mock()
        mock_config.get.return_value = "mock_value"
        mock_config_factory.return_value.create_config.return_value = mock_config
        
        # Create processor with mock components
        processor = TextProcessor(
            converter_registry=mock_components["converter_registry"],
            processor_pipeline=mock_components["processor_pipeline"],
            file_registry=mock_components["file_registry"],
            output_manager=mock_components["output_manager"],
            security_utils=mock_components["security"]
        )
        
        return processor


def test_process_file_success(processor, mock_components, temp_directory):
    """Test successful file processing"""
    # Create a test file
    input_file = temp_directory / "test.txt"
    input_file.write_text("Test content")
    
    output_file = temp_directory / "output" / "test.txt"
    
    # Configure mocks for success scenario
    mock_converter = Mock()
    mock_converter.convert.return_value = ("Extracted content", {"metadata": "value"})
    mock_components["converter_registry"].find_converter.return_value = mock_converter
    
    mock_components["processor_pipeline"].process.return_value = "Processed content"
    
    # Process the file
    result = processor.process_file(input_file, output_file)
    
    # Verify the result
    assert result.success is True
    assert result.input_path == input_file
    assert result.output_path == output_file
    
    # Verify component interactions
    mock_components["converter_registry"].find_converter.assert_called_once_with(input_file)
    mock_converter.convert.assert_called_once_with(input_file)
    mock_components["processor_pipeline"].process.assert_called_once()
    mock_components["output_manager"].write.assert_called_once()


def test_process_file_no_converter(processor, mock_components, temp_directory):
    """Test file processing when no converter is found"""
    # Create a test file
    input_file = temp_directory / "test.txt"
    input_file.write_text("Test content")
    
    # Configure mocks for no converter scenario
    mock_components["converter_registry"].find_converter.return_value = None
    
    # Process the file
    result = processor.process_file(input_file)
    
    # Verify the result
    assert result.success is False
    assert "No converter found" in result.error
    assert result.input_path == input_file
    
    # Verify component interactions
    mock_components["converter_registry"].find_converter.assert_called_once_with(input_file)
    mock_components["processor_pipeline"].process.assert_not_called()
    mock_components["output_manager"].write.assert_not_called()


def test_process_file_security_validation(processor, mock_components, temp_directory):
    """Test file processing with security validation failures"""
    # Create a test file
    input_file = temp_directory / "test.txt"
    input_file.write_text("Test content")
    
    # Configure mocks for security validation failure
    mock_components["security"].validate_path.return_value = (False, "Security validation failed")
    
    # Process the file
    result = processor.process_file(input_file)
    
    # Verify the result
    assert result.success is False
    assert "Security validation failed" in result.error
    
    # Verify component interactions
    mock_components["converter_registry"].find_converter.assert_not_called()
    mock_components["processor_pipeline"].process.assert_not_called()
    mock_components["output_manager"].write.assert_not_called()


def test_process_file_converter_exception(processor, mock_components, temp_directory):
    """Test file processing when converter raises an exception"""
    # Create a test file
    input_file = temp_directory / "test.txt"
    input_file.write_text("Test content")
    
    # Configure mocks for exception scenario
    mock_converter = Mock()
    mock_converter.convert.side_effect = Exception("Conversion error")
    mock_components["converter_registry"].find_converter.return_value = mock_converter
    
    # Process the file
    result = processor.process_file(input_file)
    
    # Verify the result
    assert result.success is False
    assert "Conversion error" in result.error
    
    # Verify component interactions
    mock_components["converter_registry"].find_converter.assert_called_once_with(input_file)
    mock_converter.convert.assert_called_once_with(input_file)
    mock_components["processor_pipeline"].process.assert_not_called()
    mock_components["output_manager"].write.assert_not_called()


@patch('textcleaner.utils.parallel.ParallelProcessor')
def test_process_directory_parallel(mock_parallel_cls, processor, mock_components, temp_directory):
    """Test parallel directory processing"""
    # Create directory structure
    input_dir = temp_directory / "input"
    input_dir.mkdir()
    
    # Create sample files
    file1 = input_dir / "file1.txt"
    file1.write_text("Content 1")
    
    file2 = input_dir / "file2.txt"
    file2.write_text("Content 2")
    
    # Configure mocks
    mock_parallel = Mock()
    mock_parallel_cls.return_value = mock_parallel
    
    # Mock parallel processing results
    result1 = ProcessingResult(file1, Path("output/file1.txt"), True)
    result2 = ProcessingResult(file2, Path("output/file2.txt"), True)
    
    # Mock processing results
    mock_parallel.process_items.return_value = [
        MagicMock(success=True, result=result1),
        MagicMock(success=True, result=result2)
    ]
    
    # Configure file finding
    with patch.object(processor, '_find_files_to_process', return_value=[file1, file2]):
        # Process the directory
        results = processor.process_directory_parallel(input_dir)
        
        # Verify results
        assert len(results) == 2
        assert all(r.success for r in results)
        
        # Verify parallel processor was used
        mock_parallel.process_items.assert_called_once()
        
        # First arg should be a list of (file_path, output_path) tuples
        args = mock_parallel.process_items.call_args[1]['items']
        assert len(args) == 2
        assert isinstance(args[0][0], Path)  # First item should be input file
        assert isinstance(args[0][1], Path)  # Second item should be output file
