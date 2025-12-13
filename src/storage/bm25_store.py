"""
Local Finder X v2.0 - BM25 Store

Persistent BM25 lexical index for keyword-based search.
Uses rank_bm25 library with pickle persistence.
"""

import pickle
import math
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    BM25Okapi = None

from src.config.paths import get_bm25_path


@dataclass
class BM25Document:
    """A document in the BM25 index."""
    doc_id: str  # chunk_id or file_id
    file_id: str
    tokens: List[str]
    is_file_level: bool = False  # True for metadata-only files


@dataclass
class BM25Index:
    """BM25 index data structure."""
    schema_version: str = "2.0"
    documents: List[BM25Document] = field(default_factory=list)
    doc_id_to_idx: Dict[str, int] = field(default_factory=dict)
    file_id_to_doc_ids: Dict[str, List[str]] = field(default_factory=dict)


class BM25Store:
    """
    Persistent BM25 index for lexical search.
    
    Supports:
    - Chunk-level tokens (for content-indexed files)
    - File-level tokens (for metadata-only files: filename, path, author)
    """
    
    def __init__(self, index_path: Optional[Path] = None):
        """
        Initialize the BM25 store.
        
        Args:
            index_path: Path to the index file. Uses default if None.
        """
        self.index_path = index_path or get_bm25_path()
        self._index: Optional[BM25Index] = None
        self._bm25: Optional[BM25Okapi] = None
        self._dirty = False
    
    @property
    def index(self) -> BM25Index:
        """Lazy-load the index."""
        if self._index is None:
            self.load()
        return self._index  # type: ignore
    
    def load(self) -> None:
        """Load index from disk."""
        if self.index_path.exists():
            try:
                with open(self.index_path, "rb") as f:
                    data = pickle.load(f)
                    if isinstance(data, BM25Index):
                        self._index = data
                    else:
                        # Legacy format or corrupted
                        self._index = BM25Index()
            except Exception as e:
                print(f"Warning: Could not load BM25 index: {e}")
                self._index = BM25Index()
        else:
            self._index = BM25Index()
        
        self._rebuild_bm25()
    
    def save(self) -> None:
        """Save index to disk."""
        if self._index is None:
            return
        
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.index_path, "wb") as f:
            pickle.dump(self._index, f)
        
        self._dirty = False
    
    def _rebuild_bm25(self) -> None:
        """Rebuild the BM25 model from documents."""
        if not BM25_AVAILABLE:
            self._bm25 = None
            return
        
        if not self.index.documents:
            self._bm25 = None
            return
        
        corpus = [doc.tokens for doc in self.index.documents]
        self._bm25 = BM25Okapi(corpus)
    
    def add_document(
        self,
        doc_id: str,
        file_id: str,
        tokens: List[str],
        is_file_level: bool = False,
    ) -> None:
        """
        Add a document to the index.
        
        Args:
            doc_id: Unique document ID (chunk_id or file_id).
            file_id: Parent file ID.
            tokens: List of tokens for this document.
            is_file_level: True if this is a file-level entry (metadata-only).
        """
        if not tokens:
            return
        
        # Remove if exists
        if doc_id in self.index.doc_id_to_idx:
            self.remove_document(doc_id)
        
        doc = BM25Document(
            doc_id=doc_id,
            file_id=file_id,
            tokens=tokens,
            is_file_level=is_file_level,
        )
        
        idx = len(self.index.documents)
        self.index.documents.append(doc)
        self.index.doc_id_to_idx[doc_id] = idx
        
        # Track file -> doc mapping
        if file_id not in self.index.file_id_to_doc_ids:
            self.index.file_id_to_doc_ids[file_id] = []
        self.index.file_id_to_doc_ids[file_id].append(doc_id)
        
        self._dirty = True
    
    def add_documents(
        self,
        documents: List[Tuple[str, str, List[str], bool]],
    ) -> int:
        """
        Add multiple documents to the index.
        
        Args:
            documents: List of (doc_id, file_id, tokens, is_file_level) tuples.
        
        Returns:
            Number of documents added.
        """
        count = 0
        for doc_id, file_id, tokens, is_file_level in documents:
            if tokens:
                self.add_document(doc_id, file_id, tokens, is_file_level)
                count += 1
        
        # Rebuild BM25 after batch add
        if count > 0:
            self._rebuild_bm25()
        
        return count
    
    def remove_document(self, doc_id: str) -> None:
        """Remove a document from the index."""
        if doc_id not in self.index.doc_id_to_idx:
            return
        
        idx = self.index.doc_id_to_idx[doc_id]
        doc = self.index.documents[idx]
        
        # Remove from file mapping
        if doc.file_id in self.index.file_id_to_doc_ids:
            self.index.file_id_to_doc_ids[doc.file_id] = [
                d for d in self.index.file_id_to_doc_ids[doc.file_id]
                if d != doc_id
            ]
        
        # Mark as removed (we'll compact later if needed)
        self.index.documents[idx] = BM25Document("", "", [])
        del self.index.doc_id_to_idx[doc_id]
        
        self._dirty = True
    
    def remove_by_file(self, file_id: str) -> int:
        """
        Remove all documents for a file.
        
        Args:
            file_id: The file ID to remove documents for.
        
        Returns:
            Number of documents removed.
        """
        doc_ids = self.index.file_id_to_doc_ids.get(file_id, [])
        count = len(doc_ids)
        
        for doc_id in list(doc_ids):
            self.remove_document(doc_id)
        
        if file_id in self.index.file_id_to_doc_ids:
            del self.index.file_id_to_doc_ids[file_id]
        
        if count > 0:
            self._rebuild_bm25()
        
        return count
    
    def search(
        self,
        query_tokens: List[str],
        top_k: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search for documents matching the query.
        
        Args:
            query_tokens: Tokenized query.
            top_k: Number of results to return.
        
        Returns:
            List of results with doc_id, file_id, score, is_file_level.
        """
        if not BM25_AVAILABLE:
            return []
        
        if self._bm25 is None or not query_tokens:
            return []
        
        scores = self._bm25.get_scores(query_tokens)
        
        # Get top-k indices
        indexed_scores = [(i, s) for i, s in enumerate(scores) if s > 0]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        top_indices = indexed_scores[:top_k]
        
        results = []
        for idx, score in top_indices:
            doc = self.index.documents[idx]
            if doc.doc_id:  # Skip removed documents
                results.append({
                    "doc_id": doc.doc_id,
                    "file_id": doc.file_id,
                    "score": float(score),
                    "is_file_level": doc.is_file_level,
                })
        
        return results
    
    def compact(self) -> None:
        """Remove deleted documents and rebuild index."""
        # Filter out empty documents
        valid_docs = [d for d in self.index.documents if d.doc_id]
        
        # Rebuild mappings
        new_index = BM25Index(schema_version="2.0")
        for i, doc in enumerate(valid_docs):
            new_index.documents.append(doc)
            new_index.doc_id_to_idx[doc.doc_id] = i
            
            if doc.file_id not in new_index.file_id_to_doc_ids:
                new_index.file_id_to_doc_ids[doc.file_id] = []
            new_index.file_id_to_doc_ids[doc.file_id].append(doc.doc_id)
        
        self._index = new_index
        self._rebuild_bm25()
        self._dirty = True
    
    def get_stats(self) -> Dict[str, int]:
        """Get index statistics."""
        valid_count = sum(1 for d in self.index.documents if d.doc_id)
        file_count = len(self.index.file_id_to_doc_ids)
        
        return {
            "documents": valid_count,
            "files": file_count,
        }
    
    def clear(self) -> None:
        """Clear the entire index."""
        self._index = BM25Index()
        self._bm25 = None
        self._dirty = True
        self.save()


# Singleton instance
_bm25_store: Optional[BM25Store] = None


def get_bm25_store() -> BM25Store:
    """Get the singleton BM25 store instance."""
    global _bm25_store
    if _bm25_store is None:
        _bm25_store = BM25Store()
    return _bm25_store


__all__ = [
    "BM25Document",
    "BM25Index",
    "BM25Store",
    "get_bm25_store",
    "BM25_AVAILABLE",
]
