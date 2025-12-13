"""
Local Finder X v2.0 - Application Data Paths

OS-specific application data directory management.
Windows: %APPDATA%/LocalFinderX/
macOS: ~/Library/Application Support/LocalFinderX/
"""

import os
import sys
from pathlib import Path


def get_app_data_dir() -> Path:
    """
    Get the application data directory based on the operating system.
    Creates the directory if it doesn't exist.
    
    Returns:
        Path: The application data directory path.
    """
    if sys.platform == "win32":
        # Windows: %APPDATA%/LocalFinderX/
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        app_dir = Path(base) / "LocalFinderX"
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/LocalFinderX/
        app_dir = Path.home() / "Library" / "Application Support" / "LocalFinderX"
    else:
        # Linux/Other: ~/.local/share/LocalFinderX/
        xdg_data = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        app_dir = Path(xdg_data) / "LocalFinderX"
    
    # Create directory if it doesn't exist
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_data_dir() -> Path:
    """Get the data directory for storage (LanceDB, BM25, etc.)."""
    data_dir = get_app_data_dir() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_logs_dir() -> Path:
    """Get the logs directory."""
    logs_dir = get_app_data_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_config_dir() -> Path:
    """Get the config directory."""
    config_dir = get_app_data_dir() / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_lancedb_path() -> Path:
    """Get the LanceDB data directory path."""
    lancedb_dir = get_data_dir() / "lancedb"
    lancedb_dir.mkdir(parents=True, exist_ok=True)
    return lancedb_dir


def get_bm25_path() -> Path:
    """Get the BM25 index file path."""
    return get_data_dir() / "bm25.bin"


def get_manifest_path() -> Path:
    """Get the manifest file path."""
    return get_data_dir() / "manifest.json"


def get_settings_path() -> Path:
    """Get the settings file path."""
    return get_config_dir() / "settings.json"


# Convenience exports
__all__ = [
    "get_app_data_dir",
    "get_data_dir",
    "get_logs_dir",
    "get_config_dir",
    "get_lancedb_path",
    "get_bm25_path",
    "get_manifest_path",
    "get_settings_path",
]
