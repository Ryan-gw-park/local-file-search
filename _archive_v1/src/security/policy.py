# src/security/policy.py
# Transparency Layer: 2.2. SecurityPolicy 사양에 따라 구현

from enum import Enum
from typing import Optional, Set
import os


class SecurityMode(Enum):
    """
    보안 모드 정의.
    
    모든 모드에서 검색 품질은 동일 — 보안 모드는 외부 통신만 제어.
    """
    LOCAL_ONLY = "local_only"   # 모든 외부 HTTP 호출 차단 (완전 오프라인)
    RESTRICTED = "restricted"   # 허용 목록에 있는 도메인만 허용
    NORMAL = "normal"           # 일반 동작 (모든 외부 호출 허용)


class SecurityPolicy:
    """
    보안 정책 관리.
    
    핵심 원칙:
    - 사용자 문서 내용, 임베딩, 인덱스는 절대 외부로 전송하지 않음
    - 외부 호출은 메타데이터, 토큰, 명시적 파일 다운로드 용도로만 허용
    - 검색 품질은 모든 보안 모드에서 동일
    """
    
    # 기본 허용 도메인 (RESTRICTED 모드용)
    DEFAULT_ALLOWED_DOMAINS: Set[str] = {
        "graph.microsoft.com",      # MS Graph API (OneDrive, SharePoint)
        "login.microsoftonline.com", # MS OAuth
        "api.localfilesearch.com",  # 라이선스 서버 (가상)
    }
    
    # 금지된 데이터 패턴 (어떤 모드에서도 전송 금지)
    FORBIDDEN_DATA_PATTERNS = [
        "embedding",
        "vector",
        "document_content",
        "file_content",
    ]
    
    def __init__(self, mode: SecurityMode = None, 
                 allowed_domains: Optional[Set[str]] = None):
        """
        Args:
            mode: 보안 모드 (기본: 환경 변수 또는 NORMAL)
            allowed_domains: 추가 허용 도메인 목록
        """
        # 환경 변수에서 모드 로드
        if mode is None:
            env_mode = os.getenv("SECURITY_MODE", "normal").lower()
            mode = {
                "local_only": SecurityMode.LOCAL_ONLY,
                "restricted": SecurityMode.RESTRICTED,
                "normal": SecurityMode.NORMAL,
            }.get(env_mode, SecurityMode.NORMAL)
        
        self.mode = mode
        self.allowed_domains = self.DEFAULT_ALLOWED_DOMAINS.copy()
        
        if allowed_domains:
            self.allowed_domains.update(allowed_domains)

    def is_url_allowed(self, url: str) -> bool:
        """
        URL 호출이 허용되는지 확인.
        
        Args:
            url: 대상 URL
            
        Returns:
            허용 여부
        """
        if self.mode == SecurityMode.LOCAL_ONLY:
            # 모든 외부 호출 차단
            return False
        
        if self.mode == SecurityMode.NORMAL:
            # 모든 호출 허용
            return True
        
        # RESTRICTED 모드: 허용 목록 확인
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # 정확히 일치하거나 서브도메인 허용
            for allowed in self.allowed_domains:
                if domain == allowed or domain.endswith(f".{allowed}"):
                    return True
            
            return False
        except Exception:
            return False

    def is_data_safe_to_send(self, data: dict) -> bool:
        """
        데이터 전송이 안전한지 확인.
        
        문서 내용, 임베딩, 인덱스 데이터 전송 차단.
        """
        data_str = str(data).lower()
        
        for pattern in self.FORBIDDEN_DATA_PATTERNS:
            if pattern in data_str:
                return False
        
        return True

    def add_allowed_domain(self, domain: str) -> None:
        """허용 도메인 추가."""
        self.allowed_domains.add(domain.lower())

    def remove_allowed_domain(self, domain: str) -> bool:
        """허용 도메인 제거."""
        domain = domain.lower()
        if domain in self.allowed_domains:
            self.allowed_domains.discard(domain)
            return True
        return False

    def set_mode(self, mode: SecurityMode) -> None:
        """보안 모드 변경."""
        self.mode = mode

    def get_mode_description(self) -> str:
        """현재 모드 설명."""
        descriptions = {
            SecurityMode.LOCAL_ONLY: "완전 오프라인 - 모든 외부 통신 차단",
            SecurityMode.RESTRICTED: "제한 모드 - 허용된 도메인만 접근 가능",
            SecurityMode.NORMAL: "일반 모드 - 모든 외부 통신 허용",
        }
        return descriptions.get(self.mode, "알 수 없음")
