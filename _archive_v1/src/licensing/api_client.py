# src/licensing/api_client.py
# Phase 2: 1.2. api_client.py 구현 사양에 따라 구현

import requests
from typing import Optional

class LicenseAPIClient:
    """
    라이선스 서버와 통신하는 클라이언트.
    - activate: 라이선스 키 활성화
    - refresh: 토큰 갱신
    """
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def activate(self, license_key: str, device_id: str) -> dict:
        """
        라이선스 키를 활성화하고 토큰을 받아온다.
        
        Returns:
            {
                "plan": "pro",
                "features": ["outlook_indexing", "cloud_connectors", ...],
                "token": "...",
                "expires_at": "2025-01-01T00:00:00Z"
            }
        """
        url = self.base_url + "/license/activate"
        payload = {"license_key": license_key, "device_id": device_id}
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e), "plan": "free", "features": []}

    def refresh(self, token: str) -> dict:
        """
        기존 토큰을 갱신한다.
        
        Returns:
            동일한 구조의 새 토큰 데이터
        """
        url = self.base_url + "/license/refresh"
        payload = {"token": token}
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
