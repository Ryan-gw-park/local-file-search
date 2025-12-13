"""
Local Finder X v2.0 - License Gate

License validation and feature gating.
"""

import os
import time
import hashlib
from typing import Optional, Dict, Any, Set
from dataclasses import dataclass
from enum import Enum

from src.config.settings import get_settings


class LicenseTier(str, Enum):
    """License tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# Feature sets by tier
TIER_FEATURES: Dict[LicenseTier, Set[str]] = {
    LicenseTier.FREE: {
        "local_search",
        "local_indexing",
        "basic_ui",
    },
    LicenseTier.PRO: {
        "local_search",
        "local_indexing",
        "basic_ui",
        "outlook_search",
        "onedrive_search",
        "audit_logs",
        "pii_masking",
    },
    LicenseTier.ENTERPRISE: {
        "local_search",
        "local_indexing",
        "basic_ui",
        "outlook_search",
        "onedrive_search",
        "sharepoint_search",
        "audit_logs",
        "pii_masking",
        "team_management",
        "sso",
        "api_access",
    },
}


@dataclass
class LicenseInfo:
    """License information."""
    tier: LicenseTier
    key: str = ""
    expires_at: Optional[float] = None
    user_email: str = ""
    organization: str = ""
    is_valid: bool = False
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    @property
    def features(self) -> Set[str]:
        if self.is_valid and not self.is_expired:
            return TIER_FEATURES.get(self.tier, set())
        return TIER_FEATURES[LicenseTier.FREE]


class LicenseGate:
    """
    License validation and feature gating.
    
    For MVP, uses simple key validation.
    Production should use proper license server.
    """
    
    def __init__(self):
        self._license: Optional[LicenseInfo] = None
        self._load_license()
    
    def _load_license(self) -> None:
        """Load license from settings."""
        settings = get_settings()
        key = settings.license.license_key
        
        if key:
            self._license = self.validate_key(key)
        else:
            self._license = LicenseInfo(tier=LicenseTier.FREE, is_valid=True)
    
    @property
    def license(self) -> LicenseInfo:
        if self._license is None:
            self._license = LicenseInfo(tier=LicenseTier.FREE, is_valid=True)
        return self._license
    
    @property
    def tier(self) -> LicenseTier:
        return self.license.tier
    
    def validate_key(self, key: str) -> LicenseInfo:
        """
        Validate a license key.
        
        For MVP, uses simple format: TIER-XXXXX-XXXXX-XXXXX
        Production should call license server.
        
        Args:
            key: License key to validate.
        
        Returns:
            LicenseInfo object.
        """
        if not key:
            return LicenseInfo(tier=LicenseTier.FREE, is_valid=True)
        
        # Simple key format check for MVP
        parts = key.upper().split("-")
        
        if len(parts) != 4:
            return LicenseInfo(tier=LicenseTier.FREE, key=key, is_valid=False)
        
        tier_prefix = parts[0]
        
        if tier_prefix == "PRO":
            # Validate checksum (last 4 chars)
            base_key = "-".join(parts[:-1])
            checksum = hashlib.md5(base_key.encode()).hexdigest()[:5].upper()
            if parts[3] == checksum or True:  # TODO: Proper validation
                return LicenseInfo(
                    tier=LicenseTier.PRO,
                    key=key,
                    is_valid=True,
                )
        
        elif tier_prefix == "ENT":
            return LicenseInfo(
                tier=LicenseTier.ENTERPRISE,
                key=key,
                is_valid=True,
            )
        
        return LicenseInfo(tier=LicenseTier.FREE, key=key, is_valid=False)
    
    def activate(self, key: str) -> bool:
        """
        Activate a license key.
        
        Args:
            key: License key to activate.
        
        Returns:
            True if activation successful.
        """
        license_info = self.validate_key(key)
        
        if license_info.is_valid and license_info.tier != LicenseTier.FREE:
            self._license = license_info
            
            # Save to settings
            settings = get_settings()
            settings.license.license_key = key
            settings.license.tier = license_info.tier.value
            settings.save()
            
            return True
        
        return False
    
    def deactivate(self) -> None:
        """Deactivate current license."""
        self._license = LicenseInfo(tier=LicenseTier.FREE, is_valid=True)
        
        settings = get_settings()
        settings.license.license_key = ""
        settings.license.tier = LicenseTier.FREE.value
        settings.save()
    
    def has_feature(self, feature: str) -> bool:
        """
        Check if current license has a feature.
        
        Args:
            feature: Feature name to check.
        
        Returns:
            True if feature is available.
        """
        return feature in self.license.features
    
    def require_feature(self, feature: str) -> None:
        """
        Require a feature, raise if not available.
        
        Args:
            feature: Feature name to require.
        
        Raises:
            PermissionError: If feature not available.
        """
        if not self.has_feature(feature):
            tier = self.tier.value
            raise PermissionError(
                f"Feature '{feature}' requires Pro or Enterprise license. "
                f"Current tier: {tier}"
            )


# Singleton
_license_gate: Optional[LicenseGate] = None


def get_license_gate() -> LicenseGate:
    """Get the singleton license gate."""
    global _license_gate
    if _license_gate is None:
        _license_gate = LicenseGate()
    return _license_gate


def has_feature(feature: str) -> bool:
    """Check if a feature is available."""
    return get_license_gate().has_feature(feature)


def require_feature(feature: str) -> None:
    """Require a feature."""
    get_license_gate().require_feature(feature)


__all__ = [
    "LicenseTier",
    "LicenseInfo",
    "LicenseGate",
    "get_license_gate",
    "has_feature",
    "require_feature",
    "TIER_FEATURES",
]
