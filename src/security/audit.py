"""
Local Finder X v2.0 - Audit Trail

Structured logging for search events and security auditing.
"""

import json
import time
import hashlib
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime

from src.config.paths import get_logs_dir


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AuditEvent:
    """Single audit event."""
    timestamp: str
    event_type: str
    query_hash: str = ""  # Hashed query for privacy
    user_id: str = ""
    files_accessed: List[str] = field(default_factory=list)
    file_count: int = 0
    pii_detected: bool = False
    elapsed_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


# =============================================================================
# Audit Logger
# =============================================================================

class AuditLogger:
    """
    Audit trail logger for search events.
    
    Logs are stored as structured JSON, one event per line.
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or get_logs_dir()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file: Optional[Path] = None
    
    @property
    def log_file(self) -> Path:
        """Get current log file (daily rotation)."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"audit_{today}.jsonl"
    
    def _hash_query(self, query: str) -> str:
        """Hash query for privacy."""
        return hashlib.sha256(query.encode()).hexdigest()[:16]
    
    def log_search(
        self,
        query: str,
        files_accessed: List[str],
        elapsed_ms: int = 0,
        pii_detected: bool = False,
        user_id: str = "",
    ) -> None:
        """
        Log a search event.
        
        Args:
            query: The search query (will be hashed).
            files_accessed: List of file paths accessed.
            elapsed_ms: Search time in milliseconds.
            pii_detected: Whether PII was detected in results.
            user_id: Optional user identifier.
        """
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type="search",
            query_hash=self._hash_query(query),
            user_id=user_id,
            files_accessed=files_accessed[:10],  # Limit to 10
            file_count=len(files_accessed),
            pii_detected=pii_detected,
            elapsed_ms=elapsed_ms,
        )
        
        self._write_event(event)
    
    def log_index(
        self,
        directories: List[str],
        file_count: int,
        elapsed_ms: int = 0,
        user_id: str = "",
    ) -> None:
        """Log an indexing event."""
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type="index",
            user_id=user_id,
            files_accessed=directories[:5],
            file_count=file_count,
            elapsed_ms=elapsed_ms,
        )
        
        self._write_event(event)
    
    def log_export(
        self,
        files: List[str],
        destination: str,
        user_id: str = "",
    ) -> None:
        """Log an export event."""
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type="export",
            user_id=user_id,
            files_accessed=files[:10],
            file_count=len(files),
        )
        
        self._write_event(event)
    
    def log_auth(
        self,
        success: bool,
        method: str,
        user_id: str = "",
    ) -> None:
        """Log an authentication event."""
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type=f"auth_{method}_{'success' if success else 'failure'}",
            user_id=user_id,
        )
        
        self._write_event(event)
    
    def _write_event(self, event: AuditEvent) -> None:
        """Write event to log file."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            print(f"Audit log error: {e}")
    
    def get_recent_events(self, count: int = 100) -> List[AuditEvent]:
        """
        Get recent audit events.
        
        Args:
            count: Number of events to retrieve.
        
        Returns:
            List of AuditEvent objects.
        """
        events = []
        
        try:
            if self.log_file.exists():
                with open(self.log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines[-count:]:
                        data = json.loads(line.strip())
                        events.append(AuditEvent(**data))
        except Exception as e:
            print(f"Error reading audit log: {e}")
        
        return events


# Singleton
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the singleton audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


__all__ = [
    "AuditEvent",
    "AuditLogger",
    "get_audit_logger",
]
