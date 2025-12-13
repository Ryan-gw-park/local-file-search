"""
Local Finder X v2.0 - File Type Classifier

Classifies files as Content-Indexed or Metadata-Only.
Based on Master Plan Phase 3 specifications.
"""

from pathlib import Path
from typing import Set, Tuple
from enum import Enum


class FileCategory(str, Enum):
    """File category for indexing."""
    CONTENT_INDEXED = "content_indexed"
    METADATA_ONLY = "metadata_only"


class FileType(str, Enum):
    """Specific file type."""
    # Content-indexed types
    WORD = "word"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    EMAIL = "email"
    
    # Metadata-only
    OTHER = "other"


# =============================================================================
# Extension Mappings
# =============================================================================

# Extensions that support content indexing
CONTENT_INDEXED_EXTENSIONS: Set[str] = {
    # Microsoft Office
    ".docx",
    ".xlsx",
    ".pptx",
    # Documents
    ".pdf",
    ".md",
    ".markdown",
    ".txt",
    ".text",
    # Email (optional, for Outlook connector)
    ".eml",
    ".msg",
}

# Extension to FileType mapping
EXTENSION_TO_TYPE = {
    # Word
    ".docx": FileType.WORD,
    ".doc": FileType.WORD,  # Note: .doc not content-indexed in v2.0
    # Excel
    ".xlsx": FileType.EXCEL,
    ".xls": FileType.EXCEL,  # Note: .xls not content-indexed in v2.0
    # PowerPoint
    ".pptx": FileType.POWERPOINT,
    ".ppt": FileType.POWERPOINT,  # Note: .ppt not content-indexed in v2.0
    # PDF
    ".pdf": FileType.PDF,
    # Markdown
    ".md": FileType.MARKDOWN,
    ".markdown": FileType.MARKDOWN,
    # Text
    ".txt": FileType.TEXT,
    ".text": FileType.TEXT,
    # Email
    ".eml": FileType.EMAIL,
    ".msg": FileType.EMAIL,
}


# =============================================================================
# Classification Functions
# =============================================================================

def get_file_extension(file_path: str) -> str:
    """
    Get the lowercase extension of a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        Lowercase extension including the dot (e.g., ".docx").
    """
    return Path(file_path).suffix.lower()


def get_file_type(file_path: str) -> FileType:
    """
    Get the specific file type for a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        FileType enum value.
    """
    ext = get_file_extension(file_path)
    return EXTENSION_TO_TYPE.get(ext, FileType.OTHER)


def get_file_category(file_path: str) -> FileCategory:
    """
    Determine if a file should be content-indexed or metadata-only.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        FileCategory enum value.
    """
    ext = get_file_extension(file_path)
    
    if ext in CONTENT_INDEXED_EXTENSIONS:
        return FileCategory.CONTENT_INDEXED
    else:
        return FileCategory.METADATA_ONLY


def classify_file(file_path: str) -> Tuple[FileCategory, FileType]:
    """
    Classify a file by category and type.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        Tuple of (FileCategory, FileType).
    """
    return get_file_category(file_path), get_file_type(file_path)


def is_content_indexed(file_path: str) -> bool:
    """
    Check if a file should be content-indexed.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        True if the file should be content-indexed.
    """
    return get_file_category(file_path) == FileCategory.CONTENT_INDEXED


def is_office_file(file_path: str) -> bool:
    """Check if a file is a Microsoft Office file."""
    file_type = get_file_type(file_path)
    return file_type in {FileType.WORD, FileType.EXCEL, FileType.POWERPOINT}


def is_document_file(file_path: str) -> bool:
    """Check if a file is any kind of document."""
    file_type = get_file_type(file_path)
    return file_type in {
        FileType.WORD,
        FileType.EXCEL,
        FileType.POWERPOINT,
        FileType.PDF,
        FileType.MARKDOWN,
        FileType.TEXT,
    }


def get_supported_extensions() -> Set[str]:
    """Get all supported content-indexed extensions."""
    return CONTENT_INDEXED_EXTENSIONS.copy()


def get_display_type_name(file_type: FileType) -> str:
    """Get a human-readable name for a file type."""
    names = {
        FileType.WORD: "Word Document",
        FileType.EXCEL: "Excel Spreadsheet",
        FileType.POWERPOINT: "PowerPoint Presentation",
        FileType.PDF: "PDF Document",
        FileType.MARKDOWN: "Markdown",
        FileType.TEXT: "Text File",
        FileType.EMAIL: "Email",
        FileType.OTHER: "Other",
    }
    return names.get(file_type, "Unknown")


__all__ = [
    "FileCategory",
    "FileType",
    "CONTENT_INDEXED_EXTENSIONS",
    "EXTENSION_TO_TYPE",
    "get_file_extension",
    "get_file_type",
    "get_file_category",
    "classify_file",
    "is_content_indexed",
    "is_office_file",
    "is_document_file",
    "get_supported_extensions",
    "get_display_type_name",
]
