"""
Local Finder X v2.0 - Vector Store Adapter

High-level wrapper for LanceDB vector operations.
Provides a clean interface for indexing and search operations.
"""

import json
import time
from typing import List, Optional, Dict, Any
from dataclasses import asdict

from src.core.schemas import ChunkRecord, ChunkMetadata
from src.storage.lancedb_store import LanceDBStore, LANCEDB_AVAILABLE


class VectorStore:
    """
    High-level vector store adapter.
    
    Wraps LanceDB operations with domain-specific logic
    and handles serialization/deserialization of ChunkRecords.
    """
    
    def __init__(self, lancedb_store: Optional[LanceDBStore] = None):
        """
        Initialize the vector store.
        
        Args:
            lancedb_store: Optional LanceDB store instance.
        """
        self._store = lancedb_store
    
    @property
    def store(self) -> LanceDBStore:
        """Lazy-load LanceDB store."""
        if self._store is None:
            if not LANCEDB_AVAILABLE:
                raise ImportError("LanceDB is not available")
            self._store = LanceDBStore()
        return self._store
    
    def add_chunk(self, chunk: ChunkRecord) -> None:
        """
        Add a single chunk to the store.
        
        Args:
            chunk: ChunkRecord to add.
        """
        self.add_chunks([chunk])
    
    def add_chunks(self, chunks: List[ChunkRecord]) -> int:
        """
        Add multiple chunks to the store.
        
        Args:
            chunks: List of ChunkRecords to add.
        
        Returns:
            Number of chunks added.
        """
        if not chunks:
            return 0
        
        records = []
        for chunk in chunks:
            # Serialize metadata to JSON string
            metadata_dict = {
                "page": chunk.metadata.page,
                "slide": chunk.metadata.slide,
                "slide_title": chunk.metadata.slide_title,
                "sheet": chunk.metadata.sheet,
                "row_range": chunk.metadata.row_range,
                "header_path": chunk.metadata.header_path,
                "subject": chunk.metadata.subject,
                "date": chunk.metadata.date,
                "sender": chunk.metadata.sender,
            }
            
            record = {
                "chunk_id": chunk.chunk_id,
                "file_id": chunk.file_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "vector": chunk.embedding or [0.0] * 1024,  # Default zero vector
                "tokens": json.dumps(chunk.tokens or []),
                "metadata": json.dumps(metadata_dict),
                "content_indexed": True,
                "created_at": time.time(),
            }
            records.append(record)
        
        return self.store.add_chunks(records)
    
    def search(
        self,
        query_vector: List[float],
        top_k: int = 50,
        file_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks.
        
        Args:
            query_vector: Query embedding vector.
            top_k: Number of results to return.
            file_ids: Optional list of file IDs to filter by.
        
        Returns:
            List of search results with chunk info and scores.
        """
        filter_expr = None
        if file_ids:
            # Build filter for specific files
            ids_str = ", ".join(f"'{fid}'" for fid in file_ids)
            filter_expr = f"file_id IN ({ids_str})"
        
        results = self.store.search_chunks(
            query_vector=query_vector,
            top_k=top_k,
            filter_expr=filter_expr,
        )
        
        # Parse results and add score info
        parsed_results = []
        for result in results:
            # Parse metadata JSON
            metadata = {}
            if result.get("metadata"):
                try:
                    metadata = json.loads(result["metadata"])
                except json.JSONDecodeError:
                    pass
            
            # Parse tokens JSON
            tokens = []
            if result.get("tokens"):
                try:
                    tokens = json.loads(result["tokens"])
                except json.JSONDecodeError:
                    pass
            
            parsed_results.append({
                "chunk_id": result.get("chunk_id"),
                "file_id": result.get("file_id"),
                "chunk_index": result.get("chunk_index"),
                "text": result.get("text"),
                "tokens": tokens,
                "metadata": metadata,
                "score": result.get("_distance", 0.0),  # LanceDB returns _distance
            })
        
        return parsed_results
    
    def delete_by_file(self, file_id: str) -> None:
        """
        Delete all chunks for a file.
        
        Args:
            file_id: The file ID to delete chunks for.
        """
        self.store.delete_chunks_by_file(file_id)
    
    def get_by_file(self, file_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a file.
        
        Args:
            file_id: The file ID to get chunks for.
        
        Returns:
            List of chunk dictionaries.
        """
        return self.store.get_chunks_by_file(file_id)
    
    def get_stats(self) -> Dict[str, int]:
        """Get storage statistics."""
        return self.store.get_stats()
    
    def clear(self) -> None:
        """Clear all data from the store."""
        self.store.clear()


# Singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get the singleton vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


__all__ = [
    "VectorStore",
    "get_vector_store",
]
