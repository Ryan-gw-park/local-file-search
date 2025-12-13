# src/connectors/base.py
# Phase 2: 2.2. BaseConnector 사양에 따라 구현

from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Optional

class BaseConnector(ABC):
    """
    모든 Connector의 기본 인터페이스.
    
    Connector는 "문서를 공급"하는 역할만 담당한다.
    검색 품질은 SearchEngine에 의해 통일되므로 Connector는 데이터 공급자 역할만 한다.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Connector 이름 (예: 'local', 'outlook', 'onedrive')"""
        pass

    def authenticate(self) -> bool:
        """
        인증 절차. LocalConnector는 필요 없음.
        
        Returns:
            인증 성공 여부
        """
        return True

    @abstractmethod
    def list_items(self) -> Iterator[Dict[str, Any]]:
        """
        문서 목록 반환 — 각 item은 반드시 다음 형식을 가진다.
        
        Yields:
            {
                "id": str,                          # 고유 식별자
                "path": str | None,                 # 로컬 파일 경로 또는 None
                "source": str,                      # "local" | "outlook" | "onedrive" | "sharepoint"
                "text": str | None,                 # 직접 텍스트 제공 시 사용
                "metadata": {                       # 메타데이터
                    "filename": str,
                    "modified": str | None,         # ISO 8601 형식
                    "author": str | None,
                    ...
                }
            }
        """
        pass

    def download(self, item: Dict[str, Any]) -> Optional[str]:
        """
        원격 문서일 경우 로컬 temp path로 다운로드.
        LocalConnector는 path를 그대로 반환.
        
        Args:
            item: list_items()에서 반환된 아이템
            
        Returns:
            로컬 파일 경로 또는 None (다운로드 실패 시)
        """
        return item.get("path")

    def close(self) -> None:
        """리소스 정리. 필요시 오버라이드."""
        pass
