# src/scheduler/jobs.py
# Phase 3: 3.2. jobs.py 예시에 따라 구현

from typing import Protocol, Any, Dict, Optional
from abc import ABC, abstractmethod


class IndexJob(Protocol):
    """인덱싱 작업 프로토콜."""
    
    @property
    def name(self) -> str:
        """작업 이름."""
        ...
    
    def run(self) -> Dict[str, Any]:
        """
        인덱싱 작업 수행.
        
        Returns:
            {"indexed": int, "skipped": int, "errors": list}
        """
        ...


class BaseIndexJob(ABC):
    """인덱싱 작업 기본 클래스."""
    
    def __init__(self, file_indexer, connector):
        """
        Args:
            file_indexer: FileIndexer 인스턴스
            connector: BaseConnector 구현체
        """
        self.file_indexer = file_indexer
        self.connector = connector
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    def run(self) -> Dict[str, Any]:
        """인덱싱 작업 실행."""
        return self.file_indexer.index_connector(self.connector)


class LocalIndexJob(BaseIndexJob):
    """로컬 파일 인덱싱 작업. Free/Pro 공통."""
    
    @property
    def name(self) -> str:
        return "local_index"


class OutlookIndexJob(BaseIndexJob):
    """Outlook 인덱싱 작업. Pro 전용."""
    
    @property
    def name(self) -> str:
        return "outlook_index"


class OneDriveIndexJob(BaseIndexJob):
    """OneDrive 인덱싱 작업. Pro 전용."""
    
    @property
    def name(self) -> str:
        return "onedrive_index"


class SharePointIndexJob(BaseIndexJob):
    """SharePoint 인덱싱 작업. Pro 전용."""
    
    @property
    def name(self) -> str:
        return "sharepoint_index"
