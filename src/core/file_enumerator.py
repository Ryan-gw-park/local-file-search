"""
Local Finder X v2.0 - File Enumerator

Enumerates files in directories with filtering rules.
Based on Master Plan Phase 3 specifications.
"""

import os
from pathlib import Path
from typing import List, Set, Optional, Iterator, Callable
from dataclasses import dataclass, field


# =============================================================================
# Constants
# =============================================================================

# Directories to skip during enumeration
SKIP_DIRECTORIES: Set[str] = {
    # System directories
    "$recycle.bin",
    "appdata",
    "programdata",
    "windows",
    "program files",
    "program files (x86)",
    # Development directories
    "__pycache__",
    "node_modules",
    ".git",
    ".svn",
    ".hg",
    "venv",
    "env",
    ".env",
    ".venv",
    # Cache directories
    "temp",
    "tmp",
    "cache",
    ".cache",
    # macOS specific
    ".Spotlight-V100",
    ".Trashes",
    ".fseventsd",
}

# File patterns to skip
SKIP_FILE_PREFIXES: Set[str] = {
    "~$",  # Office temp files
    ".",   # Hidden files
}

SKIP_FILE_SUFFIXES: Set[str] = {
    ".tmp",
    ".temp",
    ".bak",
    ".swp",
    ".swo",
    ".pyc",
    ".pyo",
    ".class",
    ".o",
    ".obj",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class EnumerationResult:
    """Result of file enumeration."""
    files: List[str] = field(default_factory=list)
    skipped_dirs: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class EnumerationOptions:
    """Options for file enumeration."""
    include_hidden: bool = False
    max_depth: Optional[int] = None
    max_file_size_bytes: Optional[int] = None  # Skip files larger than this
    extensions_filter: Optional[Set[str]] = None  # Only include these extensions
    exclude_patterns: Optional[Set[str]] = None  # Additional patterns to exclude


# =============================================================================
# Core Functions
# =============================================================================

def should_skip_directory(dir_name: str, dir_path: str, options: EnumerationOptions) -> bool:
    """
    Check if a directory should be skipped.
    
    Args:
        dir_name: Name of the directory.
        dir_path: Full path to the directory.
        options: Enumeration options.
    
    Returns:
        True if the directory should be skipped.
    """
    # Skip hidden directories (unless explicitly included)
    if dir_name.startswith(".") and not options.include_hidden:
        return True
    
    # Skip known system/cache directories
    if dir_name.lower() in SKIP_DIRECTORIES:
        return True
    
    return False


def should_skip_file(
    filename: str,
    file_path: str,
    options: EnumerationOptions,
) -> bool:
    """
    Check if a file should be skipped.
    
    Args:
        filename: Name of the file.
        file_path: Full path to the file.
        options: Enumeration options.
    
    Returns:
        True if the file should be skipped.
    """
    # Skip by prefix
    for prefix in SKIP_FILE_PREFIXES:
        if filename.startswith(prefix):
            if prefix == "." and options.include_hidden:
                continue
            return True
    
    # Skip by suffix
    lower_name = filename.lower()
    for suffix in SKIP_FILE_SUFFIXES:
        if lower_name.endswith(suffix):
            return True
    
    # Skip by size (if specified)
    if options.max_file_size_bytes is not None:
        try:
            size = Path(file_path).stat().st_size
            if size > options.max_file_size_bytes:
                return True
        except OSError:
            pass
    
    # Filter by extensions (if specified)
    if options.extensions_filter is not None:
        ext = Path(filename).suffix.lower()
        if ext not in options.extensions_filter:
            return True
    
    # Skip by custom patterns
    if options.exclude_patterns:
        for pattern in options.exclude_patterns:
            if pattern in filename or pattern in file_path:
                return True
    
    return False


def enumerate_files(
    root_paths: List[str],
    options: Optional[EnumerationOptions] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> EnumerationResult:
    """
    Enumerate all files in the given directories.
    
    Args:
        root_paths: List of root directory paths to enumerate.
        options: Enumeration options.
        progress_callback: Optional callback for progress updates.
    
    Returns:
        EnumerationResult with lists of files, skipped items, and errors.
    """
    if options is None:
        options = EnumerationOptions()
    
    result = EnumerationResult()
    
    for root_path in root_paths:
        root = Path(root_path)
        
        if not root.exists():
            result.errors.append(f"Path does not exist: {root_path}")
            continue
        
        if not root.is_dir():
            # Single file
            if not should_skip_file(root.name, str(root), options):
                result.files.append(str(root))
            continue
        
        # Walk the directory tree
        for current_root, dirs, files in os.walk(root):
            current_path = Path(current_root)
            current_depth = len(current_path.relative_to(root).parts)
            
            # Check max depth
            if options.max_depth is not None and current_depth >= options.max_depth:
                dirs.clear()
                continue
            
            # Filter directories (modifies in place)
            dirs_to_remove = []
            for d in dirs:
                dir_path = os.path.join(current_root, d)
                if should_skip_directory(d, dir_path, options):
                    dirs_to_remove.append(d)
                    result.skipped_dirs.append(dir_path)
            
            for d in dirs_to_remove:
                dirs.remove(d)
            
            # Process files
            for f in files:
                file_path = os.path.join(current_root, f)
                
                if should_skip_file(f, file_path, options):
                    result.skipped_files.append(file_path)
                    continue
                
                result.files.append(file_path)
                
                if progress_callback:
                    progress_callback(file_path)
    
    return result


def enumerate_files_iterator(
    root_paths: List[str],
    options: Optional[EnumerationOptions] = None,
) -> Iterator[str]:
    """
    Iterator version of enumerate_files for memory efficiency.
    
    Args:
        root_paths: List of root directory paths.
        options: Enumeration options.
    
    Yields:
        File paths one at a time.
    """
    if options is None:
        options = EnumerationOptions()
    
    for root_path in root_paths:
        root = Path(root_path)
        
        if not root.exists():
            continue
        
        if not root.is_dir():
            if not should_skip_file(root.name, str(root), options):
                yield str(root)
            continue
        
        for current_root, dirs, files in os.walk(root):
            current_path = Path(current_root)
            
            # Filter directories
            dirs[:] = [
                d for d in dirs
                if not should_skip_directory(d, os.path.join(current_root, d), options)
            ]
            
            # Yield files
            for f in files:
                file_path = os.path.join(current_root, f)
                if not should_skip_file(f, file_path, options):
                    yield file_path


__all__ = [
    "SKIP_DIRECTORIES",
    "SKIP_FILE_PREFIXES",
    "SKIP_FILE_SUFFIXES",
    "EnumerationResult",
    "EnumerationOptions",
    "should_skip_directory",
    "should_skip_file",
    "enumerate_files",
    "enumerate_files_iterator",
]
