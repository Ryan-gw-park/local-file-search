"""
Local Finder X v2.0 - Outlook Connector

MS Graph API-based Outlook email connector.
Requires Azure App registration for OAuth 2.0 PKCE.
"""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

try:
    import msal
    MSAL_AVAILABLE = True
except ImportError:
    MSAL_AVAILABLE = False
    msal = None

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


# =============================================================================
# Configuration
# =============================================================================

# Azure AD Application settings (to be configured by user)
DEFAULT_CLIENT_ID = ""  # Set via environment or settings
DEFAULT_TENANT_ID = "common"  # "common" for multi-tenant

# Graph API endpoints
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
MESSAGES_ENDPOINT = f"{GRAPH_BASE_URL}/me/messages"
SEARCH_ENDPOINT = f"{GRAPH_BASE_URL}/search/query"

# Required scopes for Outlook access
OUTLOOK_SCOPES = [
    "Mail.Read",
    "Mail.ReadBasic",
    "User.Read",
]


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class OutlookMessage:
    """Represents an Outlook email message."""
    id: str
    subject: str
    body_preview: str
    body_content: str = ""
    sender: str = ""
    recipients: List[str] = field(default_factory=list)
    received_at: str = ""
    has_attachments: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "subject": self.subject,
            "body_preview": self.body_preview,
            "body_content": self.body_content,
            "sender": self.sender,
            "recipients": self.recipients,
            "received_at": self.received_at,
            "has_attachments": self.has_attachments,
        }


# =============================================================================
# Token Cache (Persistent)
# =============================================================================

class TokenCache:
    """Simple token cache for MSAL."""
    
    def __init__(self, cache_path: Optional[str] = None):
        self.cache_path = cache_path
        self._cache = None
    
    @property
    def cache(self):
        if not MSAL_AVAILABLE:
            return None
        if self._cache is None:
            self._cache = msal.SerializableTokenCache()
            if self.cache_path and os.path.exists(self.cache_path):
                with open(self.cache_path, "r") as f:
                    self._cache.deserialize(f.read())
        return self._cache
    
    def save(self):
        if self._cache and self.cache_path:
            with open(self.cache_path, "w") as f:
                f.write(self._cache.serialize())


# =============================================================================
# Outlook Connector
# =============================================================================

class OutlookConnector:
    """
    Connector for Outlook via MS Graph API.
    
    Uses OAuth 2.0 PKCE flow for authentication.
    Requires Azure App registration.
    """
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        token_cache_path: Optional[str] = None,
    ):
        self.client_id = client_id or os.environ.get("AZURE_CLIENT_ID", DEFAULT_CLIENT_ID)
        self.tenant_id = tenant_id or os.environ.get("AZURE_TENANT_ID", DEFAULT_TENANT_ID)
        self.token_cache = TokenCache(token_cache_path)
        self._app = None
        self._access_token = None
    
    @property
    def is_available(self) -> bool:
        """Check if required dependencies are available."""
        return MSAL_AVAILABLE and REQUESTS_AVAILABLE and bool(self.client_id)
    
    @property
    def app(self):
        """Get or create MSAL public client application."""
        if not MSAL_AVAILABLE:
            return None
        if self._app is None:
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            self._app = msal.PublicClientApplication(
                self.client_id,
                authority=authority,
                token_cache=self.token_cache.cache,
            )
        return self._app
    
    def authenticate_interactive(self) -> bool:
        """
        Perform interactive authentication.
        Opens browser for user login.
        
        Returns:
            True if authentication successful.
        """
        if not self.is_available:
            return False
        
        try:
            # Try to get cached token first
            accounts = self.app.get_accounts()
            if accounts:
                result = self.app.acquire_token_silent(OUTLOOK_SCOPES, account=accounts[0])
                if result and "access_token" in result:
                    self._access_token = result["access_token"]
                    return True
            
            # Interactive login required
            result = self.app.acquire_token_interactive(OUTLOOK_SCOPES)
            if result and "access_token" in result:
                self._access_token = result["access_token"]
                self.token_cache.save()
                return True
            
            return False
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def authenticate_device_flow(self) -> bool:
        """
        Authenticate using device code flow.
        Useful for headless environments.
        
        Returns:
            True if authentication successful.
        """
        if not self.is_available:
            return False
        
        try:
            flow = self.app.initiate_device_flow(OUTLOOK_SCOPES)
            print(flow.get("message", ""))
            
            result = self.app.acquire_token_by_device_flow(flow)
            if result and "access_token" in result:
                self._access_token = result["access_token"]
                self.token_cache.save()
                return True
            
            return False
            
        except Exception as e:
            print(f"Device flow error: {e}")
            return False
    
    def get_messages(
        self,
        top: int = 50,
        skip: int = 0,
        filter_query: Optional[str] = None,
    ) -> List[OutlookMessage]:
        """
        Fetch messages from Outlook.
        
        Args:
            top: Number of messages to fetch.
            skip: Number of messages to skip.
            filter_query: OData filter query.
        
        Returns:
            List of OutlookMessage objects.
        """
        if not self._access_token:
            return []
        
        headers = {"Authorization": f"Bearer {self._access_token}"}
        params = {
            "$top": top,
            "$skip": skip,
            "$select": "id,subject,bodyPreview,body,from,toRecipients,receivedDateTime,hasAttachments",
        }
        
        if filter_query:
            params["$filter"] = filter_query
        
        try:
            response = requests.get(MESSAGES_ENDPOINT, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            messages = []
            for item in data.get("value", []):
                msg = OutlookMessage(
                    id=item.get("id", ""),
                    subject=item.get("subject", ""),
                    body_preview=item.get("bodyPreview", ""),
                    body_content=item.get("body", {}).get("content", ""),
                    sender=item.get("from", {}).get("emailAddress", {}).get("address", ""),
                    recipients=[
                        r.get("emailAddress", {}).get("address", "")
                        for r in item.get("toRecipients", [])
                    ],
                    received_at=item.get("receivedDateTime", ""),
                    has_attachments=item.get("hasAttachments", False),
                )
                messages.append(msg)
            
            return messages
            
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return []
    
    def search_messages(self, query: str, top: int = 25) -> List[OutlookMessage]:
        """
        Search messages using Graph Search API.
        
        Args:
            query: Search query string.
            top: Number of results.
        
        Returns:
            List of matching messages.
        """
        if not self._access_token:
            return []
        
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "requests": [{
                "entityTypes": ["message"],
                "query": {"queryString": query},
                "from": 0,
                "size": top,
            }]
        }
        
        try:
            response = requests.post(SEARCH_ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            messages = []
            for hit_container in data.get("value", []):
                for hit in hit_container.get("hitsContainers", []):
                    for result in hit.get("hits", []):
                        resource = result.get("resource", {})
                        msg = OutlookMessage(
                            id=resource.get("id", ""),
                            subject=resource.get("subject", ""),
                            body_preview=resource.get("bodyPreview", ""),
                            sender=resource.get("from", {}).get("emailAddress", {}).get("address", ""),
                            received_at=resource.get("receivedDateTime", ""),
                        )
                        messages.append(msg)
            
            return messages
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def logout(self) -> None:
        """Clear cached tokens."""
        if self.app:
            for account in self.app.get_accounts():
                self.app.remove_account(account)
        self._access_token = None
        if self.token_cache.cache_path:
            try:
                os.remove(self.token_cache.cache_path)
            except OSError:
                pass


__all__ = [
    "OutlookConnector",
    "OutlookMessage",
    "TokenCache",
    "MSAL_AVAILABLE",
    "OUTLOOK_SCOPES",
]
