"""
Helper functions for API responses and business logic
"""
from django.http import JsonResponse
from django.utils import timezone
import logging
import json
import os
from typing import Optional, Dict, Any, Tuple
from .models import BusinessBrand, SocialMediaPost

logger = logging.getLogger(__name__)

def create_json_response(message, data=None, status='success', status_code=200):
    """
    Create a standardized JSON response
    
    Args:
        message (str): Response message
        data (dict, optional): Response data
        status (str): Response status (success/error)
        status_code (int): HTTP status code
    
    Returns:
        JsonResponse: Standardized JSON response
    """
    response_data = {
        'status': status,
        'message': message,
    }
    
    if data is not None:
        response_data['data'] = data
    
    logger.info(f"📤 Creating JSON response - Status: {status_code}, Message: {message}")
    if status_code >= 400:
        logger.warning(f"⚠️  Error response being sent: {response_data}")
    
    return JsonResponse(response_data, status=status_code)

def handle_exception(exception, message="An error occurred"):
    """
    Handle exceptions and return standardized error response
    
    Args:
        exception: The exception that occurred
        message (str): Custom error message
    
    Returns:
        JsonResponse: Error response
    """
    logger.error(f"💥 Exception handled - {message}: {str(exception)}", exc_info=True)
    return create_json_response(
        message=message,
        status='error',
        status_code=500
    )


# Business Profile Helper Functions

def get_business_profile_for_user(user, allow_none: bool = False) -> Optional[BusinessBrand]:
    """
    Get business profile for user with proper error handling.
    
    Args:
        user: Django user object
        allow_none: Whether to return None if not found (instead of raising error)
    
    Returns:
        BusinessBrand instance or None
    
    Raises:
        BusinessBrand.DoesNotExist: If profile not found and allow_none=False
    """
    try:
        return user.business_brand
    except BusinessBrand.DoesNotExist:
        if allow_none:
            return None
        raise


def get_business_profile_by_business_id(business_id: str) -> Optional[Dict[str, Any]]:
    """
    Get business profile data by business_id for business users.
    
    Args:
        business_id: UUID string of the business
    
    Returns:
        Dictionary with business profile data or None if not found
    """
    try:
        from .business_models import BusinessProfile
        
        # Get the BusinessProfile for this business_id
        business_profile = BusinessProfile.objects.get(business_id=business_id)
        
        # Convert to dictionary format expected by AI generation
        profile_data = {
            'id': str(business_profile.id),
            'business_id': str(business_profile.business_id),
            'company_name': business_profile.business_name,
            'business_name': business_profile.business_name,
            'website_url': business_profile.website_url,
            'instagram_handle': business_profile.instagram_handle,
            'logo_url': business_profile.logo_url,
            'primary_color': business_profile.primary_color,
            'secondary_color': business_profile.secondary_color,
            'accent_color': business_profile.accent_color,
            'font_family': business_profile.font_family,
            'brand_mission': business_profile.brand_mission,
            'brand_values': business_profile.brand_values,
            'business_basic_details': business_profile.business_basic_details,
            'business_services': business_profile.business_services,
            'business_additional_details': business_profile.business_additional_details,
        }
        
        logger.info(f"[Business Profile] Retrieved profile for business {business_id}: {profile_data['company_name']}, font: {profile_data['font_family']}")
        return profile_data
        
    except Exception as e:
        logger.error(f"[Business Profile] Failed to get profile for business {business_id}: {str(e)}")
        return None


def create_mock_business_profile(provided_data: Dict[str, Any]):
    """
    Create a mock business profile object from provided data.
    
    Args:
        provided_data: Dictionary containing business profile data
    
    Returns:
        MockBusinessProfile instance
    """
    class MockBusinessProfile:
        def __init__(self, data):
            self.company_name = data.get('company_name', '')
            self.industry = data.get('industry', '')
            self.brand_voice = data.get('brand_voice', '')
            self.target_audience = data.get('target_audience', '')
            self.primary_color = data.get('primary_color', '')
            self.secondary_color = data.get('secondary_color', '')
            # Get font_family, with fallback to brandGuidelines.fontFamily
            font_family = data.get('font_family', '')
            if not font_family and isinstance(data.get('brandGuidelines'), dict):
                font_family = data.get('brandGuidelines', {}).get('fontFamily', '')
            
            self.font_family = font_family or 'Roboto'  # Default fallback
            
            # Log font family for debugging
            logger.info(f"[Business Profile] Font family set to: {self.font_family} (from font_family: {data.get('font_family')}, brandGuidelines: {data.get('brandGuidelines', {}).get('fontFamily', 'N/A') if isinstance(data.get('brandGuidelines'), dict) else 'N/A'})")
            self.logo_url = data.get('logo_url', '')
            # business_description is used by LayoutGeneratorService
            # Use brand_voice or industry as fallback if not provided
            self.business_description = data.get('business_description', 
                data.get('brand_voice', f"{data.get('company_name', '')} - {data.get('industry', '')}"))
            
            # Add design components support
            self.design_components = data.get('designComponents', {})
    
    return MockBusinessProfile(provided_data)


def get_business_profile_for_generation(user, provided_business_profile: Optional[Dict[str, Any]] = None):
    """
    Get business profile for AI generation (either provided mock or user's actual profile).
    
    Args:
        user: Django user object
        provided_business_profile: Optional mock business profile data
    
    Returns:
        Tuple of (business_profile_for_generation, db_business_profile_for_record)
    
    Raises:
        ValueError: If no business profile is available
    """
    business_profile = None
    
    # Use provided business profile first if available (PRIORITY: mock profile over DB)
    if provided_business_profile:
        business_profile = create_mock_business_profile(provided_business_profile)
        logger.info(f"[Business Profile] Using provided mock business profile: {business_profile.company_name}, font: {business_profile.font_family}")
    
    # Get user's business brand for database record (required by foreign key)
    # If using mock profile, we still need a DB profile for the foreign key, but we'll use mock for generation
    try:
        db_business_profile = user.business_brand
    except BusinessBrand.DoesNotExist:
        # If no DB profile exists but we have a mock profile, create a minimal one for the foreign key
        if business_profile:
            logger.warning(f"[Business Profile] No DB profile found, but using mock profile. Creating minimal DB profile for foreign key.")
            # Create a minimal business brand for the foreign key requirement
            db_business_profile = BusinessBrand.objects.create(
                user=user,
                company_name=business_profile.company_name or "Temporary",
                font_family=business_profile.font_family or "Roboto",
                primary_color=business_profile.primary_color or "#3b82f6",
                secondary_color=business_profile.secondary_color or "#10b981"
            )
        else:
            raise ValueError("Business profile not found. Please create a business profile first.")
    
    # If no provided profile, use user's business brand for generation too
    if not business_profile:
        business_profile = db_business_profile
        logger.info(f"[Business Profile] Using database business profile: {business_profile.company_name}, font: {business_profile.font_family}")
    
    return business_profile, db_business_profile


def upload_and_manage_logo(company_logo, user_id: int, old_logo_url: Optional[str] = None) -> Optional[str]:
    """
    Upload company logo and manage old logo deletion.
    
    Args:
        company_logo: File object to upload
        user_id: User ID for file organization
        old_logo_url: URL of old logo to delete (optional)
    
    Returns:
        New logo URL or None if upload failed
    """
    if not company_logo:
        return None
    
    try:
        from services.s3_service import s3_service
        
        logo_url = s3_service.upload_business_logo(company_logo, user_id)
        if not logo_url:
            return None
        
        # Delete old logo if provided and different from new one
        if old_logo_url and old_logo_url != logo_url:
            try:
                s3_service.delete_file(old_logo_url)
            except Exception as e:
                logger.warning(f"Failed to delete old logo {old_logo_url}: {str(e)}")
        
        return logo_url
        
    except Exception as e:
        logger.error(f"Exception during logo upload for user {user_id}: {str(e)}", exc_info=True)
        return None


def refresh_logo_signed_url(user) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Refresh the signed URL for user's business logo.
    
    Args:
        user: Django user object
    
    Returns:
        Tuple of (success, new_url, error_message)
    """
    try:
        business_brand = get_business_profile_for_user(user)
    except BusinessBrand.DoesNotExist:
        return False, None, "No business profile found"
    
    if not business_brand.logo_url:
        return False, None, "No logo found"
    
    try:
        from services.s3_service import s3_service
        
        s3_key = s3_service._extract_key_from_url(business_brand.logo_url)
        if not s3_key:
            return False, None, "Invalid logo URL"
        
        new_signed_url = s3_service.generate_signed_url(s3_key)
        if not new_signed_url:
            return False, None, "Failed to refresh logo URL"
        
        business_brand.logo_url = new_signed_url
        business_brand.save()
        
        return True, new_signed_url, None
        
    except Exception as e:
        logger.error(f"Error refreshing logo URL for user {user.id}: {str(e)}", exc_info=True)
        return False, None, str(e)


# Social Media Helper Functions

def create_social_media_post_record(user, conversation, business_profile, user_input: str, business_id: Optional[str] = None, post_type: str = 'single') -> SocialMediaPost:
    """
    Create a social media post database record.
    
    Args:
        user: Django user object (None for business users)
        conversation: Conversation object (can be None)
        business_profile: BusinessBrand object for the database record (can be None for business users)
        user_input: User's input text
        business_id: Business ID for business users (None for admin users)
        post_type: Type of post ('single' or 'carousel')
    
    Returns:
        SocialMediaPost instance
    """
    return SocialMediaPost.objects.create(
        user=user,
        business_id=business_id,
        conversation=conversation,
        business_profile=business_profile,
        user_input=user_input,
        status='generating',
        post_type=post_type,
        image_prompt='',  # Will be filled by AI
        caption='',  # Will be filled by AI
        hashtags='',  # Will be filled by AI
        carousel_layouts=[]  # Will be filled by AI for carousel posts
    )


def generate_caption_and_hashtags(user_input: str, business_profile) -> Tuple[str, str]:
    """
    Generate caption and hashtags using OpenAI.
    
    Args:
        user_input: User's request
        business_profile: Business profile object (real or mock)
    
    Returns:
        Tuple of (caption, hashtags)
    """
    try:
        import openai
        
        caption_prompt = f"""
Based on the user request "{user_input}" and the business context, create an engaging Instagram caption.

Business Context:
- Company: {business_profile.company_name}
- Industry: {business_profile.industry}
- Brand Voice: {business_profile.brand_voice}
- Target Audience: {business_profile.target_audience}

Please provide:
1. An engaging caption (2-3 sentences, matches brand voice) - DO NOT include hashtags in the caption text
2. 5-10 relevant hashtags (mix of popular and niche) - Keep these completely separate from the caption

IMPORTANT: The caption should be clean text without any hashtags. Hashtags should only appear in the separate hashtags section.

Format your response as:
Caption: [Your caption here - no hashtags]
Hashtags: [Your hashtags here]
"""
        
        # Create OpenAI client for caption generation
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        caption_response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using cheaper model for caption generation
            messages=[
                {"role": "system", "content": "You are an expert social media content creator. Create engaging Instagram captions and hashtags that match the brand voice and target audience."},
                {"role": "user", "content": caption_prompt}
            ],
            max_tokens=300,
            temperature=0.7,
        )
        
        caption_content = caption_response.choices[0].message.content.strip()
        
        # Parse caption and hashtags
        lines = caption_content.split('\n')
        caption = ''
        hashtags = ''
        
        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith('Caption:'):
                current_section = 'caption'
                caption = line.replace('Caption:', '').strip()
            elif line.startswith('Hashtags:'):
                current_section = 'hashtags'
                hashtags = line.replace('Hashtags:', '').strip()
            elif current_section and line:
                if current_section == 'caption':
                    caption += ' ' + line
                elif current_section == 'hashtags':
                    hashtags += ' ' + line
        
        # Fallbacks if parsing failed
        caption = caption or f"Check out our latest update! {user_input}"
        hashtags = hashtags or "#business #update #socialmedia"
        
        return caption, hashtags
        
    except Exception as e:
        logger.error(f"Error generating caption and hashtags: {str(e)}")
        # Return fallback values
        return f"Check out our latest update! {user_input}", "#business #update #socialmedia"


def get_conversation_if_exists(conversation_id: Optional[str], user):
    """
    Get conversation object if ID is provided and exists.
    
    Args:
        conversation_id: Optional conversation ID
        user: Django user object
    
    Returns:
        Conversation object or None
    """
    if not conversation_id:
        return None
    
    try:
        from knowledge_base.models import Conversation
        return Conversation.objects.get(id=conversation_id, user=user)
    except Conversation.DoesNotExist:
        return None


# Instagram Helper Functions

def initialize_instagram_client(user):
    """
    Initialize Instagram API client for user.
    
    Args:
        user: Django user object
    
    Returns:
        Tuple of (success, client_or_error_message, connected_account)
    """
    try:
        from knowledge_base.models import ConnectedAccount
        from knowledge_base.instagram_utils.instagram_api import InstagramAPIClient
        from knowledge_base.instagram_utils.encryption import token_encryption
        
        # Get user's Instagram connected account
        try:
            connected_account = ConnectedAccount.objects.get(
                user=user, 
                platform='instagram', 
                is_active=True
            )
        except ConnectedAccount.DoesNotExist:
            return False, "No active Instagram account connected", None
        
        # Check if token is still valid
        if connected_account.token_expires_at and connected_account.token_expires_at < timezone.now():
            return False, "Instagram access token has expired. Please reconnect your account.", None
        
        # Decrypt the access token
        try:
            decrypted_token = token_encryption.decrypt_token(connected_account.access_token)
            logger.info("Successfully decrypted Instagram access token")
        except Exception as e:
            logger.error(f"Failed to decrypt Instagram access token: {str(e)}")
            return False, "Failed to decrypt Instagram access token. Please reconnect your account.", None
        
        # Initialize Instagram API client with decrypted token
        client = InstagramAPIClient(decrypted_token)
        
        # Validate token
        logger.info("🔍 Validating Instagram access token...")
        if not client.validate_token():
            logger.warning(f"❌ Instagram token validation failed for user {user.id}")
            return False, "Instagram access token is invalid. Please reconnect your account.", None
        
        logger.info("✅ Instagram access token is valid")
        return True, client, connected_account
        
    except Exception as e:
        logger.error(f"Error initializing Instagram client: {str(e)}", exc_info=True)
        return False, str(e), None


def determine_media_type(media_file) -> Optional[str]:
    """
    Determine media type from file extension.
    
    Args:
        media_file: Uploaded file object
    
    Returns:
        'image', 'video', or None if unsupported
    """
    if not media_file or not hasattr(media_file, 'name'):
        return None
    
    from services.s3_service import s3_service
    file_extension = s3_service._get_file_extension(media_file.name).lower()
    
    if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
        return 'image'
    elif file_extension in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
        return 'video'
    else:
        return None
