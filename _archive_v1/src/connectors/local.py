# src/connectors/local.py
# Phase 2: 2.3. LocalConnector 사양에 따라 구현

import os
from pathlib import Path
from typing import Iterator, Dict, Any, List
from datetime import datetime
from .base import BaseConnector

class LocalFileConnector(BaseConnector):
    """
    로컬 파일 시스템에서 문서를 검색하는 Connector.
    Free/Pro 모두 사용 가능.
    """
    
    # 내용까지 인덱싱할 파일 확장자 (문서 파일)
    CONTENT_INDEXABLE_EXTENSIONS = {'.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.pdf', '.txt', '.md'}
    
    # 완전히 제외할 파일 확장자 (시스템/실행 파일 등)
    SKIP_EXTENSIONS = {
        '.exe', '.dll', '.sys', '.drv', '.ocx',  # 실행/시스템
        '.lnk', '.url',  # 바로가기
        '.tmp', '.bak', '.swp',  # 임시 파일
        '.log',  # 로그 파일
        '.ini', '.cfg',  # 설정 파일
    }
    
    # 건너뛸 디렉토리 패턴
    SKIP_DIRS = {
        '__pycache__', '.git', '.svn', 'node_modules', 'venv', '.venv',
        'AppData', 'Application Data', '.cache', 'Cache', 'Temp', 'tmp',
        '$Recycle.Bin', 'System Volume Information', 'Windows',
    }
    
    # 건너뛸 파일 패턴
    SKIP_FILE_PREFIXES = ('~$', '.', '_')
    
    def __init__(self, root_paths: List[str]):
        """
        Args:
            root_paths: 검색할 루트 디렉토리 목록
        """
        self.root_paths = [Path(p) for p in root_paths]

    @property
    def name(self) -> str:
        return "local"

    def list_items(self) -> Iterator[Dict[str, Any]]:
        """
        모든 루트 경로에서 지원되는 파일 목록을 반환.
        """
        for root_path in self.root_paths:
            if not root_path.exists() or not root_path.is_dir():
                continue
            
            yield from self._scan_directory(root_path)

    def _scan_directory(self, directory: Path) -> Iterator[Dict[str, Any]]:
        """재귀적으로 디렉토리를 스캔."""
        try:
            for entry in os.scandir(directory):
                try:
                    if entry.is_dir(follow_symlinks=False):
                        if self._should_skip_dir(entry.name):
                            continue
                        yield from self._scan_directory(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        if self._should_include_file(entry.name):
                            yield self._create_item(Path(entry.path))
                except PermissionError:
                    continue
                except OSError:
                    continue
        except PermissionError:
            pass
        except OSError:
            pass

    def _should_skip_dir(self, dir_name: str) -> bool:
        """건너뛸 디렉토리인지 확인."""
        return dir_name in self.SKIP_DIRS or dir_name.startswith('.')

    def _should_include_file(self, filename: str) -> bool:
        """포함할 파일인지 확인. 모든 파일 포함 (시스템 파일 제외)."""
        # 숨김 파일, 임시 파일 제외
        if any(filename.startswith(prefix) for prefix in self.SKIP_FILE_PREFIXES):
            return False
        
        # 확장자 체크 - 제외 목록에 없으면 모두 포함
        ext = Path(filename).suffix.lower()
        return ext not in self.SKIP_EXTENSIONS

    def _create_item(self, file_path: Path) -> Dict[str, Any]:
        """파일 정보로 아이템 생성."""
        try:
            stat = file_path.stat()
            modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
            size = stat.st_size
        except OSError:
            modified = None
            size = None
        
        ext = file_path.suffix.lower()
        is_content_indexable = ext in self.CONTENT_INDEXABLE_EXTENSIONS
        
        return {
            "id": str(file_path),
            "path": str(file_path),
            "source": "local",
            "text": None,  # FileIndexer가 추출 (content_indexable인 경우만)
            "is_content_indexable": is_content_indexable,  # 내용 인덱싱 여부
            "metadata": {
                "filename": file_path.name,
                "modified": modified,
                "author": None,
                "size": size,
                "extension": ext,
            }
        }

