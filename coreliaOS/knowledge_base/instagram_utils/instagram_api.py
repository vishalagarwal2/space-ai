# knowledge_base/utils/instagram_api.py

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from django.conf import settings

logger = logging.getLogger(__name__)


class InstagramAPIClient:
    """Client for Instagram Graph API interactions"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://graph.facebook.com/v20.0"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        })
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get Instagram user information using Instagram Business Login API"""
        try:
            # Use Instagram Business Login API endpoint with fields parameter
            # to get username and profile picture
            params = {
                'fields': 'id,username,name,profile_picture_url'
            }
            response = self.session.get("https://graph.instagram.com/me", params=params)
            response.raise_for_status()
            
            user_data = response.json()
            logger.info(f"📋 Instagram user info response: {user_data}")
            
            return user_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting Instagram user info: {str(e)}")
            raise
    
    def get_user_media(self, limit: int = 25) -> Dict[str, Any]:
        """Get user's media posts"""
        try:
            params = {'limit': limit}
            response = self.session.get(f"{self.base_url}/me/media", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting Instagram user media: {str(e)}")
            raise
    
    def create_media_container(self, image_url: str, caption: str, media_type: str = "IMAGE") -> Dict[str, Any]:
        """Create a media container for posting using Instagram Graph API"""
        try:
            data = {
                'image_url': image_url,
                'caption': caption,
                'media_type': media_type
            }
            # Use Instagram Graph API endpoint for media container creation
            response = self.session.post("https://graph.instagram.com/me/media", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating Instagram media container: {str(e)}")
            raise
    
    def create_story_container(self, image_url: str, media_type: str = "IMAGE") -> Dict[str, Any]:
        """Create a media container for Instagram Stories"""
        try:
            data = {
                'image_url': image_url,
                'media_type': media_type
            }
            response = self.session.post(f"{self.base_url}/me/media", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating Instagram story container: {str(e)}")
            raise
    
    def publish_media(self, container_id: str) -> Dict[str, Any]:
        """Publish the media container using Instagram Graph API"""
        try:
            data = {'creation_id': container_id}
            # Use Instagram Graph API endpoint for media publishing
            response = self.session.post("https://graph.instagram.com/me/media_publish", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error publishing Instagram media: {str(e)}")
            raise
    
    def get_media_insights(self, media_id: str) -> Dict[str, Any]:
        """Get insights for a specific media post"""
        try:
            params = {
                'metric': 'impressions,reach,likes,comments,shares,saved'
            }
            response = self.session.get(f"{self.base_url}/{media_id}/insights", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting Instagram media insights: {str(e)}")
            raise
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh expired access token"""
        try:
            data = {
                'grant_type': 'fb_exchange_token',
                'client_id': getattr(settings, 'APP_ID', ''),
                'client_secret': getattr(settings, 'INSTAGRAM_APP_SECRET', ''),
                'fb_exchange_token': refresh_token
            }
            response = requests.post(f"{self.base_url}/oauth/access_token", data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing Instagram access token: {str(e)}")
            raise
    
    def validate_token(self) -> bool:
        """Validate if the access token is still valid"""
        try:
            # Use Instagram Graph API endpoint for validation
            response = self.session.get("https://graph.instagram.com/me?fields=id,username")
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_long_lived_token(self, short_lived_token: str) -> Dict[str, Any]:
        """Exchange short-lived token for long-lived token"""
        try:
            data = {
                'grant_type': 'ig_exchange_token',
                'client_secret': getattr(settings, 'INSTAGRAM_APP_SECRET', ''),
                'access_token': short_lived_token
            }
            response = requests.post(f"{self.base_url}/access_token", data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting long-lived Instagram token: {str(e)}")
            raise


class InstagramOAuth:
    """Handle Instagram Graph API OAuth flow"""
    
    def __init__(self):
        self.app_id = getattr(settings, 'INSTAGRAM_APP_ID', '')
        self.app_secret = getattr(settings, 'INSTAGRAM_APP_SECRET', '')
        self.redirect_uri = getattr(settings, 'INSTAGRAM_REDIRECT_URI', '')
        # Instagram Graph API permissions for posting on behalf of users
        # Updated for Instagram Graph API v20.0 (2024)
        self.scopes = [
            'instagram_basic',
            'instagram_content_publish',
            'pages_show_list',
            'pages_read_engagement',
            'pages_manage_posts',
            'business_management',
            'instagram_manage_insights'
        ]
    
    def get_authorization_url(self, state: str = None) -> str:
        """Generate Instagram Graph API OAuth authorization URL"""
        # Validate required credentials
        if not self.app_id:
            raise ValueError("Instagram App ID (INSTAGRAM_APP_ID) is not configured")
        if not self.app_secret:
            raise ValueError("Instagram App Secret (INSTAGRAM_APP_SECRET) is not configured")
        if not self.redirect_uri:
            raise ValueError("Instagram redirect URI (INSTAGRAM_REDIRECT_URI) is not configured")
        
        # Use the correct Instagram Business Login scopes
        business_scopes = [
            'instagram_business_basic',
            'instagram_business_content_publish',
            'instagram_business_manage_messages',
            'instagram_business_manage_comments'
        ]
        
        params = {
            'client_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'scope': ','.join(business_scopes),
            'response_type': 'code'
        }
        
        if state:
            params['state'] = state
        
        # Use the correct Instagram Business Login authorization URL
        base_url = "https://www.instagram.com/oauth/authorize"
        query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
        final_url = f"{base_url}?{query_string}"
        
        
        return final_url
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token using Instagram Business Login API"""
        try:
            data = {
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri,
                'code': code
            }
            
            logger.info(f"🔄 Exchanging Instagram code for token:")
            logger.info(f"  - Client ID: {self.app_id}")
            logger.info(f"  - Redirect URI: {self.redirect_uri}")
            logger.info(f"  - Code: {code[:20]}...")
            
            # Use the correct Instagram Business Login endpoint
            response = requests.post("https://api.instagram.com/oauth/access_token", data=data)
            
            logger.info(f"📡 Instagram token exchange response:")
            logger.info(f"  - Status: {response.status_code}")
            logger.info(f"  - Response: {response.text}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error exchanging Instagram code for token: {str(e)}")
            logger.error(f"Response content: {e.response.text if hasattr(e, 'response') else 'No response'}")
            raise
    
    def get_long_lived_token(self, short_lived_token: str) -> Dict[str, Any]:
        """Exchange short-lived token for long-lived token using Instagram Business Login API"""
        try:
            data = {
                'grant_type': 'ig_exchange_token',
                'client_secret': self.app_secret,
                'access_token': short_lived_token
            }
            
            logger.info(f"🔄 Exchanging short-lived token for long-lived token:")
            logger.info(f"  - Short token: {short_lived_token[:20]}...")
            
            # Use the correct Instagram Business Login endpoint for long-lived tokens
            response = requests.get("https://graph.instagram.com/access_token", params=data)
            
            logger.info(f"📡 Instagram long-lived token response:")
            logger.info(f"  - Status: {response.status_code}")
            logger.info(f"  - Response: {response.text}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting long-lived Instagram token: {str(e)}")
            logger.error(f"Response content: {e.response.text if hasattr(e, 'response') else 'No response'}")
            raise


def create_instagram_post(access_token: str, image_url: str, caption: str, post_type: str = "POST") -> Dict[str, Any]:
    """Helper function to create and publish an Instagram post or story"""
    try:
        client = InstagramAPIClient(access_token)
        
        if post_type.upper() == "STORY":
            # Create story container (no caption for stories)
            container_response = client.create_story_container(image_url)
        else:
            # Create regular post container
            container_response = client.create_media_container(image_url, caption)
        
        container_id = container_response.get('id')
        
        if not container_id:
            raise ValueError("Failed to create media container")
        
        # Publish the media
        publish_response = client.publish_media(container_id)
        
        return {
            'success': True,
            'post_id': publish_response.get('id'),
            'container_id': container_id,
            'post_type': post_type.upper(),
            'response': publish_response
        }
    except Exception as e:
        logger.error(f"Error creating Instagram {post_type.lower()}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
