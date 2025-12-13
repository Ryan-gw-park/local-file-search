# src/plugins/interfaces.py
# Phase 4: 2.2. interfaces.py 예시에 따라 구현

from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, List, Protocol


class ConnectorPlugin(ABC):
    """
    외부에서 추가할 수 있는 Connector 플러그인 인터페이스.
    
    기존 BaseConnector를 확장.
    플러그인은 검색 품질에 영향을 주지 않음 — 
    데이터를 공급하는 역할만 하고, 인덱싱/검색은 기존 파이프라인을 그대로 사용.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """플러그인 이름 (고유 식별자)."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """UI에 표시할 이름."""
        pass
    
    @property
    def version(self) -> str:
        """플러그인 버전."""
        return "1.0.0"
    
    @abstractmethod
    def authenticate(self) -> bool:
        """인증 처리."""
        pass
    
    @abstractmethod
    def list_items(self) -> Iterator[Dict[str, Any]]:
        """
        문서 목록 반환.
        
        각 item 형식:
        {
            "id": str,
            "path": str | None,
            "source": str,
            "text": str | None,
            "metadata": {...}
        }
        """
        pass
    
    def download(self, item: Dict[str, Any]) -> str | None:
        """원격 문서 다운로드. 기본은 path 반환."""
        return item.get("path")
    
    def close(self) -> None:
        """리소스 정리."""
        pass


class PostProcessorPlugin(ABC):
    """
    검색 결과 후처리 플러그인 인터페이스.
    
    중요: 후처리는 검색 품질을 '다르게' 만들지 않음.
    결과의 형식 변환, 하이라이팅, 요약 등 표현 방식만 변경.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """플러그인 이름."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """UI에 표시할 이름."""
        pass
    
    @property
    def version(self) -> str:
        """플러그인 버전."""
        return "1.0.0"
    
    @abstractmethod
    def process(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        검색 결과 후처리.
        
        Args:
            results: search_and_answer() 반환값 {"answer": ..., "files": [...]}
            
        Returns:
            후처리된 결과 (동일 형식)
        """
        pass
