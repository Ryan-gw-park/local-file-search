import os
import msal
import requests
import json
from typing import Iterator, Dict, Any, List, Optional
from datetime import datetime
from .base import BaseConnector

class GraphConnector(BaseConnector):
    """
    Microsoft Graph API Connector for Outlook/OneDrive.
    Uses Device Code Flow for authentication.
    """
    
    # Common public client ID for manual testing or personal apps
    # Note: Users should ideally provide their own Client ID in a production setting.
    # This is a placeholder ID. The user might need to replace this.
    DEFAULT_CLIENT_ID = "4b7e7acf-8c52-4bee-bb5b-ce13a28601c9" 
    
    AUTHORITY = "https://login.microsoftonline.com/common"
    SCOPES = ["User.Read", "Mail.Read"] # Add Files.Read.All for OneDrive later

    def __init__(self, client_id: str = None, token_cache_path: str = "token_cache.bin"):
        self.client_id = client_id or self.DEFAULT_CLIENT_ID
        self.token_cache_path = token_cache_path
        self.access_token = None
        
        # Load cache
        self.cache = msal.SerializableTokenCache()
        if os.path.exists(self.token_cache_path):
            with open(self.token_cache_path, "r") as f:
                self.cache.deserialize(f.read())

        self.app = msal.PublicClientApplication(
            self.client_id, 
            authority=self.AUTHORITY,
            token_cache=self.cache
        )

    @property
    def name(self) -> str:
        return "graph_api"

    def authenticate(self) -> bool:
        """
        Check if we have a valid token or try to acquire one silently.
        Returns True if authenticated, False if user interaction is needed.
        """
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(self.SCOPES, account=accounts[0])
            if result:
                self.access_token = result["access_token"]
                return True
        return False

    def initiate_device_flow(self) -> Dict[str, Any]:
        """
        Start the device code flow.
        Returns a dict with 'user_code', 'verification_uri', and 'message'.
        """
        try:
            flow = self.app.initiate_device_flow(scopes=self.SCOPES)
            if "user_code" not in flow:
                raise Exception(f"Failed to create device flow: {flow.get('error_description')}")
            return flow
        except Exception as e:
            print(f"Device flow error: {e}")
            raise

    def complete_device_flow(self, flow: Dict[str, Any]) -> bool:
        """
        Wait for user to complete the login in browser.
        Blocks until completion or timeout.
        """
        try:
            result = self.app.acquire_token_by_device_flow(flow)
            if "access_token" in result:
                self.access_token = result["access_token"]
                # Save cache
                if self.cache.has_state_changed:
                    with open(self.token_cache_path, "w") as f:
                        f.write(self.cache.serialize())
                return True
            else:
                print(f"Auth failed: {result.get('error_description')}")
                return False
        except Exception as e:
            print(f"Token acquisition error: {e}")
            return False

    def list_items(self, max_items: int = 100) -> Iterator[Dict[str, Any]]:
        """
        Fetch emails from the Inbox via Graph API.
        """
        if not self.access_token:
            print("Not authenticated.")
            return

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Endpoint: List messages from Inbox
        # $top=max_items, $select=subject,from,receivedDateTime,body
        url = f"https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?$top={max_items}&$select=id,subject,from,receivedDateTime,body"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Graph API Error: {response.status_code} - {response.text}")
                return

            data = response.json()
            messages = data.get("value", [])
            
            for msg in messages:
                yield self._process_message(msg)
                
            # TODO: Handle pagination (@odata.nextLink) if needed
            
        except Exception as e:
            print(f"Error fetching emails: {e}")

    def _process_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Graph API message object to internal format."""
        subject = msg.get("subject", "(No Subject)")
        sender_info = msg.get("from", {}).get("emailAddress", {})
        sender_name = sender_info.get("name", "Unknown")
        sender_email = sender_info.get("address", "Unknown")
        received = msg.get("receivedDateTime")
        body_content = msg.get("body", {}).get("content", "")
        
        # Simple HTML strip (naive)
        import re
        text_body = re.sub('<[^<]+?>', '', body_content)
        
        full_text = f"Subject: {subject}\nFrom: {sender_name} <{sender_email}>\nDate: {received}\n\n{text_body}"
        
        return {
            "id": f"graph:{msg['id']}",
            "source": "Outlook(Cloud)",
            "text": full_text,
            "metadata": {
                "filename": subject[:100], # Trucate filename if too long
                "path": f"outlook_cloud:{msg['id']}",
                "modified": received,
                "author": sender_name,
                "type": "email",
                "folder": "Inbox"
            }
        }

    def close(self):
        pass
