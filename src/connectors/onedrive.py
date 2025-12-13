"""
Local Finder X v2.0 - OneDrive/SharePoint Connector

MS Graph API-based OneDrive and SharePoint connector.
"""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


# =============================================================================
# Configuration
# =============================================================================

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
ONEDRIVE_ROOT = f"{GRAPH_BASE_URL}/me/drive/root"
ONEDRIVE_ITEMS = f"{GRAPH_BASE_URL}/me/drive/items"

# Required scopes for OneDrive access
ONEDRIVE_SCOPES = [
    "Files.Read",
    "Files.Read.All",
]


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class DriveItem:
    """Represents a OneDrive/SharePoint file or folder."""
    id: str
    name: str
    path: str
    is_folder: bool
    size: int = 0
    mime_type: str = ""
    web_url: str = ""
    download_url: str = ""
    modified_at: str = ""
    created_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "is_folder": self.is_folder,
            "size": self.size,
            "mime_type": self.mime_type,
            "web_url": self.web_url,
            "download_url": self.download_url,
            "modified_at": self.modified_at,
            "created_at": self.created_at,
        }


# =============================================================================
# OneDrive Connector
# =============================================================================

class OneDriveConnector:
    """
    Connector for OneDrive/SharePoint via MS Graph API.
    
    Shares authentication with OutlookConnector.
    """
    
    def __init__(self, access_token: Optional[str] = None):
        self._access_token = access_token
    
    def set_access_token(self, token: str) -> None:
        """Set the access token from Outlook authentication."""
        self._access_token = token
    
    @property
    def is_authenticated(self) -> bool:
        return bool(self._access_token)
    
    def list_root(self) -> List[DriveItem]:
        """List items in the root of OneDrive."""
        return self.list_children("")
    
    def list_children(self, item_id: str) -> List[DriveItem]:
        """
        List children of a folder.
        
        Args:
            item_id: ID of the parent folder. Empty for root.
        
        Returns:
            List of DriveItem objects.
        """
        if not self._access_token or not REQUESTS_AVAILABLE:
            return []
        
        if item_id:
            url = f"{ONEDRIVE_ITEMS}/{item_id}/children"
        else:
            url = f"{ONEDRIVE_ROOT}/children"
        
        headers = {"Authorization": f"Bearer {self._access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            items = []
            for item in data.get("value", []):
                drive_item = DriveItem(
                    id=item.get("id", ""),
                    name=item.get("name", ""),
                    path=item.get("parentReference", {}).get("path", "") + "/" + item.get("name", ""),
                    is_folder="folder" in item,
                    size=item.get("size", 0),
                    mime_type=item.get("file", {}).get("mimeType", ""),
                    web_url=item.get("webUrl", ""),
                    download_url=item.get("@microsoft.graph.downloadUrl", ""),
                    modified_at=item.get("lastModifiedDateTime", ""),
                    created_at=item.get("createdDateTime", ""),
                )
                items.append(drive_item)
            
            return items
            
        except Exception as e:
            print(f"Error listing items: {e}")
            return []
    
    def search(self, query: str, top: int = 25) -> List[DriveItem]:
        """
        Search for files in OneDrive.
        
        Args:
            query: Search query.
            top: Number of results.
        
        Returns:
            List of matching DriveItems.
        """
        if not self._access_token or not REQUESTS_AVAILABLE:
            return []
        
        url = f"{ONEDRIVE_ROOT}/search(q='{query}')"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        params = {"$top": top}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            items = []
            for item in data.get("value", []):
                drive_item = DriveItem(
                    id=item.get("id", ""),
                    name=item.get("name", ""),
                    path=item.get("parentReference", {}).get("path", "") + "/" + item.get("name", ""),
                    is_folder="folder" in item,
                    size=item.get("size", 0),
                    mime_type=item.get("file", {}).get("mimeType", ""),
                    web_url=item.get("webUrl", ""),
                    download_url=item.get("@microsoft.graph.downloadUrl", ""),
                    modified_at=item.get("lastModifiedDateTime", ""),
                )
                items.append(drive_item)
            
            return items
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def download_content(self, item_id: str) -> Optional[bytes]:
        """
        Download file content.
        
        Args:
            item_id: ID of the file to download.
        
        Returns:
            File content as bytes, or None on error.
        """
        if not self._access_token or not REQUESTS_AVAILABLE:
            return None
        
        url = f"{ONEDRIVE_ITEMS}/{item_id}/content"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        
        try:
            response = requests.get(url, headers=headers, allow_redirects=True)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Download error: {e}")
            return None
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions for indexing."""
        return [".docx", ".xlsx", ".pptx", ".pdf", ".md", ".txt"]


__all__ = [
    "OneDriveConnector",
    "DriveItem",
    "ONEDRIVE_SCOPES",
]
