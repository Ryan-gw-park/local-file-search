"""
Local Finder X v2.0 - Manifest Store

Manages file fingerprints for incremental indexing.
Tracks which files have been indexed and their modification state.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Optional, List, Tuple

from src.config.paths import get_manifest_path


@dataclass
class FileFingerprint:
    """Fingerprint for a single file."""
    file_id: str
    size_bytes: int
    modified_at: float
    last_indexed_at: float
    content_indexed: bool = False
    hash: Optional[str] = None


@dataclass
class Manifest:
    """
    Manifest containing all indexed file fingerprints.
    Used for incremental indexing decisions.
    """
    schema_version: str = "2.0"
    files: Dict[str, FileFingerprint] = field(default_factory=dict)
    last_updated_at: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema_version": self.schema_version,
            "files": {
                path: {
                    "file_id": fp.file_id,
                    "size_bytes": fp.size_bytes,
                    "modified_at": fp.modified_at,
                    "last_indexed_at": fp.last_indexed_at,
                    "content_indexed": fp.content_indexed,
                    "hash": fp.hash,
                }
                for path, fp in self.files.items()
            },
            "last_updated_at": self.last_updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Manifest":
        """Create from dictionary."""
        files = {}
        for path, fp_data in data.get("files", {}).items():
            files[path] = FileFingerprint(
                file_id=fp_data.get("file_id", ""),
                size_bytes=fp_data.get("size_bytes", 0),
                modified_at=fp_data.get("modified_at", 0.0),
                last_indexed_at=fp_data.get("last_indexed_at", 0.0),
                content_indexed=fp_data.get("content_indexed", False),
                hash=fp_data.get("hash"),
            )
        return cls(
            schema_version=data.get("schema_version", "2.0"),
            files=files,
            last_updated_at=data.get("last_updated_at", 0.0),
        )


class ManifestStore:
    """
    Singleton store for managing the manifest.
    Handles loading, saving, and querying file fingerprints.
    """
    
    _instance: Optional["ManifestStore"] = None
    _manifest: Optional[Manifest] = None
    
    def __new__(cls) -> "ManifestStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._manifest is None:
            self.load()
    
    @property
    def manifest(self) -> Manifest:
        """Get the current manifest."""
        if self._manifest is None:
            self.load()
        return self._manifest  # type: ignore
    
    def load(self) -> Manifest:
        """Load manifest from file. Creates new if not exists."""
        manifest_path = get_manifest_path()
        
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._manifest = Manifest.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load manifest, creating new: {e}")
                self._manifest = Manifest()
                self.save()
        else:
            self._manifest = Manifest()
            self.save()
        
        return self._manifest
    
    def save(self) -> None:
        """Save current manifest to file."""
        if self._manifest is None:
            return
        
        self._manifest.last_updated_at = time.time()
        manifest_path = get_manifest_path()
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(self._manifest.to_dict(), f, indent=2, ensure_ascii=False)
    
    def get_fingerprint(self, path: str) -> Optional[FileFingerprint]:
        """Get fingerprint for a file path."""
        return self.manifest.files.get(path)
    
    def set_fingerprint(self, path: str, fingerprint: FileFingerprint) -> None:
        """Set fingerprint for a file path."""
        self.manifest.files[path] = fingerprint
    
    def remove_fingerprint(self, path: str) -> None:
        """Remove fingerprint for a file path."""
        if path in self.manifest.files:
            del self.manifest.files[path]
    
    def has_file(self, path: str) -> bool:
        """Check if a file is in the manifest."""
        return path in self.manifest.files
    
    def get_all_paths(self) -> List[str]:
        """Get all indexed file paths."""
        return list(self.manifest.files.keys())
    
    def clear(self) -> None:
        """Clear all fingerprints."""
        self._manifest = Manifest()
        self.save()


def compare_fingerprint(
    current_size: int,
    current_mtime: float,
    stored: Optional[FileFingerprint],
) -> Tuple[bool, str]:
    """
    Compare current file state with stored fingerprint.
    
    Returns:
        Tuple of (needs_reindex: bool, reason: str)
    """
    if stored is None:
        return True, "new_file"
    
    if current_size != stored.size_bytes:
        return True, "size_changed"
    
    if current_mtime > stored.modified_at:
        return True, "modified"
    
    return False, "unchanged"


def get_files_to_reindex(
    file_paths: List[str],
    manifest_store: Optional[ManifestStore] = None,
) -> Tuple[List[str], List[str], List[str]]:
    """
    Determine which files need to be reindexed.
    
    Args:
        file_paths: List of file paths to check.
        manifest_store: Optional manifest store instance.
    
    Returns:
        Tuple of (new_files, modified_files, unchanged_files)
    """
    store = manifest_store or ManifestStore()
    
    new_files = []
    modified_files = []
    unchanged_files = []
    
    for path in file_paths:
        p = Path(path)
        if not p.exists():
            continue
        
        stat = p.stat()
        stored = store.get_fingerprint(path)
        needs_reindex, reason = compare_fingerprint(
            current_size=stat.st_size,
            current_mtime=stat.st_mtime,
            stored=stored,
        )
        
        if reason == "new_file":
            new_files.append(path)
        elif needs_reindex:
            modified_files.append(path)
        else:
            unchanged_files.append(path)
    
    return new_files, modified_files, unchanged_files


def get_deleted_files(
    current_paths: List[str],
    manifest_store: Optional[ManifestStore] = None,
) -> List[str]:
    """
    Find files that are in manifest but no longer exist on disk.
    
    Args:
        current_paths: List of currently existing file paths.
        manifest_store: Optional manifest store instance.
    
    Returns:
        List of deleted file paths.
    """
    store = manifest_store or ManifestStore()
    current_set = set(current_paths)
    stored_paths = store.get_all_paths()
    
    return [p for p in stored_paths if p not in current_set]


__all__ = [
    "FileFingerprint",
    "Manifest",
    "ManifestStore",
    "compare_fingerprint",
    "get_files_to_reindex",
    "get_deleted_files",
]
