# src/security/call_logger.py
# Transparency Layer: 2.3. ExternalCallLog 사양에 따라 구현

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any


class ExternalCallLogger:
    """
    외부 HTTP 호출 로깅.
    
    모든 외부 통신을 투명하게 기록하여 사용자가 확인할 수 있도록 함.
    검색 품질에 영향 없음 — 로깅만 수행.
    """
    
    def __init__(self, path: str = "~/.localfilesearch/external_calls.log"):
        self.path = Path(path).expanduser()
        self._enabled = True

    def enable(self) -> None:
        """로깅 활성화."""
        self._enabled = True

    def disable(self) -> None:
        """로깅 비활성화."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """로깅 활성화 여부."""
        return self._enabled

    def log_call(self, 
                 url: str, 
                 method: str = "GET",
                 allowed: bool = True,
                 reason: Optional[str] = None,
                 response_status: Optional[int] = None,
                 data_size_bytes: int = 0) -> None:
        """
        외부 호출 로그 기록.
        
        Args:
            url: 대상 URL
            method: HTTP 메서드
            allowed: 정책에 의해 허용 여부
            reason: 차단/허용 이유
            response_status: HTTP 응답 코드
            data_size_bytes: 전송 데이터 크기
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "url": url,
            "method": method,
            "allowed": allowed,
            "reason": reason,
            "response_status": response_status,
            "data_size_bytes": data_size_bytes,
        }
        self._write(entry)

    def _write(self, entry: Dict[str, Any]) -> None:
        """로그 엔트리 작성."""
        if not self._enabled:
            return
        
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except IOError:
            pass  # 로그 실패는 무시

    def read_logs(self, 
                  limit: int = 100,
                  allowed_only: Optional[bool] = None,
                  url_contains: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        로그 읽기 (UI용).
        
        Args:
            limit: 최대 반환 개수
            allowed_only: True면 허용된 호출만, False면 차단된 호출만
            url_contains: URL 필터
            
        Returns:
            로그 엔트리 목록 (최신순)
        """
        if not self.path.exists():
            return []
        
        try:
            logs = []
            with self.path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        
                        # 필터링
                        if allowed_only is not None:
                            if entry.get("allowed") != allowed_only:
                                continue
                        
                        if url_contains:
                            if url_contains.lower() not in entry.get("url", "").lower():
                                continue
                        
                        logs.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            # 최신순 정렬
            logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return logs[:limit]
            
        except IOError:
            return []

    def get_stats(self) -> Dict[str, int]:
        """통계 조회."""
        logs = self.read_logs(limit=10000)
        
        allowed_count = sum(1 for log in logs if log.get("allowed"))
        blocked_count = sum(1 for log in logs if not log.get("allowed"))
        
        return {
            "total": len(logs),
            "allowed": allowed_count,
            "blocked": blocked_count,
        }

    def clear_logs(self) -> bool:
        """로그 삭제."""
        try:
            if self.path.exists():
                self.path.unlink()
            return True
        except IOError:
            return False

    def export_logs(self, output_path: str) -> bool:
        """로그 파일 내보내기."""
        try:
            if self.path.exists():
                import shutil
                shutil.copy(self.path, output_path)
            return True
        except IOError:
            return False
