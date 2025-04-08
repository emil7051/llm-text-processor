"""
Tests for the enhanced security utilities
"""

import os
import tempfile
from pathlib import Path
import platform
import sys
import pytest

# Add the parent directory to the Python path to find the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.textcleaner.utils.security import SecurityUtils


@pytest.fixture
def security_utils():
    """Create a SecurityUtils instance for testing"""
    return SecurityUtils()


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.mark.security
def test_comprehensive_file_validation(security_utils, temp_directory):
    """Test comprehensive file validation"""
    # Create a test file
    test_file = temp_directory / "validation_test.txt"
    test_file.write_text("Test content for comprehensive validation")
    
    # Test comprehensive validation
    is_valid, error = security_utils.comprehensive_file_validation(test_file)
    assert is_valid
    assert error is None


@pytest.mark.security
def test_validate_file_size(security_utils, temp_directory):
    """Test file size validation"""
    # Create a small test file
    small_file = temp_directory / "small_file.txt"
    small_file.write_text("Small file content")
    
    # Create a larger test file (5MB)
    large_file = temp_directory / "large_file.txt"
    with open(large_file, 'wb') as f:
        f.write(b'x' * (5 * 1024 * 1024))
    
    # Test small file validation
    is_valid, error = security_utils.validate_file_size(small_file)
    assert is_valid
    assert error is None
    
    # Test large file validation (should still pass the default limit)
    is_valid, error = security_utils.validate_file_size(large_file)
    assert is_valid
    assert error is None
    
    # Create an extremely large file that exceeds specific file type limit
    # Temporarily modify size limits for testing
    original_limit = security_utils.file_size_limits['txt']
    try:
        # Set a very low limit for txt files for testing
        security_utils.file_size_limits['txt'] = 1 * 1024 * 1024  # 1MB
        
        # Now test again with the lower limit
        is_valid, error = security_utils.validate_file_size(large_file)
        assert not is_valid
        assert "too large" in error
    finally:
        # Restore original limit
        security_utils.file_size_limits['txt'] = original_limit


@pytest.mark.security
def test_validate_mime_type(security_utils, temp_directory):
    """Test MIME type validation"""
    # Create files with different extensions
    txt_file = temp_directory / "test.txt"
    txt_file.write_text("Text file content")
    
    html_file = temp_directory / "test.html"
    html_file.write_text("<html><body>HTML content</body></html>")
    
    exe_file = temp_directory / "test.exe"
    exe_file.write_text("Not a real executable")
    
    # Test validation of allowed MIME types
    is_valid, error = security_utils.validate_mime_type(txt_file)
    assert is_valid
    assert error is None
    
    is_valid, error = security_utils.validate_mime_type(html_file)
    assert is_valid
    assert error is None
    
    # Test validation of disallowed MIME types
    is_valid, error = security_utils.validate_mime_type(exe_file)
    assert not is_valid
    assert "dangerous extension" in error


@pytest.mark.security
def test_sanitize_text_content(security_utils):
    """Test text content sanitization"""
    # Test with normal text
    normal_text = "This is normal text."
    sanitized = security_utils.sanitize_text_content(normal_text)
    assert sanitized == normal_text
    
    # Test with HTML script tags
    script_text = "Text with <script>alert('XSS')</script> script."
    sanitized = security_utils.sanitize_text_content(script_text)
    assert "<script>" not in sanitized
    assert "[SCRIPT REMOVED]" in sanitized
    
    # Test with iframe
    iframe_text = "Text with <iframe src='malicious.html'></iframe> iframe."
    sanitized = security_utils.sanitize_text_content(iframe_text)
    assert "<iframe" not in sanitized
    assert "[IFRAME REMOVED]" in sanitized
    
    # Test with javascript: URL
    js_url_text = "Text with javascript:alert('XSS') URL."
    sanitized = security_utils.sanitize_text_content(js_url_text)
    assert "javascript:" not in sanitized
    assert "[JS REMOVED]:" in sanitized


@pytest.mark.security
def test_compute_file_hash(security_utils, temp_directory):
    """Test file hash computation"""
    # Create a test file with known content
    test_file = temp_directory / "hash_test.txt"
    test_file.write_text("This is a test file for hash computation.")
    
    # Compute hash
    hash_value, error = security_utils.compute_file_hash(test_file)
    
    # Verify hash computation
    assert error is None
    assert hash_value is not None
    assert len(hash_value) == 64  # SHA-256 hash is 64 hex characters
    
    # Compute hash again to verify consistency
    hash_value2, _ = security_utils.compute_file_hash(test_file)
    assert hash_value == hash_value2
    
    # Modify file and check hash changes
    test_file.write_text("Modified content.")
    hash_value3, _ = security_utils.compute_file_hash(test_file)
    assert hash_value != hash_value3


@pytest.mark.security
def test_validate_file_integrity(security_utils, temp_directory):
    """Test file integrity validation"""
    # Create a test file
    test_file = temp_directory / "integrity_test.txt"
    test_file.write_text("Test content for integrity validation.")
    
    # Compute hash
    hash_value, _ = security_utils.compute_file_hash(test_file)
    
    # Validate with correct hash
    is_valid, error = security_utils.validate_file_integrity(test_file, hash_value)
    assert is_valid
    assert error is None
    
    # Validate with incorrect hash
    incorrect_hash = "a" * 64
    is_valid, error = security_utils.validate_file_integrity(test_file, incorrect_hash)
    assert not is_valid
    assert "Hash mismatch" in error


@pytest.mark.security
def test_secure_delete_file(security_utils, temp_directory):
    """Test secure file deletion with overwrite"""
    # Create a test file
    test_file = temp_directory / "secure_delete_test.txt"
    test_content = "This content should be securely deleted."
    test_file.write_text(test_content)
    
    # Verify file exists and contains expected content
    assert test_file.exists()
    assert test_file.read_text() == test_content
    
    # Securely delete the file
    success, error = security_utils.secure_delete_file(test_file)
    
    # Verify deletion
    assert success
    assert error is None
    assert not test_file.exists()


@pytest.mark.skipif(platform.system() == "Windows", reason="File permissions test not applicable on Windows")
@pytest.mark.security
def test_check_file_permissions_unix(security_utils, temp_directory):
    """Test file permission checks on Unix-like systems"""
    # Skip on Windows as chmod doesn't work the same way
    if platform.system() == "Windows":
        pytest.skip("Test not applicable on Windows")
    
    # Create a test file
    test_file = temp_directory / "permissions_test.txt"
    test_file.write_text("Test content for permission checks.")
    
    # Make file read-only
    test_file.chmod(0o444)
    
    # Check read permission (should pass)
    has_permission, error = security_utils.check_file_permissions(test_file)
    assert has_permission
    assert error is None
    
    # Check write permission (should fail for read-only file)
    has_permission, error = security_utils.check_file_permissions(test_file, require_write=True)
    assert not has_permission
    assert "No write permission" in error
    
    # Reset permissions
    test_file.chmod(0o644)
    
    # Check write permission again (should now pass)
    has_permission, error = security_utils.check_file_permissions(test_file, require_write=True)
    assert has_permission
    assert error is None
