"""
Google Docs Integration Client for Groww Weekly Review AI Agent.

This module handles:
- Creating new Google Documents
- Formatting and publishing structured pulse reports
- Managing document organization in Google Drive folders
- Integration with MCP server for content appending
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Try importing Google Docs API libraries
try:
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

load_dotenv()
logger = logging.getLogger(__name__)


class GoogleDocsClient:
    """Client for Google Docs integration via Google Docs API and MCP server."""
    
    SCOPES = ['https://www.googleapis.com/auth/docs',
              'https://www.googleapis.com/auth/drive']
    
    def __init__(self, 
                 mcp_server_url: str = None,
                 service_account_json_path: str = None,
                 use_mcp_only: bool = False):
        """
        Initialize the Google Docs client.
        
        Args:
            mcp_server_url: URL of the MCP server for content appending
            service_account_json_path: Path to Google service account credentials JSON
            use_mcp_only: If True, only use MCP server (requires pre-created doc_id)
        """
        self.mcp_server_url = mcp_server_url or os.getenv(
            'DOCS_MCP_SERVER_URL',
            'https://mcp-server-production-e580.up.railway.app'
        )
        self.service_account_path = (
            service_account_json_path
            or os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            or os.getenv('CREDENTIALS_JSON')
        )
        self.oauth_token_json = (
            os.getenv('GOOGLE_OAUTH_TOKEN_JSON')
            or os.getenv('GOOGLE_TOKEN_JSON')
            or os.getenv('TOKENS_JSON')
        )
        self.use_mcp_only = use_mcp_only
        self.docs_service = None
        self.drive_service = None
        
        # Initialize Google API services if available and not MCP-only mode
        if GOOGLE_API_AVAILABLE and not use_mcp_only:
            self._init_google_services()
    
    def _init_google_services(self):
        """Initialize Google Docs and Drive API services."""
        try:
            # Try service account credentials first
            credentials_loaded = False
            if self.service_account_path:
                if os.path.exists(self.service_account_path):
                    creds = service_account.Credentials.from_service_account_file(
                        self.service_account_path, scopes=self.SCOPES)
                    logger.info(f"Loaded service account credentials from {self.service_account_path}")
                    credentials_loaded = True
                else:
                    try:
                        creds_data = json.loads(self.service_account_path)
                        creds = service_account.Credentials.from_service_account_info(
                            creds_data, scopes=self.SCOPES)
                        logger.info("Loaded service account credentials from environment JSON")
                        credentials_loaded = True
                    except Exception as e:
                        logger.warning(f"Could not parse GOOGLE_SERVICE_ACCOUNT_JSON: {e}")

            if not credentials_loaded:
                oauth_token_json = self.oauth_token_json or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if oauth_token_json and os.path.exists(oauth_token_json):
                    from google.oauth2.credentials import Credentials
                    from google.auth.transport.requests import Request
                    creds = Credentials.from_authorized_user_file(oauth_token_json, self.SCOPES)
                    if creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    logger.info(f"Loaded OAuth credentials from {oauth_token_json}")
                    credentials_loaded = True
                elif self.oauth_token_json:
                    try:
                        from google.oauth2.credentials import Credentials
                        from google.auth.transport.requests import Request
                        oauth_data = json.loads(self.oauth_token_json)
                        creds = Credentials.from_authorized_user_info(oauth_data, self.SCOPES)
                        if creds.expired and creds.refresh_token:
                            creds.refresh(Request())
                        logger.info("Loaded OAuth credentials from environment JSON")
                        credentials_loaded = True
                    except Exception as e:
                        logger.warning(f"Could not parse OAuth token JSON from environment: {e}")
                elif os.path.exists('token.json'):
                    try:
                        from google.oauth2.credentials import Credentials
                        from google.auth.transport.requests import Request
                        creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
                        if creds.expired and creds.refresh_token:
                            creds.refresh(Request())
                        logger.info("Loaded OAuth credentials from token.json")
                        credentials_loaded = True
                    except Exception as e:
                        logger.warning(f"Could not load token.json OAuth credentials: {e}")

                if not credentials_loaded:
                    logger.warning("No credentials found. Set use_mcp_only=True to use MCP server only.")
                    return
            
            self.docs_service = build('docs', 'v1', credentials=creds)
            self.drive_service = build('drive', 'v3', credentials=creds)
            logger.info("Google Docs and Drive services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google services: {e}")
            logger.warning("Falling back to MCP-only mode for content appending")
    
    def _get_or_create_folder(self, folder_name: str = "Groww Weekly Reviews") -> str:
        """
        Get or create a folder in Google Drive for organizing documents.
        
        Args:
            folder_name: Name of the folder to create/find
            
        Returns:
            Folder ID if successful, None otherwise
        """
        if not self.drive_service:
            logger.warning("Drive service not available; skipping folder creation")
            return None
        
        try:
            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()
            
            files = results.get('files', [])
            if files:
                folder_id = files[0]['id']
                logger.info(f"Found existing folder: {folder_name} (ID: {folder_id})")
                return folder_id
            
            # Create new folder if not found
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.drive_service.files().create(body=file_metadata, fields='id').execute()
            folder_id = folder.get('id')
            logger.info(f"Created new folder: {folder_name} (ID: {folder_id})")
            return folder_id
        except HttpError as e:
            logger.error(f"Error managing Drive folder: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in folder management: {e}")
            return None
    
    def create_document(self, title: str, folder_id: str = None) -> Optional[str]:
        """
        Create a new Google Document.
        
        Args:
            title: Title of the document
            folder_id: Optional folder ID to place document in
            
        Returns:
            Document ID if successful, None otherwise
        """
        if not self.docs_service:
            logger.error("Google Docs service not initialized. Cannot create document.")
            return None
        
        try:
            body = {'title': title}
            doc = self.docs_service.documents().create(body=body).execute()
            doc_id = doc.get('id')
            logger.info(f"Created document: {title} (ID: {doc_id})")
            
            # Move to folder if specified
            if folder_id and self.drive_service:
                try:
                    self.drive_service.files().update(
                        fileId=doc_id,
                        addParents=folder_id,
                        fields='id, parents'
                    ).execute()
                    logger.info(f"Moved document to folder: {folder_id}")
                except Exception as e:
                    logger.warning(f"Could not move document to folder: {e}")
            
            return doc_id
        except HttpError as e:
            logger.error(f"Error creating document: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating document: {e}")
            return None
    
    def format_pulse_for_docs(self, pulse_data: Dict) -> str:
        """
        Format the pulse report JSON into structured Google Docs text content.
        
        Args:
            pulse_data: Dictionary containing pulse report data
            
        Returns:
            Formatted text content for Google Docs
        """
        lines = []
        
        # Title
        title = pulse_data.get('title', 'Groww Weekly Pulse Report')
        lines.append(f"{title}\n")
        
        # Week/Date information
        timestamp = pulse_data.get('timestamp', datetime.now().isoformat())
        lines.append(f"Generated: {timestamp}\n")
        
        # Summary stats
        if 'summary' in pulse_data:
            summary = pulse_data['summary']
            lines.append("SUMMARY STATISTICS")
            lines.append(f"Total Reviews Analyzed: {summary.get('total_reviews', 'N/A')}")
            lines.append(f"Reviews Sampled: {summary.get('sampled_reviews', 'N/A')}")
            lines.append(f"Date Range: {summary.get('date_range', 'N/A')}\n")
        
        # Theme Analysis
        if 'themes' in pulse_data and pulse_data['themes']:
            lines.append("TOP THEMES")
            for idx, theme in enumerate(pulse_data['themes'][:3], 1):
                lines.append(f"\n{idx}. {theme.get('theme', 'Unknown Theme')}")
                lines.append(f"   Count: {theme.get('count', 0)} reviews")
                
                # Sentiment breakdown
                if 'sentiment_breakdown' in theme:
                    sentiment = theme['sentiment_breakdown']
                    lines.append(f"   Sentiment: Positive {sentiment.get('positive', 0)} | "
                               f"Neutral {sentiment.get('neutral', 0)} | "
                               f"Negative {sentiment.get('negative', 0)}")
                
                # Key words
                if 'key_words' in theme:
                    words = theme['key_words'][:5]
                    lines.append(f"   Key Words: {', '.join(words)}")
                
                # Representative quotes
                if 'quotes' in theme:
                    lines.append("   Representative Quotes:")
                    for quote in theme['quotes'][:3]:
                        lines.append(f"   - \"{quote}\"")
        
        # Action Items
        if 'action_items' in pulse_data and pulse_data['action_items']:
            lines.append("\n\nRECOMMENDED ACTIONS")
            for idx, action in enumerate(pulse_data['action_items'], 1):
                lines.append(f"\n{idx}. {action.get('title', 'Action Item')}")
                if 'description' in action:
                    lines.append(f"   {action['description']}")
                if 'priority' in action:
                    lines.append(f"   Priority: {action['priority']}")
        
        # Final notes
        if 'notes' in pulse_data:
            lines.append(f"\n\nNOTES\n{pulse_data['notes']}")
        
        return '\n'.join(lines)
    
    def append_via_mcp(self, doc_id: str, content: str) -> bool:
        """
        Append content to a Google Doc via MCP server.
        
        Args:
            doc_id: Google Doc ID
            content: Content to append
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.mcp_server_url}/append_to_doc"
            payload = {
                "doc_id": doc_id,
                "content": content
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    logger.info(f"Successfully appended content to doc {doc_id} via MCP")
                    return True
                else:
                    logger.error(f"MCP append failed: {result.get('message', 'Unknown error')}")
                    return False
            else:
                logger.error(f"MCP server error: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.Timeout:
            logger.error(f"Timeout connecting to MCP server at {self.mcp_server_url}")
            return False
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error to MCP server at {self.mcp_server_url}")
            return False
        except Exception as e:
            logger.error(f"Error appending via MCP: {e}")
            return False

    def append_via_google_docs(self, doc_id: str, content_text: str) -> bool:
        """
        Append content to an existing Google Doc using the Docs API.

        Args:
            doc_id: Google Doc ID
            content_text: Text to append

        Returns:
            True if successful, False otherwise
        """
        if not self.docs_service:
            logger.warning("Google Docs service is not available for direct append")
            return False

        try:
            document = self.docs_service.documents().get(documentId=doc_id).execute()
            body_content = document.get('body', {}).get('content', [])
            end_index = 1
            if body_content:
                end_index = body_content[-1].get('endIndex', 1)

            # Ensure readable separation from existing content
            if end_index > 1 and not content_text.startswith('\n'):
                content_text = '\n\n' + content_text

            requests_body = {
                'requests': [
                    {
                        'insertText': {
                            'location': {'index': end_index},
                            'text': content_text
                        }
                    }
                ]
            }
            self.docs_service.documents().batchUpdate(
                documentId=doc_id,
                body=requests_body
            ).execute()
            logger.info(f"Successfully appended content directly to doc {doc_id}")
            return True
        except HttpError as e:
            logger.error(f"Google Docs API error appending to doc: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error appending via Google Docs API: {e}")
            return False
    
    def publish_pulse_report(self, 
                            pulse_data: Dict,
                            doc_title: str = None,
                            doc_id: str = None,
                            folder_name: str = "Groww Weekly Reviews") -> Tuple[bool, Optional[str]]:
        """
        Publish a pulse report to Google Docs.
        
        Args:
            pulse_data: The pulse report data to publish
            doc_title: Title for the document (auto-generated if None)
            doc_id: Existing document ID (if None, creates new document)
            folder_name: Folder name for organizing documents
            
        Returns:
            Tuple of (success: bool, doc_id: str or None)
        """
        try:
            # Generate document title if not provided
            if not doc_title:
                timestamp = datetime.now()
                week_num = timestamp.isocalendar()[1]
                year = timestamp.year
                doc_title = f"Groww Weekly Pulse - {year}-W{week_num:02d}"
            
            # Create new document if doc_id not provided
            if not doc_id:
                if self.use_mcp_only:
                    logger.error("Cannot create a new document in MCP-only mode")
                    return False, None

                folder_id = self._get_or_create_folder(folder_name)
                doc_id = self.create_document(doc_title, folder_id)
                if not doc_id:
                    logger.error("Failed to create new document")
                    return False, None

            # Format content
            formatted_content = self.format_pulse_for_docs(pulse_data)

            # If Google Docs direct API is available, try direct append first
            if self.docs_service and doc_id:
                if self.append_via_google_docs(doc_id, formatted_content):
                    logger.info(f"Successfully published pulse report to doc: {doc_id}")
                    return True, doc_id
                logger.warning("Direct Google Docs append failed; attempting MCP fallback")

            # Fallback to MCP append when direct API is unavailable or failed
            if not self.append_via_mcp(doc_id, formatted_content):
                logger.error("Failed to append content via MCP")
                return False, doc_id

            logger.info(f"Successfully published pulse report to doc: {doc_id}")
            return True, doc_id
        except Exception as e:
            logger.error(f"Error publishing pulse report: {e}")
            return False, None
    
    def health_check(self) -> bool:
        """
        Check if MCP server is healthy.
        
        Returns:
            True if server is responsive, False otherwise
        """
        try:
            response = requests.get(f"{self.mcp_server_url}/", timeout=5)
            is_healthy = response.status_code == 200
            if is_healthy:
                logger.info("MCP server health check passed")
            else:
                logger.warning(f"MCP server returned status {response.status_code}")
            return is_healthy
        except requests.exceptions.RequestException as e:
            logger.error(f"MCP server health check failed: {e}")
            return False


def create_pulse_document(pulse_data: Dict, 
                         doc_title: str = None,
                         mcp_server_url: str = None,
                         use_mcp_only: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to create and publish a pulse report to Google Docs.
    
    Args:
        pulse_data: The pulse report data
        doc_title: Optional title for the document
        mcp_server_url: Optional MCP server URL
        use_mcp_only: If True, use only MCP server (requires pre-created doc_id in pulse_data)
        
    Returns:
        Tuple of (success: bool, doc_id: str or None)
    """
    client = GoogleDocsClient(
        mcp_server_url=mcp_server_url,
        use_mcp_only=use_mcp_only
    )

    # If there is no Google Docs API service available, ensure MCP is reachable.
    if not client.docs_service and not client.health_check():
        logger.error("MCP server is not healthy")
        return False, None

    # Preserve any existing doc_id in pulse_data, or fallback to environment.
    doc_id = pulse_data.get('doc_id')
    if not doc_id:
        doc_id = os.getenv('GOOGLE_DOC_ID')
        if doc_id:
            logger.info(f"Using GOOGLE_DOC_ID from environment: {doc_id}")
            pulse_data['doc_id'] = doc_id

    success, doc_id = client.publish_pulse_report(
        pulse_data=pulse_data,
        doc_title=doc_title,
        doc_id=doc_id
    )
    
    return success, doc_id
