# src/audit/logger.py
# Phase 3: 6.2. logger.py 예시에 따라 구현

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any


class AuditLogger:
    """
    엔터프라이즈용 Audit Log.
    
    조직 관리자가 사용자별 검색/인덱싱 활동을 추적할 수 있도록 함.
    Pro(특히 팀/엔터프라이즈 플랜)에서만 활성화.
    
    Audit 로그는 검색 품질을 바꾸지 않는다.
    단지 "무엇이 있었는지 기록"만 하는 역할이다.
    """
    
    def __init__(self, path: str = "~/.localfilesearch/audit.log"):
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

    def log_search(self, user_id: str, query: str, sources: List[str], 
                   result_count: int = 0) -> None:
        """검색 활동 로깅."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "search",
            "user_id": user_id,
            "query": query,
            "sources": sources,
            "result_count": result_count
        }
        self._write(entry)

    def log_indexing(self, user_id: str, connector_type: str, 
                     indexed_count: int = 0, errors: int = 0) -> None:
        """인덱싱 활동 로깅."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "indexing",
            "user_id": user_id,
            "connector": connector_type,
            "indexed_count": indexed_count,
            "errors": errors
        }
        self._write(entry)

    def log_login(self, user_id: str, success: bool, method: str = "token") -> None:
        """로그인 활동 로깅."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "login",
            "user_id": user_id,
            "success": success,
            "method": method
        }
        self._write(entry)

    def log_admin_action(self, user_id: str, action: str, 
                         target: Optional[str] = None) -> None:
        """관리자 작업 로깅."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "admin_action",
            "user_id": user_id,
            "action": action,
            "target": target
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

    def read_logs(self, limit: int = 100, 
                  log_type: Optional[str] = None,
                  user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        로그 읽기 (Admin UI용).
        
        Args:
            limit: 최대 반환 개수
            log_type: 필터링할 로그 타입 (search, indexing, login, admin_action)
            user_id: 필터링할 사용자 ID
            
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
                        if log_type and entry.get("type") != log_type:
                            continue
                        if user_id and entry.get("user_id") != user_id:
                            continue
                        
                        logs.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            # 최신순 정렬, limit 적용
            logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return logs[:limit]
            
        except IOError:
            return []

    def export_logs(self, output_path: str) -> bool:
        """로그 파일 내보내기."""
        try:
            if self.path.exists():
                import shutil
                shutil.copy(self.path, output_path)
            return True
        except IOError:
            return False

    def clear_logs(self) -> bool:
        """로그 삭제."""
        try:
            if self.path.exists():
                self.path.unlink()
            return True
        except IOError:
            return False
