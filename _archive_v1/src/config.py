# src/config.py
# Phase 1: 3.2. config.py 상세 요구사항에 따라 구현

from dataclasses import dataclass, field, asdict
import os
import json

@dataclass
class AppConfig:
    mode: str = "pro"    # free 또는 pro (개발 모드에서는 pro 기본)
    debug: bool = True   # 개발 모드 출력 여부

@dataclass
class ExcelSettings:
    limit_rows: bool = True
    max_rows_per_sheet: int = 5000
    skip_raw_like_sheets: bool = True

@dataclass
class IndexingSettings:
    """인덱싱 성능 설정 - Auto 모드 지원"""
    performance_mode: str = "auto"  # auto, power_saving, balanced, high_performance
    parallel_workers: int = 2
    skip_large_files: bool = True
    max_file_size_mb: int = 50
    excel: ExcelSettings = field(default_factory=ExcelSettings)
    
    # Auto tuning fields
    use_auto_tuning: bool = True  # True when Auto mode is active
    recommended_mode: str = "balanced"  # Actual recommended mode for this PC
    recommended_comment: str = ""  # e.g., "8 cores, 32GB RAM"
    
    # Mode presets
    MODE_PRESETS = {
        "power_saving": {
            "parallel_workers": 1,
            "max_file_size_mb": 20,
            "excel_max_rows": 3000
        },
        "balanced": {
            "parallel_workers": 2,
            "max_file_size_mb": 50,
            "excel_max_rows": 5000
        },
        "high_performance": {
            "parallel_workers": 4,
            "max_file_size_mb": 100,
            "excel_max_rows": 10000
        }
    }
    
    def apply_mode_preset(self, mode: str):
        """Apply preset values for the given mode."""
        if mode in self.MODE_PRESETS:
            preset = self.MODE_PRESETS[mode]
            self.performance_mode = mode
            self.parallel_workers = min(preset["parallel_workers"], os.cpu_count() or 2)
            self.max_file_size_mb = preset["max_file_size_mb"]
            self.excel.max_rows_per_sheet = preset["excel_max_rows"]
            self.use_auto_tuning = False
    
    def apply_auto_tuning(self):
        """Apply auto-tuned settings based on system profile."""
        try:
            # Try relative import first, then absolute
            try:
                from .system_profile import recommend_indexing_profile
            except ImportError:
                from system_profile import recommend_indexing_profile
            
            profile = recommend_indexing_profile()
            self.performance_mode = "auto"
            self.use_auto_tuning = True
            self.parallel_workers = profile.parallel_workers
            self.max_file_size_mb = profile.max_file_size_mb
            self.excel.max_rows_per_sheet = profile.excel_max_rows
            self.excel.skip_raw_like_sheets = profile.excel_skip_raw_like_sheets
            self.recommended_mode = profile.mode
            self.recommended_comment = profile.comment
        except Exception as e:
            print(f"Warning: Could not apply auto tuning: {e}")
            self.performance_mode = "balanced"
            self.use_auto_tuning = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "performance_mode": self.performance_mode,
            "parallel_workers": self.parallel_workers,
            "skip_large_files": self.skip_large_files,
            "max_file_size_mb": self.max_file_size_mb,
            "use_auto_tuning": self.use_auto_tuning,
            "excel": {
                "limit_rows": self.excel.limit_rows,
                "max_rows_per_sheet": self.excel.max_rows_per_sheet,
                "skip_raw_like_sheets": self.excel.skip_raw_like_sheets
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "IndexingSettings":
        """Create from dictionary."""
        excel_data = data.get("excel", {})
        excel = ExcelSettings(
            limit_rows=excel_data.get("limit_rows", True),
            max_rows_per_sheet=excel_data.get("max_rows_per_sheet", 5000),
            skip_raw_like_sheets=excel_data.get("skip_raw_like_sheets", True)
        )
        return cls(
            performance_mode=data.get("performance_mode", "auto"),
            parallel_workers=data.get("parallel_workers", 2),
            skip_large_files=data.get("skip_large_files", True),
            max_file_size_mb=data.get("max_file_size_mb", 50),
            use_auto_tuning=data.get("use_auto_tuning", True),
            excel=excel
        )


# Settings file path
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "..", "settings.json")

def load_indexing_settings() -> IndexingSettings:
    """Load indexing settings from file and apply auto tuning if needed."""
    settings = IndexingSettings()
    
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                settings = IndexingSettings.from_dict(data.get("indexing", {}))
    except Exception as e:
        print(f"Warning: Could not load settings: {e}")
    
    # Always get system recommendation for display
    try:
        # Try relative import first, then absolute
        try:
            from .system_profile import recommend_indexing_profile
        except ImportError:
            from system_profile import recommend_indexing_profile
        
        profile = recommend_indexing_profile()
        settings.recommended_mode = profile.mode
        settings.recommended_comment = profile.comment
        
        # Apply auto tuning if mode is "auto"
        if settings.performance_mode == "auto" or settings.use_auto_tuning:
            settings.parallel_workers = profile.parallel_workers
            settings.max_file_size_mb = profile.max_file_size_mb
            settings.excel.max_rows_per_sheet = profile.excel_max_rows
            settings.excel.skip_raw_like_sheets = profile.excel_skip_raw_like_sheets
    except Exception as e:
        print(f"Warning: Could not get system profile: {e}")
        settings.recommended_mode = "balanced"
        settings.recommended_comment = "Unknown specs"
    
    return settings

def save_indexing_settings(settings: IndexingSettings):
    """Save indexing settings to file."""
    try:
        existing = {}
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        
        existing["indexing"] = settings.to_dict()
        
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save settings: {e}")


def load_config() -> AppConfig:
    """
    환경 변수 또는 기본값을 기반으로 AppConfig를 생성한다.
    Free/Pro 검색 품질 차이는 절대로 없음.
    
    개발 모드(debug=True)에서는 기본적으로 Pro 모드로 실행.
    정식 배포 시 debug=False로 변경하면 Free 모드가 기본값.
    """
    debug = os.getenv("APP_DEBUG", "1") == "1"
    
    # 개발 모드에서는 Pro 기본, 배포 모드에서는 Free 기본
    default_mode = "pro" if debug else "free"
    mode = os.getenv("APP_MODE", default_mode).lower()

    if mode not in ("free", "pro"):
        mode = default_mode

    return AppConfig(mode=mode, debug=debug)

