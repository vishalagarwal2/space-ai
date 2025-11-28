# knowledge_base/data_sources.py

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime
import tempfile
import requests
from pathlib import Path
from services.gcs import GCSHandler

# Google API
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

# Email processing
try:
    import email
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import base64
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

from django.conf import settings
from .models import DataSource, Document, UserGoogleOAuth
from .parsers import parser_registry
from uuid import uuid4


logger = logging.getLogger(__name__)


class OAuthMixin:
    """Mixin class to handle OAuth functionality"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.oauth_scopes = getattr(self, 'SCOPES', [])
        self.oauth_redirect_uri = getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', 
                                         'http://127.0.0.1:8000/api/google/oauth2callback')
    
    def get_oauth_flow(self):
        """Create OAuth flow instance"""
        if not GOOGLE_API_AVAILABLE:
            raise Exception("Google API libraries not available")
        
        credentials_file = self.credentials.get('credentials_file')
        scopes = getattr(settings, 'GOOGLE_COMBINED_SCOPES', [])
        flow = Flow.from_client_secrets_file(
            credentials_file,
            scopes=scopes,
            redirect_uri=self.oauth_redirect_uri
        )
        return flow
    
    def get_user_google_oauth(self):
        # Helper to get user's shared Google OAuth credentials
        logger.info(f"Fetching Google OAuth credentials for user: {getattr(self.data_source.user, 'id', None)}")
        user_oauth = getattr(self.data_source.user, 'google_oauth', None)
        if user_oauth:
            logger.info(f"User Google OAuth credentials found: {user_oauth}")
        else:
            logger.warning(f"User Google OAuth credentials not found. {user_oauth}")
        return user_oauth
    
    def get_oauth_credentials(self):
        # Use shared credentials if available
        user_oauth = self.get_user_google_oauth()
        cred_data = None
        if user_oauth and user_oauth.credentials:
            cred_data = user_oauth.credentials
            logger.info(f"Found user Google OAuth credentials. {cred_data}")
        else:
            logger.warning(f"No user Google OAuth credentials found. {cred_data}")

        try:
            if not cred_data or not all(key in cred_data for key in ['oauth_token', 'oauth_refresh_token']):
                logger.warning("OAuth credential data missing required keys.")
                return None

            logger.info(f"Building Credentials object from stored OAuth data. {cred_data}")
            credentials = Credentials(
                token=cred_data['oauth_token'],
                refresh_token=cred_data['oauth_refresh_token'],
                token_uri=cred_data['oauth_token_uri'],
                client_id=cred_data['oauth_client_id'],
                client_secret=cred_data['oauth_client_secret'],
                scopes=cred_data['oauth_scopes']
            )

            # Refresh if expired
            if credentials.expired:
                logger.info("OAuth credentials expired, refreshing...")
                credentials.refresh(Request())
                # Update stored credentials
                self.data_source.credentials.update({
                    'oauth_token': credentials.token,
                    'oauth_refresh_token': credentials.refresh_token,
                })
                self.data_source.save()
                logger.info("OAuth credentials refreshed and saved.")

            logger.info("OAuth credentials ready and valid.")
            return credentials

        except Exception as e:
            logger.error(f"Error getting OAuth credentials: {e}")
            return None
    def save_oauth_credentials(self, credentials):
        # Save to shared user record
        user_oauth, _ = UserGoogleOAuth.objects.get_or_create(user=self.data_source.user)
        user_oauth.credentials = credentials
        user_oauth.save()
    
    def get_oauth_authorization_url(self):
        """Get OAuth authorization URL"""
        try:
            flow = self.get_oauth_flow()
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            # Store state for verification (you should store this in your database)
            self.data_source.config['oauth_state'] = state
            self.data_source.save()
            
            return {
                'authorization_url': authorization_url,
                'state': state
            }
        except Exception as e:
            logger.error(f"Error getting OAuth authorization URL: {e}")
            raise
    
    def handle_oauth_callback(self, code, state):
        logger.info(f"Handling OAuth callback for source_type={self.data_source.source_type}")
        logger.info(f"Expected scopes: {self.oauth_scopes}")
        try:
            # Verify state
            stored_state = self.data_source.config.get('oauth_state')
            if stored_state != state:
                raise Exception("Invalid OAuth state")
            
            logger.info(f"Stored state: {stored_state}, Provided state: {state}")
            flow = self.get_oauth_flow()
            logger.info("About to fetch token with code: %s", code)
            flow.fetch_token(code=code)
            logger.info("Successfully fetched token")
            
            credentials = flow.credentials
            if not credentials:
                logger.error("No credentials after fetch_token, aborting OAuth callback.")
                return False
            
            if credentials:
                user_oauth, _ = UserGoogleOAuth.objects.get_or_create(user=self.data_source.user)
                user_oauth.credentials = {
                    'oauth_token': credentials.token,
                    'oauth_refresh_token': credentials.refresh_token,
                    'oauth_token_uri': credentials.token_uri,
                    'oauth_client_id': credentials.client_id,
                    'oauth_client_secret': credentials.client_secret,
                    'oauth_scopes': credentials.scopes,
                    'oauth_expiry': credentials.expiry.isoformat() if credentials.expiry else None
                }
                user_oauth.save()
                self.data_source.credentials = user_oauth.credentials
                
                # Clear OAuth state
                if 'oauth_state' in self.data_source.config:
                    del self.data_source.config['oauth_state']
                
                self.data_source.save()
                
                return True
            
            return False
            
        except Exception as e:
            import traceback
            logger.error("Exception in handle_oauth_callback: %s", traceback.format_exc())
            logger.error(f"OAuth callback error. code={code}, state={state}, stored_state={self.data_source.config.get('oauth_state')}, credentials_file={self.credentials.get('credentials_file')}")
            logger.error(f"Error handling OAuth callback: {e}")
            return False
    
    def is_oauth_authenticated(self):
        """Check if OAuth is authenticated"""
        logger.info("Checking if OAuth is authenticated for user: %s", getattr(self.data_source.user, 'id', None))
        credentials = self.get_oauth_credentials()
        if credentials is not None and credentials.valid:
            logger.info("OAuth is authenticated and credentials are valid.", credentials)
            return True
        else:
            logger.warning("OAuth is not authenticated or credentials are invalid.", credentials)
            return False


class BaseDataSource(ABC):
    """Base class for all data sources"""
    
    def __init__(self, data_source: DataSource):
        self.data_source = data_source
        self.user = data_source.user
        self.config = data_source.config
        self.credentials = data_source.credentials
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the data source"""
        pass

    @abstractmethod
    def upload(self, files: List[Dict[str, Any]]) -> List[Document]:
        """Upload files to the data source"""
        """files should be a list of dicts with 'file_name' and 'file_content' keys"""
        pass
    
    @abstractmethod
    def sync(self) -> Dict[str, Any]:
        """Sync data from the source"""
        pass
    
    @abstractmethod
    def get_documents(self) -> Iterator[Dict[str, Any]]:
        """Get documents from the source"""
        pass
    
    def requires_oauth(self) -> bool:
        """Check if this data source requires OAuth"""
        return False
    
    def get_oauth_info(self) -> Optional[Dict[str, Any]]:
        """Get OAuth information if applicable"""
        return None
    
    def get_raw_content_data(self, content) -> str:
        """Return raw content data, handling binary/text appropriately"""
        if isinstance(content, bytes):
            return f"Binary file content (size: {len(content)} bytes)"
        return str(content)
    
    def process_document(self, doc_data: Dict[str, Any]) -> Optional[Document]:
        """Process a single document"""
        try:
            # Create document record
            document = Document.objects.create(
                user=self.user,
                data_source=self.data_source,
                title=doc_data.get('title', 'Untitled'),
                original_filename=doc_data.get('filename', ''),
                file_path=doc_data.get('file_path', ''),
                file_size=doc_data.get('file_size', 0),
                mime_type=doc_data.get('mime_type', ''),
                raw_content=self.get_raw_content_data(doc_data.get('content', '')),
                source_metadata=doc_data.get('metadata', {}),
                status='pending',
            )
            
            # Process the document
            # self._process_document_content(document, doc_data)
            
            return document
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return None
    
    def _process_document_content(self, document: Document, doc_data: Dict[str, Any]):
        """Process document content using appropriate parser"""
        try:
            document.status = 'processing'
            document.save()
            
            # Get appropriate parser
            parser = parser_registry.get_parser(
                doc_data.get('file_path', ''),
                doc_data.get('mime_type', '')
            )
            if parser:
                logger.info(f"Found parser {parser.__class__.__name__} for file_path={doc_data.get('file_path', '')}, mime_type={doc_data.get('mime_type', '')}")
                # Parse the document
                # TODO: handle file_path which is not local
                if doc_data.get('file_path') and os.path.exists(doc_data['file_path']):
                    logger.info(f"Parsing document from file path: {doc_data['file_path']}")
                    parsed_result = parser.parse(doc_data['file_path'])
                else:
                    # Handle text content as before
                    logger.info("Parsing document from text content, writing to temp .txt file")
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
                        tmp_file.write(doc_data.get('content', ''))
                        tmp_file_path = tmp_file.name
                    try:
                        logger.info(f"Parsing temp file: {tmp_file_path}")
                        parsed_result = parser.parse(tmp_file_path)
                    finally:
                        logger.info(f"Deleting temp file: {tmp_file_path}")
                        os.unlink(tmp_file_path)
                
                if 'error' not in parsed_result:
                    document.processed_content = parsed_result.get('content', '')
                    document.processing_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'step': 'parsing',
                        'status': 'success',
                        'parser': parser.__class__.__name__
                    })
                    chunks = parsed_result.get('chunks', [document.processed_content])
                    document.status = 'processed'
                else:
                    document.processing_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'step': 'parsing',
                        'status': 'error',
                        'error': parsed_result['error']
                    })
                    document.status = 'error'
            else:
                document.processed_content = doc_data.get('content', '')
                document.processing_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'step': 'parsing',
                    'status': 'no_parser',
                    'message': 'No parser found for this file type'
                })
                document.status = 'processed'
            
            document.save()
            
        except Exception as e:
            logger.error(f"Error processing document content: {e}")
            document.status = 'error'
            document.processing_log.append({
                'timestamp': datetime.now().isoformat(),
                'step': 'processing',
                'status': 'error',
                'error': str(e)
            })
            document.save()

    def _get_suffix_from_mime(self, mime_type: str) -> str:
        logger.info(f"Getting file suffix for MIME type: {mime_type}")
        mapping = {
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
            'application/pdf': '.pdf',
            'image/png': '.png',
            'image/jpeg': '.jpg',
            # Add more as needed
        }
        suffix = mapping.get(mime_type, '.bin')
        logger.info(f"Suffix for MIME type {mime_type}: {suffix}")
        return suffix


class FileUploadDataSource(BaseDataSource):
    """Data source for user-uploaded files"""
    
    def authenticate(self) -> bool:
        """No authentication needed for file uploads"""
        return True
    
    def sync(self) -> Dict[str, Any]:
        """Sync uploaded files"""
        try:
            upload_dir = self.config.get('upload_dir', 'uploads')
            processed_count = 0
            
            # Process files in upload directory
            for file_path in Path(upload_dir).glob('**/*'):
                if file_path.is_file():
                    doc_data = self._process_uploaded_file(file_path)
                    if doc_data:
                        document = self.process_document(doc_data)
                        if document:
                            processed_count += 1
            
            return {
                'status': 'success',
                'processed_count': processed_count
            }
            
        except Exception as e:
            logger.error(f"Error syncing file uploads: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_documents(self) -> Iterator[Dict[str, Any]]:
        """Get uploaded documents"""
        upload_dir = self.config.get('upload_dir', 'uploads')
        
        for file_path in Path(upload_dir).glob('**/*'):
            if file_path.is_file():
                doc_data = self._process_uploaded_file(file_path)
                if doc_data:
                    yield doc_data
    
    def _process_uploaded_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Process a single uploaded file"""
        try:
            stat = file_path.stat()
            
            return {
                'title': file_path.name,
                'filename': file_path.name,
                'file_path': str(file_path),
                'file_size': stat.st_size,
                'mime_type': self._get_mime_type(file_path),
                'content': self._read_file_content(file_path),
                'metadata': {
                    'upload_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'source': 'file_upload'
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing uploaded file {file_path}: {e}")
            return None
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type for file"""
        try:
            import magic
            return magic.from_file(str(file_path), mime=True)
        except:
            # Fallback to extension-based detection
            ext = file_path.suffix.lower()
            mime_types = {
                '.txt': 'text/plain',
                '.pdf': 'application/pdf',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.mp3': 'audio/mpeg',
                '.mp4': 'video/mp4',
            }
            return mime_types.get(ext, 'application/octet-stream')
    
    def _read_file_content(self, file_path: Path) -> str:
        """Read file content as text if possible"""
        try:
            # Try to read as text first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            # Binary file or encoding issue
            return f"Binary file: {file_path.name}"


class GmailDataSource(BaseDataSource, OAuthMixin):
    """Data source for Gmail emails with OAuth support"""

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, data_source: DataSource):
        BaseDataSource.__init__(self, data_source)
        OAuthMixin.__init__(self)

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default configuration for Google Drive data source"""
        return {
            "config": {
                "query": "",  # Empty query will match all emails
                "max_results": 10
            },
            "credentials": {
              "credentials_file": getattr(settings, "GMAIL_AUTH_CREDENTIALS", "")
            },
            "auto_sync": False, # TODO: figure out how to handle auto-sync for Drive
            "sync_frequency": 10
        }
    
    def upload(self, files: List[Dict[str, Any]]) -> List[Document]:
        """Uploading is not supported for GmailDataSource."""
        raise NotImplementedError("Upload is not supported for GmailDataSource.")

    def requires_oauth(self) -> bool:
        """Gmail requires OAuth"""
        return True
    
    def get_oauth_info(self) -> Optional[Dict[str, Any]]:
        """Get OAuth information for Gmail"""
        if not self.is_oauth_authenticated():
            try:
                logger.info("OAuth not authenticated for GmailDataSource. Getting authorization URL.")
                oauth_data = self.get_oauth_authorization_url()
                logger.info(f"Obtained OAuth authorization URL for Gmail: {oauth_data.get('authorization_url')}")
                return {
                    'authorization_url': oauth_data['authorization_url'],
                    'state': oauth_data['state'],
                    'service_name': 'Gmail'
                }
            except Exception as e:
                logger.error(f"Error getting OAuth info: {e}")
                return None
        logger.info("OAuth already authenticated for GmailDataSource. No authorization URL needed.")
        return None
    
    def authenticate(self) -> bool:
        """Authenticate with Gmail API using OAuth"""
        if not GOOGLE_API_AVAILABLE:
            logger.error("Google API libraries not available")
            return False
        
        # Check if we have OAuth credentials
        if self.is_oauth_authenticated():
            credentials = self.get_oauth_credentials()
            if credentials:
                try:
                    self.service = build('gmail', 'v1', credentials=credentials)
                    return True
                except Exception as e:
                    logger.error(f"Error building Gmail service: {e}")
                    return False
        
        return False
    
    #TODO: figure out how to avoid duplication
    def sync(self) -> Dict[str, Any]:
        """Sync Gmail emails"""
        try:
            if not self.authenticate():
                return {'status': 'error', 'error': 'Authentication failed'}
            
            processed_count = 0
            
            for email_data in self.get_documents():
                document = self.process_document(email_data)
                if document:
                    processed_count += 1
            
            return {
                'status': 'success',
                'processed_count': processed_count
            }
            
        except Exception as e:
            logger.error(f"Error syncing Gmail: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_documents(self) -> Iterator[Dict[str, Any]]:
        """Get Gmail emails"""
        try:
            # Get configuration
            max_results = self.config.get('max_results', 100)
            query = self.config.get('query', '')

            logger.info(f"Fetching Gmail documents with query: {query}, max_results: {max_results}")
            
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            for message in messages:
                msg_id = message['id']
                email_data = self._get_email_data(msg_id)
                if email_data:
                    yield email_data
                    
        except Exception as e:
            logger.error(f"Error getting Gmail documents: {e}")
    
    def _get_email_data(self, msg_id: str) -> Optional[Dict[str, Any]]:
        """Get email data for a specific message"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract body
            body = self._extract_email_body(message['payload'])
            
            return {
                'title': subject,
                'filename': f"email_{msg_id}.txt",
                'file_path': '',
                'file_size': len(body),
                'mime_type': 'text/plain',
                'content': body,
                'metadata': {
                    'message_id': msg_id,
                    'sender': sender,
                    'date': date,
                    'source': 'gmail'
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting email data for {msg_id}: {e}")
            return None
    
    def _extract_email_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        elif payload['mimeType'] == 'text/plain':
            if 'data' in payload['body']:
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        return body


class GoogleDriveDataSource(BaseDataSource, OAuthMixin):
    """Data source for Google Drive files with OAuth support"""

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    def __init__(self, data_source: DataSource):
        BaseDataSource.__init__(self, data_source)
        OAuthMixin.__init__(self)

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default configuration for Google Drive data source"""
        return {
            "config": {
                "query": "",  # Empty query will match all emails
                "max_results": 10
            },
            "credentials": {
              "credentials_file": getattr(settings, "GDRIVE_AUTH_CREDENTIALS", "")
            },
            "auto_sync": False, # TODO: figure out how to handle auto-sync for Drive
            "sync_frequency": 10
        }
    
    def upload(self, files: List[Dict[str, Any]]) -> List[Document]:
        """Uploading is not supported for GoogleDriveDataSource."""
        raise NotImplementedError("Upload is not supported for GoogleDriveDataSource.")

    def requires_oauth(self) -> bool:
        """Google Drive requires OAuth"""
        return True
    
    def get_oauth_info(self) -> Optional[Dict[str, Any]]:
        """Get OAuth information for Google Drive"""
        if not self.is_oauth_authenticated():
            try:
                oauth_data = self.get_oauth_authorization_url()
                return {
                    'authorization_url': oauth_data['authorization_url'],
                    'state': oauth_data['state'],
                    'service_name': 'Google Drive'
                }
            except Exception as e:
                logger.error(f"Error getting OAuth info: {e}")
                return None
        return None
    
    def authenticate(self) -> bool:
        """Authenticate with Google Drive API using OAuth"""
        if not GOOGLE_API_AVAILABLE:
            logger.error("Google API libraries not available")
            return False
        
        # Check if we have OAuth credentials
        if self.is_oauth_authenticated():
            credentials = self.get_oauth_credentials()
            if credentials:
                try:
                    self.service = build('drive', 'v3', credentials=credentials)
                    return True
                except Exception as e:
                    logger.error(f"Error building Drive service: {e}")
                    return False
        
        return False
    
    def sync(self) -> Dict[str, Any]:
        """Sync Google Drive files"""
        try:
            if not self.authenticate():
                return {'status': 'error', 'error': 'Authentication failed'}
            
            processed_count = 0
            
            for file_data in self.get_documents():
                document = self.process_document(file_data)
                if document:
                    processed_count += 1
            
            return {
                'status': 'success',
                'processed_count': processed_count
            }
            
        except Exception as e:
            logger.error(f"Error syncing Google Drive: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_documents(self) -> Iterator[Dict[str, Any]]:
        """Get Google Drive files"""
        try:
            # Get configuration
            max_results = self.config.get('max_results', 100)
            file_types = self.config.get('file_types', [])
            
            # Build query
            query = "trashed=false"
            if file_types:
                mime_type_query = " or ".join([f"mimeType='{ft}'" for ft in file_types])
                query += f" and ({mime_type_query})"
            
            # Search for files
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            
            for file in files:
                file_name = file['name']
                mime_type = file['mimeType']
                if mime_type == 'application/vnd.google-apps.folder':
                    yield from self._fetch_folder_contents(file['id'], file_name)
                else:
                    file_data = self._get_file_data(file)
                    if file_data:
                        yield file_data
                    
        except Exception as e:
            logger.error(f"Error getting Google Drive documents: {e}")

    def _fetch_folder_contents(self, folder_id: str, parent_path: str = "") -> Iterator[Dict[str, Any]]:
        try:
            results = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)"
            ).execute()
            files = results.get('files', [])
            for file in files:
                file_name = file['name']
                mime_type = file['mimeType']
                current_path = os.path.join(parent_path, file_name)
                if mime_type == 'application/vnd.google-apps.folder':
                    # Recursively fetch subfolders
                    yield from self._fetch_folder_contents(file['id'], current_path)
                else:
                    file_data = self._get_file_data(file, parent_path)
                    if file_data:
                        yield file_data
        except Exception as e:
            logger.error(f"Error fetching folder contents for {folder_id}: {e}")
    
    def _get_file_data(self, file: Dict[str, Any], parent_path: str = "") -> Optional[Dict[str, Any]]:
        """Get file data from Google Drive and optionally save to disk for verification"""
        try:
            file_id = file['id']
            file_name = file['name']
            mime_type = file['mimeType']

            logger.info(f"Processing Google Drive file: id={file_id}, name={file_name}, mime_type={mime_type}")


            # Skip folders as documents
            if mime_type == 'application/vnd.google-apps.folder':
                logger.info(f"Skipping folder: {file_name} ({file_id})")
                return None
            
            # Download file content
            if mime_type.startswith('application/vnd.google-apps'):
                export_mime_type = self._get_export_mime_type(mime_type)
                logger.info(f"File is a Google Workspace file. Exporting as {export_mime_type}")
                content = self._download_file_content(file_id, mime_type)
                mime_type = export_mime_type if export_mime_type else mime_type
            else:
                logger.info(f"Downloading file content for file_id={file_id} with mime_type={mime_type}")
                content = self._download_file_content(file_id, mime_type)

                logger.info(f"Downloaded content for file_id={file_id}, size={len(content) if content else 0}")

            # TODO: create File Upload Service
            # Check if content is binary and save to MEDIA_ROOT if so
            save_path = ''
            if isinstance(content, bytes):
                # Build user-specific directory under MEDIA_ROOT
                user_id = str(self.user.id) if self.user and hasattr(self.user, 'id') else 'unknown'
                media_dir = os.path.join(settings.MEDIA_ROOT, 'google_drive', user_id)
                os.makedirs(media_dir, exist_ok=True)
                # Use file_id and file_name for uniqueness, add extension from mime type
                suffix = self._get_suffix_from_mime(mime_type)
                safe_file_name = f"{file_id}_{file_name}{suffix}"
                save_path = os.path.join(media_dir, safe_file_name)
                with open(save_path, 'wb') as f:
                    f.write(content)
                logger.info(f"Saved binary file to {save_path}")

            return {
                'title': file_name,
                'filename': file_name,
                'file_path':  save_path,  # You can optionally return save_path here
                'file_size': int(file.get('size', 0)),
                'mime_type': mime_type,
                'content': content,  # This is now bytes!
                'metadata': {
                    'file_id': file_id,
                    'modified_time': file.get('modifiedTime', ''),
                    'source': 'google_drive',
                    'folder_path': parent_path
                }
            }
        except Exception as e:
            logger.error(f"Error getting file data: {e}")
            return None
    
    def _download_file_content(self, file_id: str, mime_type: str) -> Optional[bytes]:
        """Download file content from Google Drive"""
        try:
            # Handle Google Workspace files
            if mime_type.startswith('application/vnd.google-apps'):
                export_mime_type = self._get_export_mime_type(mime_type)
                if export_mime_type:
                    request = self.service.files().export_media(
                        fileId=file_id,
                        mimeType=export_mime_type
                    )
                else:
                    return None
            else:
                request = self.service.files().get_media(fileId=file_id)
            

            content = request.execute()        
             
            # Try to decode as text
            try:
                decoded_content = content.decode('utf-8')
                logger.info(f"Successfully decoded file content for file_id={file_id} as UTF-8 text.")
                return decoded_content
            except Exception as decode_err:
                logger.info(f"Could not decode file content for file_id={file_id} as UTF-8: {decode_err}. Returning raw bytes.")
                return content
        except Exception as e:
            logger.error(f"Error downloading file content: {e}")
            return None
    
    def _get_export_mime_type(self, google_mime_type: str) -> Optional[str]:
        """Get export MIME type for Google Workspace files"""
        export_types = {
            'application/vnd.google-apps.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.google-apps.drawing': 'image/png',
        }
        return export_types.get(google_mime_type)


class WebScrapingDataSource(BaseDataSource):
    """Data source for web scraping"""
    
    def authenticate(self) -> bool:
        """No authentication needed for web scraping"""
        return True
    
    def upload(self, files: List[Dict[str, Any]]) -> List[Document]:
        """Uploading is not supported for WebScrapingDataSource."""
        raise NotImplementedError("Upload is not supported for WebScrapingDataSource.")
    
    def sync(self) -> Dict[str, Any]:
        """Sync web pages"""
        try:
            processed_count = 0
            
            for page_data in self.get_documents():
                document = self.process_document(page_data)
                if document:
                    processed_count += 1
            
            return {
                'status': 'success',
                'processed_count': processed_count
            }
            
        except Exception as e:
            logger.error(f"Error syncing web pages: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_documents(self) -> Iterator[Dict[str, Any]]:
        """Get web pages"""
        urls = self.config.get('urls', [])
        
        for url in urls:
            page_data = self._scrape_page(url)
            if page_data:
                yield page_data
    
    def _scrape_page(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape a single web page"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title = title.get_text() if title else url
            
            # Extract text content
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return {
                'title': title,
                'filename': f"webpage_{hash(url)}.txt",
                'file_path': '',
                'file_size': len(text),
                'mime_type': 'text/html',
                'content': text,
                'metadata': {
                    'url': url,
                    'scraped_at': datetime.now().isoformat(),
                    'source': 'web_scraping'
                }
            }
            
        except Exception as e:
            logger.error(f"Error scraping page {url}: {e}")
            return None
        
        
class GCSDataSource(BaseDataSource):
    """Data source handler for Google Cloud Storage."""

    def __init__(self, data_source: DataSource):
        # Strict validation of DataSource object
        if not data_source:
            raise ValueError("A DataSource object must be provided to GCSDataSource.")
        if not hasattr(data_source, "config") or not isinstance(data_source.config, dict):
            raise ValueError("DataSource.config must be a dict.")
        if not hasattr(data_source, "credentials") or not isinstance(data_source.credentials, dict):
            raise ValueError("DataSource.credentials must be a dict with GCS service account info.")
        if not hasattr(data_source, "user") or not data_source.user:
            raise ValueError("DataSource.user must be set for GCSDataSource.")

        super().__init__(data_source)
        self.bucket_name = getattr(settings, "KNOWLEDGE_BASE_GCS_BUCKET")
        self.client = GCSHandler(
            bucket_name=self.bucket_name,
            credentials_path=getattr(settings, "GCS_CREDENTIALS", None),
        )

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default configuration for GCS data source"""
        return {
            "config": {
                "bucket_name": "user_files",  # Must be set in DataSource config
            },
            "auto_sync": False,  # TODO: figure out how to handle auto-sync for GCS
            "sync_frequency": 10
        }

    def authenticate(self) -> bool:
        try:
            self.client.list_files("", 1)
            return True
        except Exception as e:
            logger.error(f"GCS authentication failed: {str(e)}")
            return False
        
    def get_upload_dir(self) -> str:
        """
        Get the upload directory for the user.
        If not set, return a default path based on user ID.
        """
        if not self.user or not self.user.id:
            raise ValueError("User ID is required to get upload directory")
        
        upload_dir = self.config.get('upload_dir', '')
        
        return upload_dir

    def upload(self, files: List[Dict[str, Any]]) -> List[Document]:
        """
        Upload multiple files for a user, creating a new directory inside the user id directory.
        Each file dict should have 'file_name' and 'file_content' (bytes or str).
        Returns a list of created Document objects.
        """
        user_id = self.user.id if self.user else None
        if not user_id:
            raise ValueError("user_id is required for upload")
        
        if(self.authenticate() is False):
            raise ValueError("GCS authentication failed, cannot upload files")

        # Create a unique directory name under the user directory (e.g., timestamp or uuid)
        from uuid import uuid4
        import time
        dir_name = f"batch_{int(time.time())}_{uuid4().hex[:8]}"
        upload_dir_path = f"{user_id}/{dir_name}"

        created_documents = []
        failed_uploads = []

        for i, file in enumerate(files):
            try:
                file_name = os.path.basename(file['file_name'])

                if not file_name:
                    raise ValueError(f"Invalid file name for file {i}")
                
                file_content = file['file_content']
                path = f"{upload_dir_path}/{file_name}"

                content_to_upload = None

                # If file_content is str, encode to bytes
                if isinstance(file_content, str):
                    content_to_upload = file_content.encode('utf-8')
                elif isinstance(file_content, bytes):
                    content_to_upload = file_content
                else:
                    raise ValueError(f"Unsupported content type for file {file_name}: {type(file_content)}")


                success = self.client.upload_from_string(
                    content=content_to_upload,
                    gcs_file_path=path,
                    content_type='application/octet-stream'
                )

                if success:
                    if self.client.file_exists(path):
                        created_documents.append(file_name)
                    else:
                        logger.error(f"File {file_name} was uploaded but does not exist in GCS after upload.")
                        failed_uploads.append((file_name, "Upload verification failed"))
                else:
                    logger.error(f"Failed to upload file {file_name} to GCS.")
                    failed_uploads.append((file_name, "Upload failed"))

            except Exception as e:
                failed_uploads.append((file.get('file_name', f'file_{i}'), str(e)))
                logger.error(f"Error uploading file {file.get('file_name', f'file_{i}')} to GCS: {e}")
                continue

        if failed_uploads:
            logger.error(f"Failed uploads: {failed_uploads}")

        if not created_documents:
            logger.warning("No files were successfully uploaded to GCS.")
            return []
        
        logger.info(f"Successfully uploaded {len(created_documents)} files to GCS under {upload_dir_path}")

        # Update upload_dir in config and save
        upload_dir = self.config.get('upload_dir', '')
        upload_dir = upload_dir_path
        self.config['upload_dir'] = upload_dir
        self.data_source.config = self.config
        self.data_source.save()

        # Sync to ensure documents are processed
        sync_report = self.sync()
        logger.info(f"GCS upload sync report: {sync_report}")

        return created_documents

    def sync(self) -> Dict[str, Any]:
        """
        Sync all files from the GCS bucket (optionally under a prefix).
        For each file, create a Document if not already present.
        """
        try:
            if not self.authenticate():
                return {'status': 'error', 'error': 'Authentication failed'}

            processed_count = 0
            for doc_data in self.get_documents():
                if not Document.objects.filter(file_path=doc_data['file_path'], user=self.user).exists():
                    document = self.process_document(doc_data)
                    if document:
                        processed_count += 1

            return {
                'status': 'success',
                'processed_count': processed_count
            }
        except Exception as e:
            logger.error(f"Error syncing GCS: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def get_documents(self) -> Iterator[Dict[str, Any]]:
        """
        Yield document dicts for each file in the GCS bucket (optionally under a prefix).
        """
        try:
            prefix = self.get_upload_dir()
            for blob in self.client.yield_blobs(prefix=prefix):
                if blob.size == 0 or blob.name.endswith('/'):
                    continue  # skip folders or empty blobs
                yield self._get_file_data(blob)
        except Exception as e:
            logger.error(f"Error listing GCS documents: {e}")
            return
        
    def _get_file_data(self, blob: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get file data from GCS blob"""
        try:
            file_name = os.path.basename(blob.name)
            mime_type = blob.content_type or 'application/octet-stream'
            content = blob.download_as_bytes()

            save_path = ''
            if isinstance(content, bytes):
                # Build user-specific directory under MEDIA_ROOT
                user_id = str(self.user.id) if self.user and hasattr(self.user, 'id') else 'unknown'
                media_dir = os.path.join(settings.MEDIA_ROOT, 'google_cloud_storage', user_id)
                os.makedirs(media_dir, exist_ok=True)
                save_path = os.path.join(media_dir, file_name)
                with open(save_path, 'wb') as f:
                    f.write(content)
                logger.info(f"Saved binary file to {save_path}")

            return {
                'title': file_name,
                'filename': file_name,
                'file_path': save_path,
                'file_size': blob.size,
                'mime_type': mime_type,
                'content': content,
                'metadata': {
                    'gcs_path': blob.name,
                    'bucket': self.bucket_name,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                    'storage_class': getattr(blob, 'storage_class', None),
                    'source': 'gcs'
                }
            }
        except Exception as e:
            logger.error(f"Error getting file data from GCS: {e}")
            return None

class DataSourceRegistry:
    """Registry for managing data sources"""
    
    def __init__(self):
        self.sources = {}
        self._register_default_sources()
    
    def _register_default_sources(self):
        """Register default data sources"""
        self.sources['file_upload'] = FileUploadDataSource
        self.sources['gmail'] = GmailDataSource
        self.sources['google_drive'] = GoogleDriveDataSource
        self.sources['web_scraping'] = WebScrapingDataSource
        self.sources['gcs'] = GCSDataSource
    
    def register_source(self, source_type: str, source_class: type):
        """Register a new data source"""
        self.sources[source_type] = source_class
    
    def get_source(self, data_source: DataSource) -> Optional[BaseDataSource]:
        """Get data source instance"""
        source_class = self.sources.get(data_source.source_type)
        if source_class:
            return source_class(data_source)
        return None
    
    def get_available_sources(self) -> List[str]:
        """Get list of available data source types"""
        return list(self.sources.keys())
    
    def get_oauth_sources(self) -> List[str]:
        """Get list of OAuth-enabled data source types"""
        oauth_sources = []
        for source_type, source_class in self.sources.items():
            # Check if the source class has OAuth capability
            if hasattr(source_class, 'requires_oauth'):
                # Create a dummy instance to check (you might want to improve this)
                try:
                    dummy_data_source = type('DummyDataSource', (), {
                        'source_type': source_type,
                        'user': None,
                        'config': {},
                        'credentials': {},
                        'save': lambda: None
                    })()
                    instance = source_class(dummy_data_source)
                    if instance.requires_oauth():
                        oauth_sources.append(source_type)
                except:
                    pass
        return oauth_sources
    
    def get_default_config(self, source_type: str) -> dict:
        source_class = self.sources.get(source_type)
        if source_class and hasattr(source_class, 'get_default_config'):
            return source_class.get_default_config()
        return {}


# Global data source registry
data_source_registry = DataSourceRegistry()


# Utility functions for OAuth workflow
def get_oauth_authorization_url(data_source: DataSource) -> Optional[Dict[str, Any]]:
    """Get OAuth authorization URL for a data source"""
    source_instance = data_source_registry.get_source(data_source)
    if source_instance and source_instance.requires_oauth():
        return source_instance.get_oauth_info()
    return None


def handle_oauth_callback(data_source: DataSource, code: str, state: str) -> bool:
    """Handle OAuth callback for a data source"""
    source_instance = data_source_registry.get_source(data_source)
    if source_instance and hasattr(source_instance, 'handle_oauth_callback'):
        return source_instance.handle_oauth_callback(code, state)
    return False


def is_oauth_authenticated(data_source: DataSource) -> bool:
    """Check if a data source is OAuth authenticated"""
    source_instance = data_source_registry.get_source(data_source)
    if source_instance and hasattr(source_instance, 'is_oauth_authenticated'):
        return source_instance.is_oauth_authenticated()
    return False