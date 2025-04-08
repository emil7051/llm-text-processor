"""Enhanced security utilities for the TextCleaner."""

import os
import re
import stat
import tempfile
import secrets
import shutil
import platform
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Set, Any, Union
import io

from textcleaner.utils.logging_config import get_logger


class SecurityUtils:
    """Enhanced utilities for secure file handling and validation."""
    
    def __init__(self):
        """Initialize security utilities."""
        self.logger = get_logger(__name__)
        
        # Initialize MIME types
        mimetypes.init()
        
        # Potentially dangerous file extensions
        self.dangerous_extensions = [
            '.exe', '.dll', '.so', '.sh', '.bat', '.cmd', '.app', 
            '.js', '.vbs', '.ps1', '.py', '.jar', '.com', '.msi',
            '.scr', '.php', '.asp', '.aspx', '.cgi', '.pl'
        ]
        
        # Allowed MIME types for text processing
        self.allowed_mime_types = {
            'text/plain', 'text/html', 'text/markdown', 'text/csv',
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/rtf', 'application/json', 'application/xml'
        }
        
        # File size limits (in bytes)
        self.file_size_limits = {
            'default': 300 * 1024 * 1024,  # 100MB general limit
            'pdf': 50 * 1024 * 1024,       # 50MB for PDFs
            'docx': 30 * 1024 * 1024,      # 30MB for Word docs
            'xlsx': 20 * 1024 * 1024,      # 20MB for Excel
            'txt': 200 * 1024 * 1024       # 200MB for plain text
        }
        
        # Locations that should be treated with caution
        self.sensitive_paths = [
            '/etc', '/var', '/usr/bin', '/usr/sbin', '/bin', '/sbin',
            '/System', '/Library', '/private', '/Users/*/Library',
            'C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)',
            'C:\\Users\\*\\AppData'
        ]
        
        # Patterns for potential security issues in text content
        self.suspicious_patterns = [
            # SQL injection patterns
            r'(?i)(\%27)|(\')|(\-\-)|(\%23)|(#)',
            r'(?i)((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))',
            # Command injection patterns
            r'(?i)(\&\#)|(\\)|(\|)|(\;)',
            # Path traversal
            r'\.\.[\\/]',
            # Script tags
            r'(?i)<script.*?>.*?</script>',
            # Other potentially malicious HTML
            r'(?i)<iframe.*?>.*?</iframe>',
            r'(?i)javascript\s*:',
            # Base64 executable content
            r'(?i)base64.*(?:exe|dll|bat|sh|cmd|vbs)'
        ]
    
    def validate_path(self, path: Path) -> Tuple[bool, Optional[str]]:
        """Validate that a path is safe to process.
        
        Args:
            path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        path_str = str(path)
        
        # Check for directory traversal attempts
        if '..' in path_str:
            error = f"Path contains parent directory reference: {path}"
            self.logger.warning(error)
            return False, error
        
        # Check if path exists
        if not path.exists():
            error = f"Path does not exist: {path}"
            self.logger.debug(error)
            return False, error
        
        # Check if path is a symlink (which could be a security risk)
        if path.is_symlink():
            error = f"Path is a symbolic link: {path}"
            self.logger.warning(error)
            return False, error
        
        # Check if path is in a sensitive location using glob-style matching
        for sensitive_path in self.sensitive_paths:
            if '*' in sensitive_path:
                # Escape special regex characters except the asterisk
                pattern = sensitive_path
                pattern = pattern.replace('\\', '\\\\')
                pattern = pattern.replace('.', '\\.')
                pattern = pattern.replace('+', '\\+')
                pattern = pattern.replace('?', '\\?')
                pattern = pattern.replace('|', '\\|')
                pattern = pattern.replace('{', '\\{')
                pattern = pattern.replace('}', '\\}')
                pattern = pattern.replace('(', '\\(')
                pattern = pattern.replace(')', '\\)')
                pattern = pattern.replace('[', '\\[')
                pattern = pattern.replace(']', '\\]')
                pattern = pattern.replace('$', '\\$')
                pattern = pattern.replace('^', '\\^')
                # Replace * with .* for regex
                pattern = pattern.replace('*', '.*')
                
                try:
                    if re.match(pattern, path_str):
                        error = f"Path is in a sensitive location: {path}"
                        self.logger.warning(error)
                        return False, error
                except re.error:
                    # If there's a regex error, log it but continue processing
                    self.logger.warning(f"Invalid regex pattern for path validation: {pattern}")
            elif path_str.startswith(sensitive_path):
                error = f"Path is in a sensitive location: {path}"
                self.logger.warning(error)
                return False, error
        
        # Check if file has a potentially dangerous extension
        if path.is_file() and path.suffix.lower() in self.dangerous_extensions:
            error = f"File has a potentially dangerous extension: {path}"
            self.logger.warning(error)
            return False, error
        
        return True, None
    
    def validate_file_size(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate that a file is not too large to safely process.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path.is_file():
            return True, None  # Not a file, so size check not applicable
        
        # Get file size
        try:
            file_size = file_path.stat().st_size
        except Exception as e:
            error = f"Could not determine file size for {file_path}: {str(e)}"
            self.logger.error(error)
            return False, error
        
        # Get the appropriate size limit based on file extension
        ext = file_path.suffix.lower().lstrip('.')
        size_limit = self.file_size_limits.get(ext, self.file_size_limits['default'])
        
        # Check against size limit
        if file_size > size_limit:
            error = f"File is too large to safely process: {file_path} ({file_size} bytes, limit is {size_limit} bytes)"
            self.logger.warning(error)
            return False, error
        
        return True, None
    
    def check_file_permissions(self, file_path: Path, 
                              require_write: bool = False) -> Tuple[bool, Optional[str]]:
        """Check if we have appropriate permissions to read/write the file.
        
        Args:
            file_path: Path to the file
            require_write: Whether write permission is required
            
        Returns:
            Tuple of (has_permission, error_message)
        """
        # Check read permission
        if not os.access(file_path, os.R_OK):
            error = f"No read permission for file: {file_path}"
            self.logger.warning(error)
            return False, error
        
        # Check write permission if required
        if require_write and not os.access(file_path, os.W_OK):
            error = f"No write permission for file: {file_path}"
            self.logger.warning(error)
            return False, error
        
        # On Unix-like systems, check for executable bit on non-executable files
        if platform.system() != "Windows" and file_path.is_file():
            mode = os.stat(file_path).st_mode
            if mode & stat.S_IEXEC:
                self.logger.warning(f"Warning: File has executable permission: {file_path}")
                # We don't fail here, just warn
        
        return True, None
    
    def validate_mime_type(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate that a file has an allowed MIME type.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            if mime_type is None:
                # If MIME type can't be determined, we check the extension
                ext = file_path.suffix.lower()
                if ext in self.dangerous_extensions:
                    error = f"File has a potentially dangerous extension: {file_path}"
                    self.logger.warning(error)
                    return False, error
                # If extension is unknown but not dangerous, allow it
                return True, None
            
            if mime_type not in self.allowed_mime_types:
                error = f"File has disallowed MIME type: {file_path} ({mime_type})"
                self.logger.warning(error)
                return False, error
            
            return True, None
        except Exception as e:
            error = f"Error determining MIME type for {file_path}: {str(e)}"
            self.logger.error(error)
            return False, error
    
    def validate_output_path(self, output_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate that an output path is safe to write to.
        
        Args:
            output_path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check parent directory
        parent_dir = output_path.parent
        
        # Make sure parent directory exists or can be created
        if not parent_dir.exists():
            try:
                parent_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                error = f"Cannot create directory for output: {parent_dir}, error: {str(e)}"
                self.logger.error(error)
                return False, error
        
        # Check write permission on parent directory
        if not os.access(parent_dir, os.W_OK):
            error = f"No write permission for output directory: {parent_dir}"
            self.logger.error(error)
            return False, error
        
        # Check if file exists and is writable
        if output_path.exists() and not os.access(output_path, os.W_OK):
            error = f"Output file exists but is not writable: {output_path}"
            self.logger.error(error)
            return False, error
        
        # Check for suspicious characters in filename
        filename = output_path.name
        if re.search(r'[<>:"|?*\x00-\x1F]', filename):
            error = f"Output filename contains invalid characters: {filename}"
            self.logger.error(error)
            return False, error
        
        return True, None
    
    def create_secure_temp_file(self, prefix: str = "llm_proc_", 
                               suffix: str = None, 
                               dir: Optional[str] = None) -> Tuple[Path, Optional[str]]:
        """Create a secure temporary file.
        
        Args:
            prefix: Prefix for the temp file name
            suffix: Suffix (extension) for the temp file
            dir: Directory to create the temp file in
            
        Returns:
            Tuple of (temp_file_path, error_message)
        """
        try:
            # Add randomness to the prefix for additional security
            random_suffix = secrets.token_hex(4)
            secure_prefix = f"{prefix}{random_suffix}_"
            
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                prefix=secure_prefix,
                suffix=suffix,
                dir=dir
            )
            temp_file.close()  # Close the file but don't delete it
            temp_path = Path(temp_file.name)
            
            # Set strict permissions: user read/write only
            if platform.system() != "Windows":
                os.chmod(temp_path, 0o600)
                
            self.logger.debug(f"Created secure temporary file: {temp_path}")
            return temp_path, None
        except Exception as e:
            error = f"Failed to create temporary file: {str(e)}"
            self.logger.error(error)
            return None, error
    
    def secure_delete_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Securely delete a file with overwrite.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if file_path.exists():
                # Get file size
                file_size = file_path.stat().st_size
                
                # For small-to-medium files (< 100MB), perform secure deletion with overwrite
                if file_size < 100 * 1024 * 1024:  # 100MB
                    # Overwrite file with random data before deletion
                    with open(file_path, 'wb') as f:
                        f.write(os.urandom(file_size))
                
                # Delete the file
                file_path.unlink()
                self.logger.debug(f"Securely deleted file: {file_path}")
            return True, None
        except Exception as e:
            error = f"Failed to delete file {file_path}: {str(e)}"
            self.logger.error(error)
            return False, error
    
    def sanitize_text_content(self, content: str) -> str:
        """Sanitize text content to remove potentially malicious patterns.
        
        Args:
            content: Text content to sanitize
            
        Returns:
            Sanitized text content
        """
        sanitized = content
        
        # Remove or sanitize potentially malicious HTML
        sanitized = re.sub(r'<script.*?>.*?</script>', '[SCRIPT REMOVED]', sanitized, flags=re.DOTALL | re.IGNORECASE)
        sanitized = re.sub(r'<iframe.*?>.*?</iframe>', '[IFRAME REMOVED]', sanitized, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove javascript: URLs
        sanitized = re.sub(r'javascript\s*:', '[JS REMOVED]:', sanitized, flags=re.IGNORECASE)
        
        # Check for and log suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content, re.DOTALL):
                self.logger.warning(f"Suspicious pattern detected in content: {pattern}")
                # We don't remove all patterns, but log them for awareness
        
        return sanitized
    
    def compute_file_hash(self, file_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """Compute a SHA-256 hash of a file for integrity verification.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (hash_value, error_message)
        """
        try:
            if not file_path.exists():
                return None, f"File does not exist: {file_path}"
                
            sha256_hash = hashlib.sha256()
            
            # Read the file in chunks to handle large files efficiently
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
                    
            return sha256_hash.hexdigest(), None
        except Exception as e:
            error = f"Failed to compute hash for {file_path}: {str(e)}"
            self.logger.error(error)
            return None, error
    
    def validate_file_integrity(self, file_path: Path, expected_hash: str) -> Tuple[bool, Optional[str]]:
        """Validate file integrity by comparing its hash with an expected value.
        
        Args:
            file_path: Path to the file
            expected_hash: Expected SHA-256 hash value
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        actual_hash, error = self.compute_file_hash(file_path)
        
        if error:
            return False, error
            
        if actual_hash != expected_hash:
            error = f"File integrity check failed for {file_path}. Hash mismatch."
            self.logger.warning(error)
            return False, error
            
        return True, None
    
    def comprehensive_file_validation(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Perform comprehensive validation on a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Convert to Path object if string
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        # Run all validations in sequence
        valid, error = self.validate_path(file_path)
        if not valid:
            return False, error
            
        valid, error = self.validate_file_size(file_path)
        if not valid:
            return False, error
            
        valid, error = self.check_file_permissions(file_path)
        if not valid:
            return False, error
            
        valid, error = self.validate_mime_type(file_path)
        if not valid:
            return False, error
            
        # All validations passed
        return True, None


class TestSecurityUtils(SecurityUtils):
    """Security utilities for testing purposes that allow temporary directories."""
    
    def __init__(self):
        """Initialize test security utilities with relaxed path validation."""
        super().__init__()
        self.logger = get_logger(__name__)
        self.logger.warning("Using TestSecurityUtils - security validations are relaxed for testing")
    
    def validate_path(self, path: Path) -> Tuple[bool, Optional[str]]:
        """Validate path with relaxed rules for testing.
        
        This overrides the standard validate_path to allow temporary directories
        that would normally be blocked.
        
        Args:
            path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        path_str = str(path)
        
        # For testing: Allow temporary directories
        temp_dir = tempfile.gettempdir()
        if path_str.startswith(temp_dir):
            return True, None
        
        # Fall back to standard validation for non-temp paths
        return super().validate_path(path)
    
    def validate_output_path(self, output_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate output path with relaxed rules for testing.
        
        Args:
            output_path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        path_str = str(output_path)
        
        # For testing: Allow temporary directories
        temp_dir = tempfile.gettempdir()
        if path_str.startswith(temp_dir):
            # Just check write permissions
            parent_dir = output_path.parent
            if not parent_dir.exists():
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    error = f"Cannot create directory for output: {parent_dir}, error: {str(e)}"
                    self.logger.error(error)
                    return False, error
            
            return True, None
        
        # Fall back to standard validation for non-temp paths
        return super().validate_output_path(output_path)


# Export a global instance for easy import
security_utils = SecurityUtils()
