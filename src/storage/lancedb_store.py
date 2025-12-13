"""
Local Finder X v2.0 - LanceDB Store

LanceDB-based vector and metadata storage.
Provides high-performance vector search with SQL-like filtering.
"""

import time
from typing import List, Optional, Dict, Any
from pathlib import Path

try:
    import lancedb
    from lancedb.table import Table
    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False
    lancedb = None
    Table = None

try:
    import pyarrow as pa
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False
    pa = None

from src.config.paths import get_lancedb_path


# =============================================================================
# Schema Definition
# =============================================================================

def get_chunks_schema():
    """
    Get the Arrow schema for the chunks table.
    
    Schema based on Master Plan Phase 2:
    - chunk_id: unique identifier
    - file_id: parent file reference
    - chunk_index: position in file
    - text: chunk content
    - vector: embedding (1024 dimensions for BGE-M3)
    - tokens: lexical tokens (stored as JSON string)
    - metadata: location info (stored as JSON string)
    - content_indexed: boolean flag
    - created_at: timestamp
    """
    if not PYARROW_AVAILABLE:
        raise ImportError("pyarrow is required for LanceDB schema definition")
    
    return pa.schema([
        pa.field("chunk_id", pa.string()),
        pa.field("file_id", pa.string()),
        pa.field("chunk_index", pa.int32()),
        pa.field("text", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), 1024)),  # BGE-M3 dimension
        pa.field("tokens", pa.string()),  # JSON array of tokens
        pa.field("metadata", pa.string()),  # JSON object
        pa.field("content_indexed", pa.bool_()),
        pa.field("created_at", pa.float64()),
    ])


def get_files_schema():
    """
    Get the Arrow schema for the files table.
    
    Stores FileRecord metadata for quick lookup.
    """
    if not PYARROW_AVAILABLE:
        raise ImportError("pyarrow is required for LanceDB schema definition")
    
    return pa.schema([
        pa.field("file_id", pa.string()),
        pa.field("path", pa.string()),
        pa.field("filename", pa.string()),
        pa.field("extension", pa.string()),
        pa.field("source", pa.string()),
        pa.field("content_indexed", pa.bool_()),
        pa.field("size_bytes", pa.int64()),
        pa.field("created_at", pa.float64()),
        pa.field("modified_at", pa.float64()),
        pa.field("author", pa.string()),
        pa.field("indexed_at", pa.float64()),
    ])


# =============================================================================
# LanceDB Store
# =============================================================================

class LanceDBStore:
    """
    LanceDB-based storage for vectors and metadata.
    
    Provides:
    - Vector similarity search (cosine)
    - Metadata filtering
    - File and chunk management
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize LanceDB connection.
        
        Args:
            db_path: Path to LanceDB directory. Uses default if None.
        """
        if not LANCEDB_AVAILABLE:
            raise ImportError(
                "lancedb is required. Install with: pip install lancedb"
            )
        
        self.db_path = db_path or get_lancedb_path()
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        self._db = None
        self._chunks_table: Optional[Table] = None
        self._files_table: Optional[Table] = None
    
    @property
    def db(self):
        """Lazy-load database connection."""
        if self._db is None:
            self._db = lancedb.connect(str(self.db_path))
        return self._db
    
    def _ensure_tables(self) -> None:
        """Ensure all required tables exist."""
        table_names = self.db.table_names()
        
        # Create chunks table if not exists
        if "chunks" not in table_names:
            # Create with empty data matching schema
            schema = get_chunks_schema()
            self._chunks_table = self.db.create_table(
                "chunks",
                schema=schema,
                mode="overwrite",
            )
        else:
            self._chunks_table = self.db.open_table("chunks")
        
        # Create files table if not exists
        if "files" not in table_names:
            schema = get_files_schema()
            self._files_table = self.db.create_table(
                "files",
                schema=schema,
                mode="overwrite",
            )
        else:
            self._files_table = self.db.open_table("files")
    
    @property
    def chunks_table(self) -> Table:
        """Get the chunks table."""
        if self._chunks_table is None:
            self._ensure_tables()
        return self._chunks_table  # type: ignore
    
    @property
    def files_table(self) -> Table:
        """Get the files table."""
        if self._files_table is None:
            self._ensure_tables()
        return self._files_table  # type: ignore
    
    # =========================================================================
    # Chunk Operations
    # =========================================================================
    
    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Add chunks to the store.
        
        Args:
            chunks: List of chunk dictionaries with required fields.
        
        Returns:
            Number of chunks added.
        """
        if not chunks:
            return 0
        
        # Add timestamp if not present
        for chunk in chunks:
            if "created_at" not in chunk:
                chunk["created_at"] = time.time()
        
        self.chunks_table.add(chunks)
        return len(chunks)
    
    def search_chunks(
        self,
        query_vector: List[float],
        top_k: int = 50,
        filter_expr: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks by vector.
        
        Args:
            query_vector: Query embedding vector.
            top_k: Number of results to return.
            filter_expr: Optional SQL-like filter expression.
        
        Returns:
            List of matching chunks with scores.
        """
        query = self.chunks_table.search(query_vector).limit(top_k)
        
        if filter_expr:
            query = query.where(filter_expr)
        
        results = query.to_list()
        return results
    
    def delete_chunks_by_file(self, file_id: str) -> int:
        """
        Delete all chunks for a file.
        
        Args:
            file_id: The file ID to delete chunks for.
        
        Returns:
            Number of chunks deleted (approximate).
        """
        # LanceDB delete by predicate
        self.chunks_table.delete(f"file_id = '{file_id}'")
        return 0  # LanceDB doesn't return count
    
    def get_chunks_by_file(self, file_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a file."""
        results = self.chunks_table.search().where(
            f"file_id = '{file_id}'"
        ).to_list()
        return results
    
    # =========================================================================
    # File Operations
    # =========================================================================
    
    def add_file(self, file_record: Dict[str, Any]) -> None:
        """Add a file record to the store."""
        if "indexed_at" not in file_record:
            file_record["indexed_at"] = time.time()
        self.files_table.add([file_record])
    
    def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get a file record by ID."""
        results = self.files_table.search().where(
            f"file_id = '{file_id}'"
        ).limit(1).to_list()
        return results[0] if results else None
    
    def get_file_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get a file record by path."""
        # Escape single quotes in path
        escaped_path = path.replace("'", "''")
        results = self.files_table.search().where(
            f"path = '{escaped_path}'"
        ).limit(1).to_list()
        return results[0] if results else None
    
    def delete_file(self, file_id: str) -> None:
        """Delete a file and its chunks."""
        self.delete_chunks_by_file(file_id)
        self.files_table.delete(f"file_id = '{file_id}'")
    
    def get_all_files(self) -> List[Dict[str, Any]]:
        """Get all file records."""
        return self.files_table.to_pandas().to_dict("records")
    
    # =========================================================================
    # Utility
    # =========================================================================
    
    def get_stats(self) -> Dict[str, int]:
        """Get storage statistics."""
        try:
            chunks_count = len(self.chunks_table.to_pandas())
            files_count = len(self.files_table.to_pandas())
        except Exception:
            chunks_count = 0
            files_count = 0
        
        return {
            "chunks": chunks_count,
            "files": files_count,
        }
    
    def clear(self) -> None:
        """Clear all data from the store."""
        self.db.drop_table("chunks", ignore_missing=True)
        self.db.drop_table("files", ignore_missing=True)
        self._chunks_table = None
        self._files_table = None
        self._ensure_tables()


# Convenience function
def get_lancedb_store() -> LanceDBStore:
    """Get a LanceDB store instance."""
    return LanceDBStore()


__all__ = [
    "LanceDBStore",
    "get_lancedb_store",
    "get_chunks_schema",
    "get_files_schema",
    "LANCEDB_AVAILABLE",
]
