# src/licensing/token_store.py
# Phase 2: 1.3. TokenStore 구현 사양에 따라 구현

import json
from pathlib import Path
from typing import Optional, Dict, Any

class TokenStore:
    """
    라이선스 서버에서 받은 토큰을 디스크에 저장/로드.
    - 앱 실행 시 자동 로딩
    - 토큰이 없으면 Free로 동작
    """
    def __init__(self, file_path: str = "~/.localfilesearch/license.json"):
        self.path = Path(file_path).expanduser()

    def load(self) -> Optional[Dict[str, Any]]:
        """저장된 토큰 데이터를 로드. 없으면 None 반환."""
        if not self.path.exists():
            return None
        try:
            return json.loads(self.path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, IOError):
            return None

    def save(self, token_data: Dict[str, Any]) -> bool:
        """토큰 데이터를 디스크에 저장."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(token_data, ensure_ascii=False, indent=2), encoding='utf-8')
            return True
        except IOError:
            return False

    def clear(self) -> bool:
        """저장된 토큰 삭제."""
        try:
            if self.path.exists():
                self.path.unlink()
            return True
        except IOError:
            return False
