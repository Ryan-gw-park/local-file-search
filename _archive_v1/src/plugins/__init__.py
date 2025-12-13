# src/plugins/__init__.py
# Phase 4: 2. 플러그인 시스템 설계

from .interfaces import ConnectorPlugin, PostProcessorPlugin
from .registry import PluginRegistry

__all__ = ["ConnectorPlugin", "PostProcessorPlugin", "PluginRegistry"]
