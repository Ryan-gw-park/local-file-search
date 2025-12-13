# src/connectors/outlook.py
# Phase 2: 2.4. OutlookConnector 사양에 따라 구현

import os
import re
from typing import Iterator, Dict, Any, Optional
from datetime import datetime
from .base import BaseConnector

# Outlook COM API 사용 여부 확인
try:
    import win32com.client
    import pythoncom
    HAS_OUTLOOK = True
except ImportError:
    HAS_OUTLOOK = False


class OutlookConnector(BaseConnector):
    """
    Outlook COM API를 사용하여 메일을 검색하는 Connector.
    Pro 전용 기능.
    
    기능:
    - Outlook COM API 사용하여 메일 텍스트 추출
    - HTML → 텍스트 변환
    - ReceivedTime, Sender 등 metadata 저장
    """
    
    def __init__(self, max_emails: int = 300, folders: Optional[list] = None):
        """
        Args:
            max_emails: 인덱싱할 최대 이메일 수
            folders: 검색할 폴더 목록 (기본: Inbox, Sent Items)
        """
        self.max_emails = max_emails
        self.folders = folders or ["Inbox", "Sent Items"]
        self._outlook = None
        self._namespace = None

    @property
    def name(self) -> str:
        return "outlook"

    def authenticate(self) -> bool:
        """Outlook COM 연결."""
        if not HAS_OUTLOOK:
            return False
        
        try:
            pythoncom.CoInitialize()
            self._outlook = win32com.client.GetActiveObject("Outlook.Application")
            self._namespace = self._outlook.GetNamespace("MAPI")
            return True
        except Exception:
            try:
                self._outlook = win32com.client.Dispatch("Outlook.Application")
                self._namespace = self._outlook.GetNamespace("MAPI")
                return True
            except Exception:
                return False

    def list_items(self) -> Iterator[Dict[str, Any]]:
        """이메일 목록 반환."""
        if not self._namespace:
            if not self.authenticate():
                return
        
        count = 0
        for folder_name in self.folders:
            if count >= self.max_emails:
                break
            
            try:
                folder = self._get_folder(folder_name)
                if not folder:
                    continue
                
                items = folder.Items
                items.Sort("[ReceivedTime]", True)  # 최신순
                
                for item in items:
                    if count >= self.max_emails:
                        break
                    
                    try:
                        yield self._create_item(item)
                        count += 1
                    except Exception:
                        continue
            except Exception:
                continue

    def _get_folder(self, folder_name: str):
        """폴더 이름으로 폴더 객체 반환."""
        try:
            # 기본 폴더 상수
            folder_map = {
                "Inbox": 6,
                "Sent Items": 5,
                "Drafts": 16,
            }
            
            if folder_name in folder_map:
                return self._namespace.GetDefaultFolder(folder_map[folder_name])
            
            # 이름으로 직접 검색
            for folder in self._namespace.Folders:
                for subfolder in folder.Folders:
                    if subfolder.Name == folder_name:
                        return subfolder
            return None
        except Exception:
            return None

    def _create_item(self, mail_item) -> Dict[str, Any]:
        """메일 아이템에서 정보 추출."""
        try:
            subject = mail_item.Subject or "(No Subject)"
            sender = str(mail_item.SenderName) if hasattr(mail_item, 'SenderName') else "Unknown"
            received = mail_item.ReceivedTime
            entry_id = mail_item.EntryID
            
            # 본문 추출 (HTML 제거)
            body = ""
            if hasattr(mail_item, 'Body'):
                body = mail_item.Body or ""
            
            # HTML 태그 제거
            body = re.sub(r'<[^>]+>', '', body)
            body = body[:5000]  # 너무 긴 본문 제한
            
            # 날짜 변환
            try:
                modified = received.isoformat() if received else None
            except:
                modified = None
            
            return {
                "id": f"outlook:{entry_id}",
                "path": f"outlook:{entry_id}",
                "source": "outlook",
                "text": f"Subject: {subject}\nFrom: {sender}\n\n{body}",
                "metadata": {
                    "filename": subject,
                    "modified": modified,
                    "author": sender,
                    "type": "email",
                    "entry_id": entry_id,
                }
            }
        except Exception as e:
            raise

    def close(self) -> None:
        """COM 리소스 정리."""
        try:
            pythoncom.CoUninitialize()
        except:
            pass
        self._outlook = None
        self._namespace = None
