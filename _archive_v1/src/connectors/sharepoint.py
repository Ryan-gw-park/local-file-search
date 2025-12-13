# src/connectors/sharepoint.py
# Phase 2: 2.6. SharePointConnector 사양에 따라 구현

import os
import tempfile
from typing import Iterator, Dict, Any, Optional, List
from pathlib import Path
from .base import BaseConnector

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class SharePointConnector(BaseConnector):
    """
    SharePoint에서 문서를 검색하는 Connector.
    Microsoft Graph API 사용.
    Pro 전용 기능.
    
    기능:
    - 사이트 목록 조회
    - Document Library 선택
    - 파일 목록 조회
    - 파일 temp 다운로드
    """
    
    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
    SUPPORTED_EXTENSIONS = {'.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.pdf', '.txt'}
    
    def __init__(self, access_token: Optional[str] = None, site_id: Optional[str] = None):
        """
        Args:
            access_token: Microsoft Graph API 액세스 토큰
            site_id: SharePoint 사이트 ID (선택)
        """
        self.access_token = access_token
        self.site_id = site_id
        self._temp_dir = tempfile.mkdtemp(prefix="sharepoint_")

    @property
    def name(self) -> str:
        return "sharepoint"

    def set_access_token(self, token: str) -> None:
        """액세스 토큰 설정."""
        self.access_token = token

    def set_site_id(self, site_id: str) -> None:
        """사이트 ID 설정."""
        self.site_id = site_id

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

    def list_sites(self) -> List[Dict[str, Any]]:
        """사용 가능한 SharePoint 사이트 목록."""
        if not self.access_token:
            return []
        
        try:
            response = requests.get(
                f"{self.GRAPH_API_BASE}/sites?search=*",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return [
                    {"id": site["id"], "name": site.get("displayName", site["name"])}
                    for site in data.get("value", [])
                ]
        except Exception:
            pass
        
        return []

    def list_items(self) -> Iterator[Dict[str, Any]]:
        """SharePoint 문서 목록 반환."""
        if not self.access_token or not self.site_id:
            return
        
        try:
            # Document Library 목록 가져오기
            response = requests.get(
                f"{self.GRAPH_API_BASE}/sites/{self.site_id}/drives",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=30
            )
            
            if response.status_code != 200:
                return
            
            drives = response.json().get("value", [])
            
            for drive in drives:
                drive_id = drive.get("id")
                if drive_id:
                    yield from self._list_drive(drive_id)
                    
        except Exception:
            return

    def _list_drive(self, drive_id: str) -> Iterator[Dict[str, Any]]:
        """드라이브(Document Library) 내 파일 목록."""
        try:
            response = requests.get(
                f"{self.GRAPH_API_BASE}/drives/{drive_id}/root/children",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=30
            )
            
            if response.status_code != 200:
                return
            
            items = response.json().get("value", [])
            
            for item in items:
                if "folder" in item:
                    # 하위 폴더 재귀
                    item_id = item["id"]
                    yield from self._list_folder(drive_id, item_id)
                elif "file" in item:
                    name = item.get("name", "")
                    ext = Path(name).suffix.lower()
                    if ext in self.SUPPORTED_EXTENSIONS:
                        yield self._create_item(item, drive_id)
                        
        except Exception:
            return

    def _list_folder(self, drive_id: str, folder_id: str) -> Iterator[Dict[str, Any]]:
        """폴더 내 파일 목록 (재귀)."""
        try:
            response = requests.get(
                f"{self.GRAPH_API_BASE}/drives/{drive_id}/items/{folder_id}/children",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=30
            )
            
            if response.status_code != 200:
                return
            
            items = response.json().get("value", [])
            
            for item in items:
                if "folder" in item:
                    yield from self._list_folder(drive_id, item["id"])
                elif "file" in item:
                    name = item.get("name", "")
                    ext = Path(name).suffix.lower()
                    if ext in self.SUPPORTED_EXTENSIONS:
                        yield self._create_item(item, drive_id)
                        
        except Exception:
            return

    def _create_item(self, drive_item: dict, drive_id: str) -> Dict[str, Any]:
        """Graph API 아이템에서 정보 추출."""
        item_id = drive_item.get("id", "")
        name = drive_item.get("name", "Unknown")
        modified = drive_item.get("lastModifiedDateTime")
        
        author = None
        if "lastModifiedBy" in drive_item:
            user = drive_item["lastModifiedBy"].get("user", {})
            author = user.get("displayName")
        
        return {
            "id": f"sharepoint:{drive_id}:{item_id}",
            "path": None,
            "source": "sharepoint",
            "text": None,
            "metadata": {
                "filename": name,
                "modified": modified,
                "author": author,
                "drive_id": drive_id,
                "item_id": item_id,
                "download_url": drive_item.get("@microsoft.graph.downloadUrl"),
            }
        }

    def download(self, item: Dict[str, Any]) -> Optional[str]:
        """파일을 로컬 temp 디렉토리로 다운로드."""
        metadata = item.get("metadata", {})
        download_url = metadata.get("download_url")
        filename = metadata.get("filename", "file")
        drive_id = metadata.get("drive_id")
        item_id = metadata.get("item_id")
        
        if not download_url and drive_id and item_id:
            try:
                response = requests.get(
                    f"{self.GRAPH_API_BASE}/drives/{drive_id}/items/{item_id}/content",
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
        
        if download_url:
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
