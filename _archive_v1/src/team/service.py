# src/team/service.py
# Phase 3: 2.2. 코드 구조 - service.py 예시에 따라 구현

import json
from pathlib import Path
from typing import Optional, List
from .models import TeamConfig, TeamMember


class TeamService:
    """
    팀 관련 로직 (설정 저장/로드 등).
    
    팀 기능은 검색 품질에 영향을 주지 않으며,
    여러 사용자가 공용 커넥터를 공유할 수 있는 구조만 제공한다.
    """
    
    def __init__(self, storage_path: str = "~/.localfilesearch/team.json"):
        self.storage_path = Path(storage_path).expanduser()

    def load_team_config(self) -> Optional[TeamConfig]:
        """저장된 팀 설정 로드."""
        if not self.storage_path.exists():
            return None
        
        try:
            data = json.loads(self.storage_path.read_text(encoding='utf-8'))
            
            # TeamMember 객체 복원
            members = [
                TeamMember(
                    user_id=m["user_id"],
                    role=m["role"],
                    email=m.get("email"),
                    display_name=m.get("display_name")
                )
                for m in data.get("members", [])
            ]
            
            return TeamConfig(
                team_id=data["team_id"],
                team_name=data.get("team_name", ""),
                members=members,
                connectors=data.get("connectors", {})
            )
        except (json.JSONDecodeError, KeyError, IOError):
            return None

    def save_team_config(self, config: TeamConfig) -> bool:
        """팀 설정 저장."""
        try:
            data = {
                "team_id": config.team_id,
                "team_name": config.team_name,
                "members": [
                    {
                        "user_id": m.user_id,
                        "role": m.role,
                        "email": m.email,
                        "display_name": m.display_name
                    }
                    for m in config.members
                ],
                "connectors": config.connectors
            }
            
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            return True
        except IOError:
            return False

    def clear_team_config(self) -> bool:
        """팀 설정 삭제."""
        try:
            if self.storage_path.exists():
                self.storage_path.unlink()
            return True
        except IOError:
            return False

    def has_team(self) -> bool:
        """팀 설정이 존재하는지 확인."""
        config = self.load_team_config()
        return config is not None
