# src/api/server.py
# Phase 4: 3.1. FastAPI 서버 사양에 따라 구현

import os
from typing import Optional

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


def create_app(
    title: str = "Local File Search API",
    version: str = "0.8.0",
    cors_origins: Optional[list] = None
) -> "FastAPI":
    """
    FastAPI 앱 생성.
    
    Phase 4: 로컬 HTTP API 서버.
    검색 품질은 API/UI 구분 없이 동일.
    """
    if not HAS_FASTAPI:
        raise ImportError("FastAPI is required. Install with: pip install fastapi uvicorn")
    
    app = FastAPI(
        title=title,
        version=version,
        description="Local AI File Search API - Search quality is identical for Free/Pro"
    )
    
    # CORS 설정 (기본: localhost만 허용)
    origins = cors_origins or [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 라우트 등록
    from .routes import router
    if router:
        app.include_router(router, prefix="/api/v1")
    
    @app.get("/")
    async def root():
        return {
            "name": title,
            "version": version,
            "docs": "/docs",
            "note": "Search quality is FREE/PRO identical"
        }
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    return app


def run_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False
) -> None:
    """
    API 서버 실행.
    
    Args:
        host: 바인드 주소 (기본: localhost만)
        port: 포트 번호
        reload: 개발 모드 리로드
    """
    if not HAS_FASTAPI:
        print("FastAPI is required. Install with: pip install fastapi uvicorn")
        return
    
    app = create_app()
    
    print(f"Starting API server at http://{host}:{port}")
    print(f"API docs: http://{host}:{port}/docs")
    print("Note: Search quality is FREE/PRO identical")
    
    uvicorn.run(app, host=host, port=port, reload=reload)


if __name__ == "__main__":
    run_server()
