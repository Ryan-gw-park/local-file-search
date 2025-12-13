"""
Local Finder X v2.0 - Base Extractor

Base class and utilities for content extractors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Type
from pathlib import Path


@dataclass
class ExtractorResult:
    """Result from content extraction."""
    text: str = ""
    # Structured content for better chunking
    sections: List[Dict[str, Any]] = field(default_factory=list)
    # Metadata extracted from the document
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Error if extraction failed
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        return self.error is None and bool(self.text.strip())


class BaseExtractor(ABC):
    """Base class for content extractors."""
    
    # File extensions this extractor handles
    SUPPORTED_EXTENSIONS: List[str] = []
    
    @abstractmethod
    def extract(self, file_path: str) -> ExtractorResult:
        """
        Extract content from a file.
        
        Args:
            file_path: Path to the file.
        
        Returns:
            ExtractorResult with extracted content.
        """
        pass
    
    def can_handle(self, file_path: str) -> bool:
        """Check if this extractor can handle the given file."""
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS
    
    def _create_error_result(self, error: str) -> ExtractorResult:
        """Create an error result."""
        return ExtractorResult(error=error)
    
    def _create_success_result(
        self,
        text: str,
        sections: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExtractorResult:
        """Create a success result."""
        return ExtractorResult(
            text=text,
            sections=sections or [],
            metadata=metadata or {},
        )


# Registry of extractors
_EXTRACTOR_REGISTRY: Dict[str, Type[BaseExtractor]] = {}


def register_extractor(extractor_class: Type[BaseExtractor]) -> Type[BaseExtractor]:
    """Register an extractor class for its supported extensions."""
    for ext in extractor_class.SUPPORTED_EXTENSIONS:
        _EXTRACTOR_REGISTRY[ext.lower()] = extractor_class
    return extractor_class


def get_extractor_for_file(file_path: str) -> Optional[BaseExtractor]:
    """
    Get an appropriate extractor for a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        An extractor instance, or None if no extractor available.
    """
    ext = Path(file_path).suffix.lower()
    extractor_class = _EXTRACTOR_REGISTRY.get(ext)
    
    if extractor_class:
        return extractor_class()
    
    return None


__all__ = [
    "ExtractorResult",
    "BaseExtractor",
    "register_extractor",
    "get_extractor_for_file",
]
