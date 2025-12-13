# src/connectors/onedrive.py
# Phase 2: 2.5. OneDriveConnector 사양에 따라 구현

import os
import tempfile
from typing import Iterator, Dict, Any, Optional, List
from pathlib import Path
from .base import BaseConnector

# Microsoft Graph API 사용 (requests 필요)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class OneDriveConnector(BaseConnector):
    """
    OneDrive에서 파일을 검색하는 Connector.
    Microsoft Graph API 사용.
    Pro 전용 기능.
    
    기능:
    - Microsoft OAuth2 로그인
    - /drive/root/children 또는 delta API로 파일 목록 조회
    - 파일 다운로드 → 로컬 temp 저장
    """
    
    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
    SUPPORTED_EXTENSIONS = {'.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.pdf', '.txt'}
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Args:
            access_token: Microsoft Graph API 액세스 토큰
        """
        self.access_token = access_token
        self._temp_dir = tempfile.mkdtemp(prefix="onedrive_")

    @property
    def name(self) -> str:
        return "onedrive"

    def set_access_token(self, token: str) -> None:
        """액세스 토큰 설정."""
        self.access_token = token

    def authenticate(self) -> bool:
        """토큰 유효성 확인."""
        if not self.access_token or not HAS_REQUESTS:
            return False
        
        try:
            response = requests.get(
                f"{self.GRAPH_API_BASE}/me",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False

    def list_items(self) -> Iterator[Dict[str, Any]]:
        """OneDrive 파일 목록 반환."""
        if not self.access_token:
            return
        
        try:
            yield from self._list_folder("/me/drive/root/children")
        except Exception:
            return

    def _list_folder(self, endpoint: str) -> Iterator[Dict[str, Any]]:
        """폴더 내 파일 목록 조회 (재귀)."""
        try:
            response = requests.get(
                f"{self.GRAPH_API_BASE}{endpoint}",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=30
            )
            
            if response.status_code != 200:
                return
            
            data = response.json()
            items = data.get("value", [])
            
            for item in items:
                if "folder" in item:
                    # 하위 폴더 재귀 탐색
                    folder_id = item["id"]
                    yield from self._list_folder(f"/me/drive/items/{folder_id}/children")
                elif "file" in item:
                    # 파일인 경우
                    name = item.get("name", "")
                    ext = Path(name).suffix.lower()
                    
                    if ext in self.SUPPORTED_EXTENSIONS:
                        yield self._create_item(item)
            
            # 페이지네이션
            next_link = data.get("@odata.nextLink")
            if next_link:
                yield from self._list_folder_by_url(next_link)
                
        except Exception:
            return

    def _list_folder_by_url(self, url: str) -> Iterator[Dict[str, Any]]:
        """전체 URL로 폴더 조회."""
        try:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=30
            )
            
            if response.status_code != 200:
                return
            
            data = response.json()
            for item in data.get("value", []):
                if "file" in item:
                    name = item.get("name", "")
                    ext = Path(name).suffix.lower()
                    if ext in self.SUPPORTED_EXTENSIONS:
                        yield self._create_item(item)
        except Exception:
            return

    def _create_item(self, drive_item: dict) -> Dict[str, Any]:
        """Graph API 아이템에서 정보 추출."""
        item_id = drive_item.get("id", "")
        name = drive_item.get("name", "Unknown")
        modified = drive_item.get("lastModifiedDateTime")
        
        # 작성자 정보
        author = None
        if "lastModifiedBy" in drive_item:
            user = drive_item["lastModifiedBy"].get("user", {})
            author = user.get("displayName")
        
        return {
            "id": f"onedrive:{item_id}",
            "path": None,  # download() 호출 시 설정됨
            "source": "onedrive",
            "text": None,
            "metadata": {
                "filename": name,
                "modified": modified,
                "author": author,
                "item_id": item_id,
                "download_url": drive_item.get("@microsoft.graph.downloadUrl"),
            }
        }

    def download(self, item: Dict[str, Any]) -> Optional[str]:
        """파일을 로컬 temp 디렉토리로 다운로드."""
        metadata = item.get("metadata", {})
        download_url = metadata.get("download_url")
        filename = metadata.get("filename", "file")
        
        if not download_url:
            # download_url이 없으면 API로 가져오기
            item_id = metadata.get("item_id")
            if item_id:
                try:
                    response = requests.get(
                        f"{self.GRAPH_API_BASE}/me/drive/items/{item_id}/content",
                        headers={"Authorization": f"Bearer {self.access_token}"},
                        timeout=60,
                        allow_redirects=True
                    )
                    if response.status_code == 200:
                        local_path = os.path.join(self._temp_dir, filename)
                        with open(local_path, 'wb') as f:
                            f.write(response.content)
                        return local_path
                except Exception:
                    pass
            return None
        
        try:
            response = requests.get(download_url, timeout=60)
            if response.status_code == 200:
                local_path = os.path.join(self._temp_dir, filename)
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                return local_path
        except Exception:
            pass
        
        return None

    def close(self) -> None:
        """임시 파일 정리."""
        import shutil
        try:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        except:
            pass
