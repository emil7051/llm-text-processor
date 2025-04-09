"""Base class for all text processors."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseProcessor(ABC):
    """Base class for all text processors.
    
    Each processor is responsible for a specific aspect of text processing,
    such as structure preservation, content cleaning, or optimization.
    """
    
    @abstractmethod
    def process(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Process the content.
        
        Args:
            content: The content to process.
            metadata: Optional metadata about the content.
            
        Returns:
            Processed content.
        """
        pass 