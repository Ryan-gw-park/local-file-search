# src/plugins/registry.py
# Phase 4: 2.2. registry.py 예시에 따라 구현

from typing import Dict, Type, Optional, List
from .interfaces import ConnectorPlugin, PostProcessorPlugin


class PluginRegistry:
    """
    플러그인 등록 및 관리.
    
    앱 실행 시 플러그인 디렉토리 스캔 또는 수동 등록을 통해 플러그인 로드.
    플러그인은 검색 품질에 영향을 주지 않음.
    """
    
    def __init__(self):
        self._connector_plugins: Dict[str, ConnectorPlugin] = {}
        self._postprocessor_plugins: Dict[str, PostProcessorPlugin] = {}

    # === Connector Plugins ===
    
    def register_connector(self, plugin: ConnectorPlugin) -> None:
        """Connector 플러그인 등록."""
        self._connector_plugins[plugin.name] = plugin

    def unregister_connector(self, name: str) -> bool:
        """Connector 플러그인 제거."""
        if name in self._connector_plugins:
            del self._connector_plugins[name]
            return True
        return False

    def get_connector(self, name: str) -> Optional[ConnectorPlugin]:
        """Connector 플러그인 조회."""
        return self._connector_plugins.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        """등록된 Connector 플러그인 목록."""
        return [
            {
                "name": p.name,
                "display_name": p.display_name,
                "version": p.version
            }
            for p in self._connector_plugins.values()
        ]

    # === PostProcessor Plugins ===
    
    def register_postprocessor(self, plugin: PostProcessorPlugin) -> None:
        """PostProcessor 플러그인 등록."""
        self._postprocessor_plugins[plugin.name] = plugin

    def unregister_postprocessor(self, name: str) -> bool:
        """PostProcessor 플러그인 제거."""
        if name in self._postprocessor_plugins:
            del self._postprocessor_plugins[name]
            return True
        return False

    def get_postprocessor(self, name: str) -> Optional[PostProcessorPlugin]:
        """PostProcessor 플러그인 조회."""
        return self._postprocessor_plugins.get(name)

    def list_postprocessors(self) -> List[Dict[str, str]]:
        """등록된 PostProcessor 플러그인 목록."""
        return [
            {
                "name": p.name,
                "display_name": p.display_name,
                "version": p.version
            }
            for p in self._postprocessor_plugins.values()
        ]

    # === Utility ===
    
    def clear_all(self) -> None:
        """모든 플러그인 제거."""
        self._connector_plugins.clear()
        self._postprocessor_plugins.clear()

    def get_stats(self) -> Dict[str, int]:
        """등록된 플러그인 통계."""
        return {
            "connectors": len(self._connector_plugins),
            "postprocessors": len(self._postprocessor_plugins)
        }
