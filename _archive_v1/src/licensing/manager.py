# src/licensing/manager.py
# Phase 2: 1.4. LicenseManager 변경사항에 따라 구현

from typing import Literal, Set, Optional
from config import AppConfig
from licensing.api_client import LicenseAPIClient
from licensing.token_store import TokenStore

PlanType = Literal["free", "pro"]

class LicenseManager:
    """
    Free/Pro 검색 품질은 동일.
    차이는 검색 대상 범위에서만 발생한다.
    
    Phase 2: 서버에서 받은 token을 기준으로 Pro 여부 판단.
    AppConfig.mode는 fallback/testing용.
    """
    def __init__(self, config: AppConfig, 
                 api_client: Optional[LicenseAPIClient] = None, 
                 token_store: Optional[TokenStore] = None):
        self.config = config
        self.api = api_client
        self.token_store = token_store or TokenStore()
        
        # 토큰 로드 시도
        self.token = self.token_store.load() if self.token_store else None
        
        if self.token and "plan" in self.token:
            # 서버에서 받은 토큰 기반
            self._plan: PlanType = self.token.get("plan", "free")
            self._features: Set[str] = set(self.token.get("features", []))
        else:
            # 개발/테스트 모드: config.mode 사용
            self._plan = config.mode
            self._features = set()

    @property
    def plan(self) -> PlanType:
        return self._plan

    def is_pro(self) -> bool:
        return self._plan == "pro"

    def has_feature(self, feature: str) -> bool:
        """
        Free/Pro 기능 제한을 정의.
        검색 품질 관련 feature는 언제나 True여야 한다.
        """
        # 검색 품질 관련 기능은 항상 허용 (Free/Pro 동일)
        always_free = {
            "local_search",
            "local_indexing",
            "semantic_search",
            "best_quality",
            "vector_engine",
        }
        if feature in always_free:
            return True

        # 서버에서 받은 feature 목록에 있는지 확인
        if feature in self._features:
            return True

        # Pro 모드면 모든 기능 허용 (개발/테스트용)
        if self._plan == "pro":
            return True

        # Free 모드에서 Pro 전용 기능 차단
        return False

    def activate_license(self, license_key: str, device_id: str) -> bool:
        """
        라이선스 키를 활성화하고 토큰을 저장한다.
        """
        if not self.api:
            return False
        
        result = self.api.activate(license_key, device_id)
        if "error" in result:
            return False
        
        # 토큰 저장
        if self.token_store:
            self.token_store.save(result)
        
        # 상태 업데이트
        self.token = result
        self._plan = result.get("plan", "free")
        self._features = set(result.get("features", []))
        
        return True

    def refresh_license(self) -> bool:
        """
        기존 토큰을 갱신한다.
        """
        if not self.api or not self.token:
            return False
        
        token_str = self.token.get("token", "")
        if not token_str:
            return False
        
        result = self.api.refresh(token_str)
        if "error" in result:
            return False
        
        # 토큰 업데이트
        if self.token_store:
            self.token_store.save(result)
        
        self.token = result
        self._plan = result.get("plan", "free")
        self._features = set(result.get("features", []))
        
        return True

    def logout(self) -> bool:
        """
        라이선스 로그아웃 (토큰 삭제).
        """
        if self.token_store:
            self.token_store.clear()
        
        self.token = None
        self._plan = self.config.mode
        self._features = set()
        
        return True
