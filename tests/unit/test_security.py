"""
Tests for security utilities
"""

import os
import tempfile
from pathlib import Path
import pytest

from textcleaner.utils.security import SecurityUtils


@pytest.fixture
def security_utils():
    """Create a SecurityUtils instance for testing"""
    return SecurityUtils()


def test_validate_path_normal(security_utils, temp_directory):
    """Test validation of normal paths"""
    # Create a test file
    test_file = temp_directory / "test.txt"
    test_file.write_text("Test content")
    
    # Test valid file
    is_valid, error = security_utils.validate_path(test_file)
    assert is_valid
    assert error is None


def test_validate_path_nonexistent(security_utils, temp_directory):
    """Test validation of nonexistent paths"""
    nonexistent_file = temp_directory / "nonexistent.txt"
    
    is_valid, error = security_utils.validate_path(nonexistent_file)
    assert not is_valid
    assert "does not exist" in error


def test_validate_path_directory_traversal(security_utils, temp_directory):
    """Test validation catches directory traversal attempts"""
    traversal_path = temp_directory / ".." / "some_file.txt"
    
    is_valid, error = security_utils.validate_path(traversal_path)
    assert not is_valid
    assert "parent directory reference" in error


def test_validate_path_symlink(security_utils, temp_directory):
    """Test validation catches symbolic links"""
    # Create a file
    real_file = temp_directory / "real_file.txt"
    real_file.write_text("Real file content")
    
    # Create a symlink to it
    symlink_file = temp_directory / "symlink_file.txt"
    try:
        symlink_file.symlink_to(real_file)
        
        # Test validation
        is_valid, error = security_utils.validate_path(symlink_file)
        assert not is_valid
        assert "symbolic link" in error
        
    except OSError:
        # Some environments don't allow symlinks creation
        pytest.skip("Symlink creation not supported in this environment")


def test_check_file_permissions(security_utils, temp_directory):
    """Test file permission checking"""
    # Create a test file
    test_file = temp_directory / "permissions_test.txt"
    test_file.write_text("Test content")
    
    # Test with read permissions
    has_permission, error = security_utils.check_file_permissions(test_file)
    assert has_permission
    assert error is None
    
    # Test with write requirement
    has_permission, error = security_utils.check_file_permissions(test_file, require_write=True)
    assert has_permission
    assert error is None


def test_secure_temp_file(security_utils):
    """Test secure temporary file creation"""
    # Create temp file
    temp_path, error = security_utils.create_secure_temp_file(prefix="test_")
    
    # Verify creation succeeded
    assert error is None
    assert temp_path is not None
    assert temp_path.exists()
    assert temp_path.name.startswith("test_")
    
    # Clean up
    try:
        os.remove(temp_path)
    except:
        pass


def test_secure_delete_file(security_utils, temp_directory):
    """Test secure file deletion"""
    # Create a test file
    test_file = temp_directory / "file_to_delete.txt"
    test_file.write_text("This file will be deleted")
    
    # Verify file exists
    assert test_file.exists()
    
    # Delete file
    success, error = security_utils.secure_delete_file(test_file)
    
    # Verify deletion
    assert success
    assert error is None
    assert not test_file.exists()


def test_validate_output_path(security_utils, temp_directory):
    """Test validation of output paths"""
    # Normal output path
    output_path = temp_directory / "output.txt"
    is_valid, error = security_utils.validate_output_path(output_path)
    assert is_valid
    assert error is None
    
    # Output path in nonexistent directory
    nested_path = temp_directory / "nested" / "output.txt"
    is_valid, error = security_utils.validate_output_path(nested_path)
    assert is_valid  # Should be valid as it creates parent directories
    
    # Verify directory was created
    assert nested_path.parent.exists()
