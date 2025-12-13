"""
Local Finder X v2.0 - Search Engine

Hybrid search with Dense + BM25 + RRF Fusion.
Based on Master Plan Phase 4 specifications.
"""

import time
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field

from src.core.schemas import (
    SearchResponse, FileHit, FileRecord, Evidence,
    EvidenceScores, EvidenceLocation, MatchType, SourceType
)
from src.core.tokenizer import tokenize_query
from src.core.embedding import get_embedding_model
from src.storage.vector_store import VectorStore, get_vector_store
from src.storage.bm25_store import BM25Store, get_bm25_store
from src.storage.manifest import ManifestStore
from src.storage.lancedb_store import LANCEDB_AVAILABLE


# =============================================================================
# Configuration
# =============================================================================

# Default search parameters
DEFAULT_TOP_K_DENSE = 50
DEFAULT_TOP_K_BM25 = 50
DEFAULT_RRF_K = 60
DEFAULT_MAX_RESULTS = 20
DEFAULT_MAX_EVIDENCES = 5

# Metadata-only score decay
METADATA_ONLY_DECAY = 0.4


# =============================================================================
# Retrievers
# =============================================================================

def dense_retrieve(
    query: str,
    vector_store: VectorStore,
    top_k: int = DEFAULT_TOP_K_DENSE,
) -> List[Dict[str, Any]]:
    """
    Dense retrieval using vector similarity.
    
    Args:
        query: Search query.
        vector_store: Vector store instance.
        top_k: Number of results.
    
    Returns:
        List of chunk results with scores.
    """
    embedding_model = get_embedding_model()
    
    if not embedding_model.is_available():
        return []
    
    query_vector = embedding_model.encode_query(query)
    if query_vector is None:
        return []
    
    try:
        results = vector_store.search(query_vector, top_k=top_k)
        
        # Normalize scores (LanceDB returns distance, lower is better)
        for result in results:
            distance = result.get("score", 0.0)
            # Convert distance to similarity score (0-1)
            result["dense_score"] = max(0, 1 - distance)
        
        return results
    except Exception as e:
        print(f"Dense retrieval error: {e}")
        return []


def lexical_retrieve(
    query: str,
    bm25_store: BM25Store,
    top_k: int = DEFAULT_TOP_K_BM25,
) -> List[Dict[str, Any]]:
    """
    Lexical retrieval using BM25.
    
    Args:
        query: Search query.
        bm25_store: BM25 store instance.
        top_k: Number of results.
    
    Returns:
        List of document results with scores.
    """
    tokens = tokenize_query(query)
    
    if not tokens:
        return []
    
    results = bm25_store.search(tokens, top_k=top_k)
    
    # Normalize BM25 scores
    if results:
        max_score = max(r["score"] for r in results)
        if max_score > 0:
            for result in results:
                result["lexical_score"] = result["score"] / max_score
        else:
            for result in results:
                result["lexical_score"] = 0.0
    
    return results


# =============================================================================
# RRF Fusion
# =============================================================================

def rrf_fusion(
    dense_results: List[Dict[str, Any]],
    lexical_results: List[Dict[str, Any]],
    k: int = DEFAULT_RRF_K,
) -> Dict[str, float]:
    """
    Reciprocal Rank Fusion to combine dense and lexical results.
    
    RRF Score = sum(1 / (k + rank))
    
    Args:
        dense_results: Results from dense retrieval.
        lexical_results: Results from lexical retrieval.
        k: RRF constant (default 60).
    
    Returns:
        Dictionary mapping file_id to fused score.
    """
    file_scores: Dict[str, float] = {}
    
    # Add dense scores
    for rank, result in enumerate(dense_results, 1):
        file_id = result.get("file_id", "")
        if file_id:
            rrf_score = 1.0 / (k + rank)
            file_scores[file_id] = file_scores.get(file_id, 0) + rrf_score
    
    # Add lexical scores
    for rank, result in enumerate(lexical_results, 1):
        file_id = result.get("file_id", "")
        if file_id:
            rrf_score = 1.0 / (k + rank)
            file_scores[file_id] = file_scores.get(file_id, 0) + rrf_score
    
    return file_scores


# =============================================================================
# Evidence Builder
# =============================================================================

def build_evidences(
    file_id: str,
    dense_results: List[Dict[str, Any]],
    max_evidences: int = DEFAULT_MAX_EVIDENCES,
) -> List[Evidence]:
    """
    Build evidence list for a file from dense results.
    
    Args:
        file_id: Target file ID.
        dense_results: Dense retrieval results.
        max_evidences: Maximum evidences to return.
    
    Returns:
        List of Evidence objects.
    """
    evidences = []
    
    # Filter results for this file
    file_chunks = [r for r in dense_results if r.get("file_id") == file_id]
    
    # Sort by score
    file_chunks.sort(key=lambda x: x.get("dense_score", 0), reverse=True)
    
    for chunk in file_chunks[:max_evidences]:
        text = chunk.get("text", "")
        metadata = chunk.get("metadata", {})
        
        # Create snippet (first 300 chars)
        snippet = text[:300] + "..." if len(text) > 300 else text
        
        evidence = Evidence(
            file_id=file_id,
            summary="",  # TODO: Generate summary
            snippet=snippet,
            scores=EvidenceScores(
                final=chunk.get("dense_score", 0.0),
                dense=chunk.get("dense_score", 0.0),
                lexical=0.0,
            ),
            location=EvidenceLocation(
                page=metadata.get("page"),
                slide=metadata.get("slide"),
                sheet=metadata.get("sheet"),
                header_path=metadata.get("header_path"),
            ),
        )
        evidences.append(evidence)
    
    return evidences


# =============================================================================
# Search Engine
# =============================================================================

class SearchEngine:
    """
    Hybrid search engine combining Dense + BM25 with RRF fusion.
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        bm25_store: Optional[BM25Store] = None,
        manifest_store: Optional[ManifestStore] = None,
    ):
        self._vector_store = vector_store
        self._bm25_store = bm25_store
        self._manifest_store = manifest_store
    
    @property
    def vector_store(self) -> VectorStore:
        if self._vector_store is None:
            self._vector_store = get_vector_store()
        return self._vector_store
    
    @property
    def bm25_store(self) -> BM25Store:
        if self._bm25_store is None:
            self._bm25_store = get_bm25_store()
        return self._bm25_store
    
    @property
    def manifest_store(self) -> ManifestStore:
        if self._manifest_store is None:
            self._manifest_store = ManifestStore()
        return self._manifest_store
    
    def search(
        self,
        query: str,
        max_results: int = DEFAULT_MAX_RESULTS,
        top_k_dense: int = DEFAULT_TOP_K_DENSE,
        top_k_bm25: int = DEFAULT_TOP_K_BM25,
        rrf_k: int = DEFAULT_RRF_K,
        max_evidences: int = DEFAULT_MAX_EVIDENCES,
    ) -> SearchResponse:
        """
        Perform hybrid search.
        
        Args:
            query: Search query.
            max_results: Maximum files to return.
            top_k_dense: Dense retrieval count.
            top_k_bm25: BM25 retrieval count.
            rrf_k: RRF constant.
            max_evidences: Max evidences per file.
        
        Returns:
            SearchResponse with results.
        """
        start_time = time.time()
        
        if not query.strip():
            return SearchResponse(query=query, elapsed_ms=0)
        
        try:
            # Step 1: Dense retrieval
            dense_results = []
            if LANCEDB_AVAILABLE:
                try:
                    dense_results = dense_retrieve(query, self.vector_store, top_k_dense)
                except Exception:
                    pass
            
            # Step 2: Lexical retrieval
            lexical_results = lexical_retrieve(query, self.bm25_store, top_k_bm25)
            
            # Step 3: RRF Fusion
            file_scores = rrf_fusion(dense_results, lexical_results, rrf_k)
            
            # Step 4: Apply metadata-only decay
            for result in lexical_results:
                if result.get("is_file_level"):
                    file_id = result.get("file_id", "")
                    if file_id in file_scores:
                        file_scores[file_id] *= METADATA_ONLY_DECAY
            
            # Step 5: Sort and limit
            sorted_files = sorted(file_scores.items(), key=lambda x: x[1], reverse=True)
            top_files = sorted_files[:max_results]
            
            # Step 6: Build FileHits with Evidences
            results = []
            for file_id, score in top_files:
                # Get file info from manifest
                file_record = self._get_file_record(file_id)
                if file_record is None:
                    continue
                
                # Determine match type
                has_dense = any(r.get("file_id") == file_id for r in dense_results)
                has_lexical = any(r.get("file_id") == file_id for r in lexical_results)
                
                if has_dense and has_lexical:
                    match_type = MatchType.HYBRID
                elif has_dense:
                    match_type = MatchType.SEMANTIC
                else:
                    match_type = MatchType.LEXICAL
                
                # Build evidences
                evidences = build_evidences(file_id, dense_results, max_evidences)
                
                file_hit = FileHit(
                    file=file_record,
                    score=score,
                    match_type=match_type,
                    content_available=file_record.content_indexed,
                    evidences=evidences,
                )
                results.append(file_hit)
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            return SearchResponse(
                query=query,
                elapsed_ms=elapsed_ms,
                results=results,
            )
            
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return SearchResponse(
                query=query,
                elapsed_ms=elapsed_ms,
                error=str(e),
            )
    
    def _get_file_record(self, file_id: str) -> Optional[FileRecord]:
        """Get FileRecord from manifest by file_id."""
        # Search through manifest for matching file_id
        for path, fp in self.manifest_store.manifest.files.items():
            if fp.file_id == file_id:
                return FileRecord(
                    file_id=file_id,
                    path=path,
                    filename=path.split("/")[-1] if "/" in path else path.split("\\")[-1],
                    content_indexed=fp.content_indexed,
                )
        return None


# Singleton
_search_engine: Optional[SearchEngine] = None


def get_search_engine() -> SearchEngine:
    """Get the singleton search engine instance."""
    global _search_engine
    if _search_engine is None:
        _search_engine = SearchEngine()
    return _search_engine


def search(query: str, **kwargs) -> SearchResponse:
    """Convenience function for searching."""
    return get_search_engine().search(query, **kwargs)


__all__ = [
    "SearchEngine",
    "get_search_engine",
    "search",
    "dense_retrieve",
    "lexical_retrieve",
    "rrf_fusion",
    "build_evidences",
    "DEFAULT_TOP_K_DENSE",
    "DEFAULT_TOP_K_BM25",
    "DEFAULT_RRF_K",
    "DEFAULT_MAX_RESULTS",
]
