"""
Local Finder X v2.0 - Data Schemas (DTOs/Models)

Defines all core data structures for the application.
Based on Master Plan Phase 2 specifications.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
import time


# =============================================================================
# Enums
# =============================================================================

class SourceType(str, Enum):
    """Source type for files."""
    LOCAL = "local"
    OUTLOOK = "outlook"
    ONEDRIVE = "onedrive"
    SHAREPOINT = "sharepoint"
    GDRIVE = "gdrive"


class MatchType(str, Enum):
    """Match type for search results."""
    SEMANTIC = "semantic"
    LEXICAL = "lexical"
    HYBRID = "hybrid"
    RERANKED = "reranked"


# =============================================================================
# FileRecord - Represents a single file (Content Indexed or Metadata-Only)
# =============================================================================

@dataclass
class Fingerprint:
    """File fingerprint for incremental indexing."""
    size_bytes: int
    modified_at: float
    hash: Optional[str] = None


@dataclass
class IndexStats:
    """Indexing statistics for a file."""
    chunk_count: int = 0
    last_indexed_at: float = 0.0
    index_error: Optional[str] = None


@dataclass
class FileRecord:
    """
    Represents a single file in the index.
    This is the primary unit for search results.
    
    - content_indexed=True: Has ChunkRecords, participates in semantic search.
    - content_indexed=False: Metadata-only, participates in file-level lexical match.
    """
    schema_version: str = "2.0"
    file_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Source and indexing status
    source: SourceType = SourceType.LOCAL
    content_indexed: bool = False
    
    # File metadata
    path: str = ""
    filename: str = ""
    extension: str = ""
    
    size_bytes: int = 0
    created_at: float = 0.0
    modified_at: float = 0.0
    
    author: Optional[str] = None
    
    # Indexing metadata
    fingerprint: Fingerprint = field(default_factory=lambda: Fingerprint(0, 0.0))
    index_stats: IndexStats = field(default_factory=IndexStats)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "schema_version": self.schema_version,
            "file_id": self.file_id,
            "source": self.source.value,
            "content_indexed": self.content_indexed,
            "path": self.path,
            "filename": self.filename,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "author": self.author,
            "fingerprint": {
                "size_bytes": self.fingerprint.size_bytes,
                "modified_at": self.fingerprint.modified_at,
                "hash": self.fingerprint.hash,
            },
            "index_stats": {
                "chunk_count": self.index_stats.chunk_count,
                "last_indexed_at": self.index_stats.last_indexed_at,
                "index_error": self.index_stats.index_error,
            },
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileRecord":
        """Create from dictionary."""
        fp_data = data.get("fingerprint", {})
        stats_data = data.get("index_stats", {})
        
        return cls(
            schema_version=data.get("schema_version", "2.0"),
            file_id=data.get("file_id", str(uuid.uuid4())),
            source=SourceType(data.get("source", "local")),
            content_indexed=data.get("content_indexed", False),
            path=data.get("path", ""),
            filename=data.get("filename", ""),
            extension=data.get("extension", ""),
            size_bytes=data.get("size_bytes", 0),
            created_at=data.get("created_at", 0.0),
            modified_at=data.get("modified_at", 0.0),
            author=data.get("author"),
            fingerprint=Fingerprint(
                size_bytes=fp_data.get("size_bytes", 0),
                modified_at=fp_data.get("modified_at", 0.0),
                hash=fp_data.get("hash"),
            ),
            index_stats=IndexStats(
                chunk_count=stats_data.get("chunk_count", 0),
                last_indexed_at=stats_data.get("last_indexed_at", 0.0),
                index_error=stats_data.get("index_error"),
            ),
        )


# =============================================================================
# ChunkRecord - Represents a searchable chunk (Content Indexed files only)
# =============================================================================

@dataclass
class ChunkMetadata:
    """Location metadata for a chunk."""
    page: Optional[int] = None
    slide: Optional[int] = None
    slide_title: Optional[str] = None
    sheet: Optional[str] = None
    row_range: Optional[str] = None
    header_path: Optional[List[str]] = None
    # Email specific
    subject: Optional[str] = None
    date: Optional[str] = None
    sender: Optional[str] = None


@dataclass
class ChunkRecord:
    """
    Represents a single searchable chunk.
    Only created for content_indexed files.
    """
    schema_version: str = "2.0"
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_id: str = ""
    
    chunk_index: int = 0
    text: str = ""
    
    # These are populated during indexing
    embedding: Optional[List[float]] = None
    tokens: Optional[List[str]] = None
    
    metadata: ChunkMetadata = field(default_factory=ChunkMetadata)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "schema_version": self.schema_version,
            "chunk_id": self.chunk_id,
            "file_id": self.file_id,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "embedding": self.embedding,
            "tokens": self.tokens,
            "metadata": {
                "page": self.metadata.page,
                "slide": self.metadata.slide,
                "slide_title": self.metadata.slide_title,
                "sheet": self.metadata.sheet,
                "row_range": self.metadata.row_range,
                "header_path": self.metadata.header_path,
                "subject": self.metadata.subject,
                "date": self.metadata.date,
                "sender": self.metadata.sender,
            },
        }


# =============================================================================
# Evidence - UI display model for "why this file matched"
# =============================================================================

@dataclass
class EvidenceScores:
    """Score breakdown for an evidence."""
    final: float = 0.0
    dense: float = 0.0
    lexical: float = 0.0


@dataclass
class EvidenceLocation:
    """Location information for an evidence."""
    page: Optional[int] = None
    slide: Optional[int] = None
    sheet: Optional[str] = None
    header_path: Optional[List[str]] = None


@dataclass
class Evidence:
    """
    Represents a single piece of evidence for why a file matched.
    This is the UI-facing model, derived from ChunkRecord.
    """
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_id: str = ""
    
    summary: str = ""  # e.g., "이 부분이 'Q4 예산'과 유사합니다."
    snippet: str = ""  # 200-500 chars, with highlights
    
    scores: EvidenceScores = field(default_factory=EvidenceScores)
    location: EvidenceLocation = field(default_factory=EvidenceLocation)


# =============================================================================
# SearchResponse - Complete search result for UI binding
# =============================================================================

@dataclass
class FileHit:
    """A single file hit in search results."""
    file: FileRecord = field(default_factory=FileRecord)
    score: float = 0.0
    match_type: MatchType = MatchType.HYBRID
    content_available: bool = True
    evidences: List[Evidence] = field(default_factory=list)


@dataclass
class SearchResponse:
    """
    Complete search response for UI binding.
    UI should render this directly without additional processing.
    """
    query: str = ""
    elapsed_ms: int = 0
    results: List[FileHit] = field(default_factory=list)
    error: Optional[str] = None
    
    @property
    def total_results(self) -> int:
        return len(self.results)
    
    @property
    def has_results(self) -> bool:
        return len(self.results) > 0


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "SourceType",
    "MatchType",
    # File
    "Fingerprint",
    "IndexStats",
    "FileRecord",
    # Chunk
    "ChunkMetadata",
    "ChunkRecord",
    # Evidence
    "EvidenceScores",
    "EvidenceLocation",
    "Evidence",
    # Search Response
    "FileHit",
    "SearchResponse",
]
