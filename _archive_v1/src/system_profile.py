# src/system_profile.py
"""
System profile detection for automatic performance tuning.
Detects CPU cores and RAM to recommend optimal indexing settings.
"""
from dataclasses import dataclass
from typing import Literal
import psutil

PerformanceMode = Literal["auto", "power_saving", "balanced", "high_performance"]


@dataclass
class SystemSpecs:
    """Detected system hardware specifications."""
    physical_cores: int
    logical_cores: int
    ram_gb: float


@dataclass
class RecommendedIndexingProfile:
    """Recommended indexing settings based on system specs."""
    mode: PerformanceMode  # Actual recommended mode (not "auto")
    parallel_workers: int
    max_file_size_mb: int
    excel_max_rows: int
    excel_skip_raw_like_sheets: bool
    comment: str  # e.g., "8 cores, 32GB RAM"


def get_system_specs() -> SystemSpecs:
    """Detect system CPU cores and RAM."""
    physical = psutil.cpu_count(logical=False) or 1
    logical = psutil.cpu_count(logical=True) or physical
    ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    return SystemSpecs(
        physical_cores=physical,
        logical_cores=logical,
        ram_gb=round(ram_gb, 1),
    )


def recommend_indexing_profile() -> RecommendedIndexingProfile:
    """
    Calculate recommended indexing profile based on system specs.
    
    Returns profile with optimal settings for the detected hardware.
    """
    specs = get_system_specs()
    cores = specs.physical_cores
    ram = specs.ram_gb

    # Default values (conservative)
    mode: PerformanceMode = "power_saving"
    workers = 1
    max_file_size_mb = 20
    excel_max_rows = 3000
    skip_raw_like = True

    # High Performance: 8+ cores, 24+ GB RAM
    if cores >= 8 and ram >= 24:
        mode = "high_performance"
        workers = min(8, cores)  # Cap at 8 workers
        max_file_size_mb = 100
        excel_max_rows = 10000
        skip_raw_like = True
    # Balanced: 6+ cores, 12+ GB RAM
    elif cores >= 6 and ram >= 12:
        mode = "balanced"
        workers = min(4, cores)
        max_file_size_mb = 50
        excel_max_rows = 5000
        skip_raw_like = True
    # Power Saving: 4+ cores, 8+ GB RAM
    elif cores >= 4 and ram >= 8:
        mode = "power_saving"
        workers = 2
        max_file_size_mb = 30
        excel_max_rows = 3000
        skip_raw_like = True
    else:
        # Very low spec (2 cores, 4GB, etc.) - very conservative
        mode = "power_saving"
        workers = 1
        max_file_size_mb = 20
        excel_max_rows = 2000
        skip_raw_like = True

    comment = f"{specs.physical_cores} cores, {specs.ram_gb} GB RAM"

    return RecommendedIndexingProfile(
        mode=mode,
        parallel_workers=workers,
        max_file_size_mb=max_file_size_mb,
        excel_max_rows=excel_max_rows,
        excel_skip_raw_like_sheets=skip_raw_like,
        comment=comment,
    )
