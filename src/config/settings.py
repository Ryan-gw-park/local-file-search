"""
Local Finder X v2.0 - Application Settings

Settings management with JSON persistence.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

from .paths import get_settings_path


@dataclass
class IndexingSettings:
    """Settings for the indexing process."""
    max_file_size_mb: int = 100
    skip_hidden_files: bool = True
    parallel_workers: int = 4
    chunk_size: int = 1000
    chunk_overlap: int = 100


@dataclass
class SearchSettings:
    """Settings for the search process."""
    mode: str = "SMART"  # FAST, SMART, ASSIST
    top_n_dense: int = 50
    top_n_bm25: int = 50
    rrf_k: int = 60
    max_evidences_per_file: int = 5


@dataclass
class UISettings:
    """Settings for the UI."""
    theme: str = "system"  # light, dark, system
    language: str = "ko"  # ko, en
    left_panel_width: int = 300
    right_panel_width: int = 400


@dataclass
class LicenseSettings:
    """Settings for license management."""
    license_key: Optional[str] = None
    is_pro: bool = False


@dataclass
class AppSettings:
    """Main application settings container."""
    schema_version: str = "2.0"
    indexing: IndexingSettings = field(default_factory=IndexingSettings)
    search: SearchSettings = field(default_factory=SearchSettings)
    ui: UISettings = field(default_factory=UISettings)
    license: LicenseSettings = field(default_factory=LicenseSettings)
    indexed_folders: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary for JSON serialization."""
        return {
            "schema_version": self.schema_version,
            "indexing": asdict(self.indexing),
            "search": asdict(self.search),
            "ui": asdict(self.ui),
            "license": asdict(self.license),
            "indexed_folders": self.indexed_folders,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        """Create settings from dictionary."""
        return cls(
            schema_version=data.get("schema_version", "2.0"),
            indexing=IndexingSettings(**data.get("indexing", {})),
            search=SearchSettings(**data.get("search", {})),
            ui=UISettings(**data.get("ui", {})),
            license=LicenseSettings(**data.get("license", {})),
            indexed_folders=data.get("indexed_folders", []),
        )


class SettingsManager:
    """
    Singleton settings manager for the application.
    Handles loading and saving settings to JSON file.
    """
    
    _instance: Optional["SettingsManager"] = None
    _settings: Optional[AppSettings] = None
    
    def __new__(cls) -> "SettingsManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._settings is None:
            self.load()
    
    @property
    def settings(self) -> AppSettings:
        """Get the current settings."""
        if self._settings is None:
            self.load()
        return self._settings  # type: ignore
    
    def load(self) -> AppSettings:
        """Load settings from file. Creates default if not exists."""
        settings_path = get_settings_path()
        
        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._settings = AppSettings.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load settings, using defaults: {e}")
                self._settings = AppSettings()
                self.save()
        else:
            self._settings = AppSettings()
            self.save()
        
        return self._settings
    
    def save(self) -> None:
        """Save current settings to file."""
        if self._settings is None:
            return
        
        settings_path = get_settings_path()
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(self._settings.to_dict(), f, indent=2, ensure_ascii=False)
    
    def reset(self) -> None:
        """Reset settings to defaults."""
        self._settings = AppSettings()
        self.save()


# Convenience function
def get_settings() -> AppSettings:
    """Get the current application settings."""
    return SettingsManager().settings


def save_settings() -> None:
    """Save the current application settings."""
    SettingsManager().save()


__all__ = [
    "AppSettings",
    "IndexingSettings",
    "SearchSettings",
    "UISettings",
    "LicenseSettings",
    "SettingsManager",
    "get_settings",
    "save_settings",
]
