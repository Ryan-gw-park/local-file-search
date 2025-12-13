# src/api/auth.py
# Phase 4: 3.3. API_TOKEN 인증 사양에 따라 구현

import os
from functools import wraps
from typing import Optional, Callable

# FastAPI imports (optional)
try:
    from fastapi import HTTPException, Header, Depends
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


def get_api_token() -> Optional[str]:
    """환경 변수에서 API 토큰 조회."""
    return os.getenv("API_TOKEN")


def validate_token(token: str) -> bool:
    """토큰 유효성 검사."""
    api_token = get_api_token()
    if not api_token:
        # 토큰 미설정 시 모든 요청 허용 (개발 모드)
        return True
    return token == api_token


if HAS_FASTAPI:
    async def require_api_token(
        authorization: Optional[str] = Header(None, alias="Authorization")
    ) -> bool:
        """
        FastAPI dependency: API 토큰 인증 요구.
        
        Header: Authorization: Bearer <token>
        """
        api_token = get_api_token()
        
        # 토큰 미설정 시 인증 불필요 (개발 모드)
        if not api_token:
            return True
        
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header required")
        
        # Bearer 토큰 파싱
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization format")
        
        token = parts[1]
        if not validate_token(token):
            raise HTTPException(status_code=403, detail="Invalid API token")
        
        return True
else:
    # FastAPI 없을 때 fallback
    def require_api_token(authorization: Optional[str] = None) -> bool:
        """Fallback: FastAPI 없이 토큰 검증."""
        if not authorization:
            return get_api_token() is None
        
        token = authorization.replace("Bearer ", "").strip()
        return validate_token(token)


def generate_token(length: int = 32) -> str:
    """랜덤 API 토큰 생성."""
    import secrets
    return secrets.token_urlsafe(length)
