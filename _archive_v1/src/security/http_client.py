# src/security/http_client.py
# Transparency Layer: 2.4. SecureHttpClient 사양에 따라 구현

from typing import Optional, Dict, Any
import requests

from .policy import SecurityPolicy, SecurityMode
from .call_logger import ExternalCallLogger


class SecureHttpClient:
    """
    보안 정책을 적용하는 HTTP 클라이언트.
    
    모든 외부 HTTP 호출은 이 클라이언트를 통해야 함.
    - 보안 정책에 따라 호출 허용/차단
    - 모든 호출을 투명하게 로깅
    - 문서 내용/임베딩/인덱스 전송 차단
    
    검색 품질에 영향 없음 — 보안/투명성 레이어일 뿐.
    """
    
    def __init__(self, 
                 policy: Optional[SecurityPolicy] = None,
                 logger: Optional[ExternalCallLogger] = None,
                 timeout: int = 30):
        """
        Args:
            policy: 보안 정책 (기본: 환경 변수 기반)
            logger: 외부 호출 로거
            timeout: 기본 요청 타임아웃 (초)
        """
        self.policy = policy or SecurityPolicy()
        self.logger = logger or ExternalCallLogger()
        self.timeout = timeout

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        GET 요청.
        
        보안 정책에 따라 차단될 수 있음.
        """
        return self._request("GET", url, **kwargs)

    def post(self, url: str, json: Optional[Dict] = None, 
             data: Optional[Any] = None, **kwargs) -> Optional[requests.Response]:
        """
        POST 요청.
        
        데이터에 문서 내용/임베딩이 포함되면 차단.
        """
        # 데이터 안전성 확인
        if json and not self.policy.is_data_safe_to_send(json):
            self.logger.log_call(
                url=url,
                method="POST",
                allowed=False,
                reason="Forbidden data pattern detected (document content/embedding)"
            )
            return None
        
        return self._request("POST", url, json=json, data=data, **kwargs)

    def put(self, url: str, json: Optional[Dict] = None, **kwargs) -> Optional[requests.Response]:
        """PUT 요청."""
        if json and not self.policy.is_data_safe_to_send(json):
            self.logger.log_call(
                url=url,
                method="PUT",
                allowed=False,
                reason="Forbidden data pattern detected"
            )
            return None
        
        return self._request("PUT", url, json=json, **kwargs)

    def delete(self, url: str, **kwargs) -> Optional[requests.Response]:
        """DELETE 요청."""
        return self._request("DELETE", url, **kwargs)

    def _request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        실제 HTTP 요청 수행.
        
        보안 정책 확인 → 로깅 → 요청 수행
        """
        # 1. 보안 정책 확인
        if not self.policy.is_url_allowed(url):
            reason = f"Blocked by security policy ({self.policy.mode.value})"
            self.logger.log_call(
                url=url,
                method=method,
                allowed=False,
                reason=reason
            )
            return None
        
        # 2. 타임아웃 기본값 설정
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout
        
        # 3. 요청 수행
        try:
            response = requests.request(method, url, **kwargs)
            
            # 4. 성공 로깅
            self.logger.log_call(
                url=url,
                method=method,
                allowed=True,
                reason="Policy allowed",
                response_status=response.status_code,
                data_size_bytes=len(response.content) if response.content else 0
            )
            
            return response
            
        except requests.RequestException as e:
            # 에러 로깅
            self.logger.log_call(
                url=url,
                method=method,
                allowed=True,
                reason=f"Request error: {str(e)}",
                response_status=0
            )
            raise

    def set_policy(self, policy: SecurityPolicy) -> None:
        """보안 정책 변경."""
        self.policy = policy

    def set_mode(self, mode: SecurityMode) -> None:
        """보안 모드 변경."""
        self.policy.set_mode(mode)

    def get_call_stats(self) -> Dict[str, int]:
        """호출 통계 조회."""
        return self.logger.get_stats()

    def get_recent_calls(self, limit: int = 20) -> list:
        """최근 호출 목록."""
        return self.logger.read_logs(limit=limit)
