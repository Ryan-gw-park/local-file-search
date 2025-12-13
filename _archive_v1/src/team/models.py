# src/team/models.py
# Phase 3: 2.2. 코드 구조 - models.py 예시에 따라 구현

from dataclasses import dataclass, field
from typing import Literal, List, Dict, Any, Optional

RoleType = Literal["admin", "member"]


@dataclass
class TeamMember:
    """팀 구성원 정보."""
    user_id: str
    role: RoleType
    email: Optional[str] = None
    display_name: Optional[str] = None


@dataclass
class TeamConfig:
    """
    팀 공용 설정.
    
    팀 기능은 Pro에서만 활성화되지만,
    이로 인해 검색 품질이 달라져선 안 된다.
    팀 기능은 "여러 사용자가 공용 커넥터를 공유할 수 있다"는 구조일 뿐.
    """
    team_id: str
    team_name: str = ""
    members: List[TeamMember] = field(default_factory=list)
    # 팀 공용 커넥터 설정
    connectors: Dict[str, Any] = field(default_factory=dict)
    # 예: {"onedrive": {"shared_folder": "..."}, "sharepoint": {"site_id": "..."}}
    
    def get_member(self, user_id: str) -> Optional[TeamMember]:
        """사용자 ID로 팀 멤버 조회."""
        for member in self.members:
            if member.user_id == user_id:
                return member
        return None
    
    def is_admin(self, user_id: str) -> bool:
        """사용자가 admin인지 확인."""
        member = self.get_member(user_id)
        return member is not None and member.role == "admin"
    
    def add_member(self, member: TeamMember) -> None:
        """팀 멤버 추가."""
        # 중복 제거
        self.members = [m for m in self.members if m.user_id != member.user_id]
        self.members.append(member)
    
    def remove_member(self, user_id: str) -> bool:
        """팀 멤버 제거."""
        original_count = len(self.members)
        self.members = [m for m in self.members if m.user_id != user_id]
        return len(self.members) < original_count
