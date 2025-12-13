"""
Local Finder X v2.0 - Indexing Orchestrator

Main controller for the indexing pipeline.
Coordinates file enumeration, extraction, chunking, and storage.
"""

import time
import uuid
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path

from src.core.schemas import FileRecord, ChunkRecord, ChunkMetadata, Fingerprint, IndexStats, SourceType
from src.core.file_enumerator import enumerate_files, EnumerationOptions
from src.core.file_classifier import classify_file, FileCategory, FileType, is_content_indexed
from src.core.extractors import get_extractor_for_file
from src.core.chunker import chunk_content
from src.core.tokenizer import tokenize
from src.core.embedding import get_embedding_model
from src.storage.manifest import ManifestStore, FileFingerprint, get_files_to_reindex, get_deleted_files
from src.storage.vector_store import VectorStore, get_vector_store
from src.storage.bm25_store import BM25Store, get_bm25_store
from src.storage.lancedb_store import LANCEDB_AVAILABLE


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class IndexingProgress:
    """Progress information for indexing."""
    total_files: int = 0
    processed_files: int = 0
    new_files: int = 0
    modified_files: int = 0
    deleted_files: int = 0
    skipped_files: int = 0
    error_files: int = 0
    current_file: str = ""
    errors: List[str] = field(default_factory=list)
    
    @property
    def percent(self) -> float:
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100


@dataclass
class IndexingResult:
    """Final result of indexing operation."""
    success: bool = True
    total_files: int = 0
    indexed_files: int = 0
    content_indexed: int = 0
    metadata_only: int = 0
    deleted_files: int = 0
    error_count: int = 0
    errors: List[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0


ProgressCallback = Callable[[IndexingProgress], None]


# =============================================================================
# Indexing Orchestrator
# =============================================================================

class IndexingOrchestrator:
    """
    Main controller for the indexing pipeline.
    
    Coordinates:
    1. File enumeration and filtering
    2. Incremental indexing (manifest-based)
    3. Content extraction
    4. Chunking
    5. Embedding generation
    6. Storage (LanceDB + BM25)
    """
    
    def __init__(
        self,
        manifest_store: Optional[ManifestStore] = None,
        vector_store: Optional[VectorStore] = None,
        bm25_store: Optional[BM25Store] = None,
    ):
        self._manifest = manifest_store
        self._vector_store = vector_store
        self._bm25_store = bm25_store
        self._embedding_model = None
    
    @property
    def manifest(self) -> ManifestStore:
        if self._manifest is None:
            self._manifest = ManifestStore()
        return self._manifest
    
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
    def embedding_model(self):
        if self._embedding_model is None:
            self._embedding_model = get_embedding_model()
        return self._embedding_model
    
    def index_directories(
        self,
        directories: List[str],
        options: Optional[EnumerationOptions] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> IndexingResult:
        """
        Index all files in the given directories.
        
        Args:
            directories: List of directory paths to index.
            options: Enumeration options.
            progress_callback: Optional callback for progress updates.
        
        Returns:
            IndexingResult with statistics.
        """
        start_time = time.time()
        result = IndexingResult()
        progress = IndexingProgress()
        
        try:
            # Step 1: Enumerate files
            enum_result = enumerate_files(directories, options)
            all_files = enum_result.files
            
            # Step 2: Determine what needs indexing
            new_files, modified_files, unchanged_files = get_files_to_reindex(
                all_files, self.manifest
            )
            deleted_files = get_deleted_files(all_files, self.manifest)
            
            progress.total_files = len(new_files) + len(modified_files) + len(deleted_files)
            progress.new_files = len(new_files)
            progress.modified_files = len(modified_files)
            progress.deleted_files = len(deleted_files)
            progress.skipped_files = len(unchanged_files)
            
            # Step 3: Handle deleted files
            for path in deleted_files:
                self._handle_deleted_file(path)
                progress.processed_files += 1
                result.deleted_files += 1
                if progress_callback:
                    progress_callback(progress)
            
            # Step 4: Index new and modified files
            files_to_index = new_files + modified_files
            for path in files_to_index:
                progress.current_file = path
                
                try:
                    indexed = self._index_file(path)
                    if indexed:
                        result.indexed_files += 1
                        if is_content_indexed(path):
                            result.content_indexed += 1
                        else:
                            result.metadata_only += 1
                except Exception as e:
                    error_msg = f"Error indexing {path}: {str(e)}"
                    progress.errors.append(error_msg)
                    result.errors.append(error_msg)
                    result.error_count += 1
                
                progress.processed_files += 1
                if progress_callback:
                    progress_callback(progress)
            
            # Step 5: Save stores
            self.manifest.save()
            self.bm25_store.save()
            
            result.total_files = len(all_files)
            result.success = result.error_count == 0
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Indexing failed: {str(e)}")
        
        result.elapsed_seconds = time.time() - start_time
        return result
    
    def _index_file(self, file_path: str) -> bool:
        """
        Index a single file.
        
        Returns:
            True if successfully indexed.
        """
        path = Path(file_path)
        if not path.exists():
            return False
        
        stat = path.stat()
        category, file_type = classify_file(file_path)
        
        # Create FileRecord
        file_id = str(uuid.uuid4())
        file_record = FileRecord(
            file_id=file_id,
            source=SourceType.LOCAL,
            content_indexed=(category == FileCategory.CONTENT_INDEXED),
            path=file_path,
            filename=path.name,
            extension=path.suffix.lower(),
            size_bytes=stat.st_size,
            created_at=stat.st_ctime,
            modified_at=stat.st_mtime,
            fingerprint=Fingerprint(
                size_bytes=stat.st_size,
                modified_at=stat.st_mtime,
            ),
        )
        
        # Remove old data if exists
        old_fp = self.manifest.get_fingerprint(file_path)
        if old_fp:
            self._remove_file_data(old_fp.file_id)
        
        if category == FileCategory.CONTENT_INDEXED:
            # Full content indexing
            self._index_content(file_path, file_id, file_record)
        else:
            # Metadata-only indexing
            self._index_metadata_only(file_path, file_id, file_record)
        
        # Update manifest
        self.manifest.set_fingerprint(file_path, FileFingerprint(
            file_id=file_id,
            size_bytes=stat.st_size,
            modified_at=stat.st_mtime,
            last_indexed_at=time.time(),
            content_indexed=file_record.content_indexed,
        ))
        
        return True
    
    def _index_content(
        self,
        file_path: str,
        file_id: str,
        file_record: FileRecord,
    ) -> None:
        """Index file with full content extraction."""
        # Extract content
        extractor = get_extractor_for_file(file_path)
        if extractor is None:
            return
        
        result = extractor.extract(file_path)
        if not result.success:
            return
        
        # Update file record with metadata
        if result.metadata.get("author"):
            file_record.author = result.metadata["author"]
        
        # Chunk content
        chunks = chunk_content(file_path, result)
        if not chunks:
            return
        
        # Create ChunkRecords
        chunk_records = []
        bm25_docs = []
        
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            
            # Tokenize for BM25
            tokens = tokenize(chunk.text)
            
            # Generate embedding
            embedding = None
            if self.embedding_model.is_available():
                embedding = self.embedding_model.encode_query(chunk.text)
            
            chunk_record = ChunkRecord(
                chunk_id=chunk_id,
                file_id=file_id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                embedding=embedding,
                tokens=tokens,
                metadata=ChunkMetadata(
                    page=chunk.page,
                    slide=chunk.slide,
                    slide_title=chunk.slide_title,
                    sheet=chunk.sheet,
                    row_range=chunk.row_range,
                    header_path=chunk.header_path,
                ),
            )
            chunk_records.append(chunk_record)
            
            # Add to BM25
            if tokens:
                bm25_docs.append((chunk_id, file_id, tokens, False))
        
        # Store in vector store
        if LANCEDB_AVAILABLE and chunk_records:
            try:
                self.vector_store.add_chunks(chunk_records)
            except Exception:
                pass  # Skip if LanceDB not available
        
        # Store in BM25
        if bm25_docs:
            self.bm25_store.add_documents(bm25_docs)
        
        # Update file record stats
        file_record.index_stats = IndexStats(
            chunk_count=len(chunk_records),
            last_indexed_at=time.time(),
        )
    
    def _index_metadata_only(
        self,
        file_path: str,
        file_id: str,
        file_record: FileRecord,
    ) -> None:
        """Index file with metadata only (filename, path)."""
        path = Path(file_path)
        
        # Create searchable text from filename and path
        filename_text = path.stem.replace("_", " ").replace("-", " ")
        tokens = tokenize(filename_text)
        
        # Add path components as tokens
        for part in path.parts[-3:]:  # Last 3 path components
            tokens.extend(tokenize(part.replace("_", " ").replace("-", " ")))
        
        if tokens:
            # Add as file-level BM25 document
            self.bm25_store.add_document(
                doc_id=file_id,
                file_id=file_id,
                tokens=tokens,
                is_file_level=True,
            )
    
    def _handle_deleted_file(self, file_path: str) -> None:
        """Handle a file that was deleted from disk."""
        fp = self.manifest.get_fingerprint(file_path)
        if fp:
            self._remove_file_data(fp.file_id)
            self.manifest.remove_fingerprint(file_path)
    
    def _remove_file_data(self, file_id: str) -> None:
        """Remove all stored data for a file."""
        # Remove from vector store
        if LANCEDB_AVAILABLE:
            try:
                self.vector_store.delete_by_file(file_id)
            except Exception:
                pass
        
        # Remove from BM25
        self.bm25_store.remove_by_file(file_id)
    
    def clear_all(self) -> None:
        """Clear all indexed data."""
        self.manifest.clear()
        if LANCEDB_AVAILABLE:
            try:
                self.vector_store.clear()
            except Exception:
                pass
        self.bm25_store.clear()


def get_indexing_orchestrator() -> IndexingOrchestrator:
    """Get an indexing orchestrator instance."""
    return IndexingOrchestrator()


__all__ = [
    "IndexingProgress",
    "IndexingResult",
    "IndexingOrchestrator",
    "get_indexing_orchestrator",
]
