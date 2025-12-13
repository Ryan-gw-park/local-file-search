# src/api/routes.py
# Phase 4: 3.2. API 라우트 사양에 따라 구현

from typing import Optional, List, Dict, Any

try:
    from fastapi import APIRouter, Depends, HTTPException
    from pydantic import BaseModel
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    # Fallback stubs
    class BaseModel:
        pass
    def APIRouter():
        return None

from .auth import require_api_token


# === Pydantic Models ===

class SearchRequest(BaseModel):
    """검색 요청 모델."""
    query: str
    n_results: int = 30


class SearchResult(BaseModel):
    """검색 결과 모델."""
    answer: str
    files: List[Dict[str, Any]]


class IndexRequest(BaseModel):
    """인덱싱 요청 모델."""
    connector: str  # "local", "outlook", "onedrive", "sharepoint"
    paths: Optional[List[str]] = None  # LocalConnector용


class IndexResult(BaseModel):
    """인덱싱 결과 모델."""
    indexed: int
    skipped: int
    errors: List[str]


class StatusResponse(BaseModel):
    """상태 응답 모델."""
    status: str
    document_count: int
    version: str


# === API Router ===

if HAS_FASTAPI:
    router = APIRouter()
    
    # 의존성으로 사용할 SearchEngine 인스턴스
    _search_engine = None
    _file_indexer = None
    
    def get_search_engine():
        global _search_engine
        if _search_engine is None:
            from ..search_engine import SearchEngine
            _search_engine = SearchEngine()
        return _search_engine
    
    def get_file_indexer():
        global _file_indexer
        if _file_indexer is None:
            from ..indexer import FileIndexer
            _file_indexer = FileIndexer()
        return _file_indexer
    
    @router.get("/status", response_model=StatusResponse)
    async def get_status(auth: bool = Depends(require_api_token)):
        """
        API 상태 확인.
        
        검색 품질에 영향 없음 — 상태 정보만 반환.
        """
        indexer = get_file_indexer()
        return StatusResponse(
            status="ok",
            document_count=indexer.collection.count(),
            version="0.8.0"
        )
    
    @router.post("/search", response_model=SearchResult)
    async def search(
        request: SearchRequest,
        auth: bool = Depends(require_api_token)
    ):
        """
        검색 API.
        
        검색 품질은 Free/Pro 동일.
        API를 통한 검색도 동일한 SearchEngine.search_and_answer() 사용.
        """
        engine = get_search_engine()
        result = engine.search_and_answer(request.query)
        return SearchResult(
            answer=result.get("answer", ""),
            files=result.get("files", [])
        )
    
    @router.post("/index", response_model=IndexResult)
    async def index(
        request: IndexRequest,
        auth: bool = Depends(require_api_token)
    ):
        """
        인덱싱 API.
        
        인덱싱 파이프라인은 동일 — API/UI 구분 없이 같은 품질.
        """
        indexer = get_file_indexer()
        
        if request.connector == "local":
            paths = request.paths or []
            if not paths:
                raise HTTPException(status_code=400, detail="paths required for local connector")
            
            total_indexed = 0
            total_skipped = 0
            total_errors = []
            
            for path in paths:
                result = indexer.index_directory(path)
                total_indexed += result.get("indexed", 0)
                total_skipped += result.get("skipped", 0)
                total_errors.extend(result.get("errors", []))
            
            return IndexResult(
                indexed=total_indexed,
                skipped=total_skipped,
                errors=[str(e) for e in total_errors[:10]]  # 최대 10개 에러만
            )
        
        elif request.connector == "outlook":
            result = indexer.index_outlook()
            return IndexResult(
                indexed=result.get("indexed", 0),
                skipped=result.get("skipped", 0),
                errors=result.get("errors", [])
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown connector: {request.connector}"
            )
    
    @router.get("/plugins")
    async def list_plugins(auth: bool = Depends(require_api_token)):
        """등록된 플러그인 목록."""
        from ..plugins import PluginRegistry
        registry = PluginRegistry()
        return {
            "connectors": registry.list_connectors(),
            "postprocessors": registry.list_postprocessors()
        }

else:
    router = None
