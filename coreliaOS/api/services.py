"""
Service classes for handling complex business logic
"""
import json
import logging
from typing import Dict, Any, Optional, Tuple
from django.utils import timezone

from .models import BusinessBrand, InstagramPost, SocialMediaPost
from .serializers import BusinessBrandSerializer, InstagramPostSerializer, SocialMediaPostSerializer
from .helpers import (
    create_json_response, handle_exception, get_business_profile_for_user,
    get_business_profile_for_generation, upload_and_manage_logo,
    refresh_logo_signed_url, create_social_media_post_record,
    generate_caption_and_hashtags, get_conversation_if_exists,
    initialize_instagram_client, determine_media_type
)

logger = logging.getLogger(__name__)


class BusinessProfileService:
    """Service for managing business profiles"""
    
    @staticmethod
    def get_profile_with_fresh_urls(user):
        """
        Get business profile with fresh signed URLs for logos.
        
        Args:
            user: Django user object
        
        Returns:
            JsonResponse with profile data or error
        """
        try:
            business_brand = get_business_profile_for_user(user, allow_none=True)
            if not business_brand:
                return create_json_response(
                    "No business profile found",
                    data=None
                )
            
            # Generate fresh signed URL if logo exists and is old
            if business_brand.logo_url:
                from datetime import datetime, timedelta
                should_refresh = (
                    business_brand.updated_at < datetime.now(business_brand.updated_at.tzinfo) - timedelta(hours=1)
                    if business_brand.updated_at else True
                )
                
                if should_refresh:
                    success, new_url, error = refresh_logo_signed_url(user)
                    if success:
                        business_brand.logo_url = new_url
            
            return create_json_response(
                "Business profile retrieved successfully",
                data=BusinessBrandSerializer.to_dict(business_brand)
            )
            
        except Exception as e:
            return handle_exception(e, "Failed to retrieve business profile")
    
    @staticmethod
    def create_or_update_profile(user, profile_data: Dict[str, Any], company_logo=None):
        """
        Create or update business profile.
        
        Args:
            user: Django user object
            profile_data: Dictionary with profile fields
            company_logo: Optional logo file
        
        Returns:
            JsonResponse with created/updated profile or error
        """
        try:
            company_name = profile_data.get('company_name')
            if not company_name:
                return create_json_response(
                    "Company name is required",
                    status='error',
                    status_code=400
                )
            
            # Handle logo upload
            logo_url = None
            old_logo_url = None
            
            # Get existing profile to check for old logo
            existing_brand = get_business_profile_for_user(user, allow_none=True)
            if existing_brand:
                old_logo_url = existing_brand.logo_url
            
            if company_logo:
                logo_url = upload_and_manage_logo(company_logo, user.id, old_logo_url)
                if not logo_url:
                    return create_json_response(
                        "Failed to upload logo. Please try again.",
                        status='error',
                        status_code=400
                    )
            
            # Create or update business brand
            defaults = {
                'company_name': company_name,
                'primary_color': profile_data.get('primary_color', '#3b82f6'),
                'secondary_color': profile_data.get('secondary_color', '#10b981'),
                'font_family': profile_data.get('font_family', 'Roboto'),
                'brand_voice': profile_data.get('brand_voice', ''),
                'industry': profile_data.get('industry', ''),
                'target_audience': profile_data.get('target_audience', ''),
                'business_description': profile_data.get('business_description', ''),
            }
            
            if logo_url:
                defaults['logo_url'] = logo_url
            
            business_brand, created = BusinessBrand.objects.get_or_create(
                user=user,
                defaults=defaults
            )
            
            if not created:
                # Update existing profile
                for key, value in defaults.items():
                    setattr(business_brand, key, value)
                business_brand.save()
            
            response_data = BusinessBrandSerializer.to_dict(business_brand)
            
            return create_json_response(
                "Business profile saved successfully",
                data=response_data,
                status_code=201 if created else 200
            )
            
        except Exception as e:
            logger.error(f"Error saving business profile for user {user.id}: {str(e)}", exc_info=True)
            return handle_exception(e, "Failed to save business profile")
    
    @staticmethod
    def refresh_logo_url(user):
        """
        Refresh the signed URL for user's logo.
        
        Args:
            user: Django user object
        
        Returns:
            JsonResponse with new URL or error
        """
        try:
            success, new_url, error_message = refresh_logo_signed_url(user)
            
            if not success:
                return create_json_response(
                    error_message,
                    status='error',
                    status_code=404 if "not found" in error_message.lower() else 500
                )
            
            return create_json_response(
                "Logo URL refreshed successfully",
                data={'logo_url': new_url}
            )
            
        except Exception as e:
            return handle_exception(e, "Failed to refresh logo URL")


class SocialMediaPostService:
    """Service for managing social media posts"""
    
    @staticmethod
    def generate_post(user, user_input: str, conversation_id: Optional[str] = None, 
                     provided_business_profile: Optional[Dict[str, Any]] = None,
                     business_id: Optional[str] = None, content_idea=None,
                     override_post_format: Optional[str] = None):
        """
        Generate a complete social media post with layout and caption.
        
        Args:
            user: Django user object (None for business users)
            user_input: User's request text
            conversation_id: Optional conversation ID
            provided_business_profile: Optional mock business profile data
            business_id: Optional business ID for business users
            content_type: Optional content type (educational -> carousel, others -> single)
        
        Returns:
            JsonResponse with generated post or error
        """
        try:
            if not user_input:
                return create_json_response(
                    "User input is required",
                    status='error',
                    status_code=400
                )
            
            # Handle business users vs admin users differently
            if business_id:
                # Business user flow - get business profile from database by business_id
                from .helpers import get_business_profile_by_business_id, create_mock_business_profile
                
                # Get the actual business profile from database
                business_profile_data = get_business_profile_by_business_id(business_id)
                if not business_profile_data:
                    return create_json_response(
                        f"Business profile not found for business ID: {business_id}",
                        status='error',
                        status_code=404
                    )
                
                # Create business profile object for AI generation
                business_profile = create_mock_business_profile(business_profile_data)
                db_business_profile = None  # Business users don't need BusinessBrand profile
                conversation = None  # Business users don't have conversations
            else:
                # Admin user flow - get business profiles for generation and database
                try:
                    business_profile, db_business_profile = get_business_profile_for_generation(
                        user, provided_business_profile
                    )
                except ValueError as e:
                    return create_json_response(
                        str(e),
                        status='error',
                        status_code=404
                    )
                
                # Get conversation if provided
                conversation = get_conversation_if_exists(conversation_id, user)
            
            # Determine post type based on content_idea and override
            post_type = 'single'  # default
            if override_post_format:
                post_type = override_post_format
            elif content_idea and hasattr(content_idea, 'post_format'):
                post_type = content_idea.post_format
            elif content_idea and hasattr(content_idea, 'content_type') and content_idea.content_type == 'educational':
                post_type = 'carousel'  # Educational content defaults to carousel
            
            # Create social media post record
            social_media_post = create_social_media_post_record(
                user, conversation, db_business_profile, user_input, business_id, post_type
            )
            
            # Generate JSON layout and caption using AI
            try:
                # Generate JSON layout using the layout generator service
                from services.layout_generator import LayoutGeneratorService
                
                layout_generator = LayoutGeneratorService(business_profile)
                
                # Generate layout based on the determined post type
                layout_json = layout_generator.generate_layout(user_input, include_debug=True, post_format=social_media_post.post_type)
                
                # Store the layout JSON in the post
                if layout_json.get('post_type') == 'carousel':
                    # For carousel posts, store individual slides in carousel_layouts
                    social_media_post.carousel_layouts = layout_json.get('slides', [])
                    social_media_post.layout_json = json.dumps(layout_json.get('slides', [])[0] if layout_json.get('slides') else {})
                    social_media_post.image_prompt = f"Carousel Layout Generated for Instagram post ({len(layout_json.get('slides', []))} slides)"
                else:
                    # For single posts, store as before
                    social_media_post.layout_json = json.dumps(layout_json)
                    social_media_post.image_prompt = "JSON Layout Generated for Instagram post"
                
                # Generate caption and hashtags
                caption, hashtags = generate_caption_and_hashtags(user_input, business_profile)
                
                social_media_post.caption = caption
                social_media_post.hashtags = hashtags
                social_media_post.status = 'ready'
                social_media_post.save()
                
            except Exception as e:
                logger.error(f"Error generating social media post: {str(e)}")
                social_media_post.status = 'failed'
                social_media_post.save()
                raise
            
            response_data = SocialMediaPostSerializer.to_dict(social_media_post)
            
            return create_json_response(
                "Social media post generated successfully",
                data=response_data,
                status_code=201
            )
            
        except Exception as e:
            return handle_exception(e, "Failed to generate social media post")
    
    @staticmethod
    def refine_post(user, post_id: str, refinements: Dict[str, Any]):
        """
        Refine an existing social media post.
        
        Args:
            user: Django user object
            post_id: Post ID to refine
            refinements: Dictionary of refinements to apply
        
        Returns:
            JsonResponse with refined post or error
        """
        try:
            if not post_id:
                return create_json_response(
                    "Post ID is required",
                    status='error',
                    status_code=400
                )
            
            try:
                social_media_post = SocialMediaPost.objects.get(id=post_id, user=user)
            except SocialMediaPost.DoesNotExist:
                return create_json_response(
                    "Social media post not found",
                    status='error',
                    status_code=404
                )
            
            # Update post with refinements
            if 'caption' in refinements:
                social_media_post.caption = refinements['caption']
            
            if 'hashtags' in refinements:
                social_media_post.hashtags = refinements['hashtags']
            
            if 'regenerate_image' in refinements and refinements['regenerate_image']:
                social_media_post.status = 'generating'
                # Here we would regenerate the image
                social_media_post.status = 'ready'
            
            social_media_post.status = 'refining'
            social_media_post.save()
            
            response_data = SocialMediaPostSerializer.to_dict(social_media_post)
            
            return create_json_response(
                "Social media post refined successfully",
                data=response_data
            )
            
        except Exception as e:
            return handle_exception(e, "Failed to refine social media post")


class InstagramService:
    """Service for managing Instagram operations"""
    
    @staticmethod
    def create_post(user, caption: str, media_file):
        """
        Create a new Instagram post with media upload.
        
        Args:
            user: Django user object
            caption: Post caption
            media_file: Media file to upload
        
        Returns:
            JsonResponse with created post or error
        """
        try:
            if not media_file:
                return create_json_response(
                    "Media file is required",
                    status='error',
                    status_code=400
                )
            
            # Determine media type
            media_type = determine_media_type(media_file)
            if not media_type:
                return create_json_response(
                    "Unsupported file type. Please upload an image or video.",
                    status='error',
                    status_code=400
                )
            
            # Upload media
            from services.s3_service import s3_service
            
            if media_type == 'image':
                media_url = s3_service.upload_post_image(media_file, user.id)
            else:  # video
                media_url = s3_service.upload_post_video(media_file, user.id)
            
            if not media_url:
                return create_json_response(
                    "Failed to upload media. Please try again.",
                    status='error',
                    status_code=400
                )
            
            # Create Instagram post record
            instagram_post = InstagramPost.objects.create(
                user=user,
                caption=caption,
                media_url=media_url,
                media_type=media_type,
                status='draft'
            )
            
            response_data = InstagramPostSerializer.to_dict(instagram_post)
            
            return create_json_response(
                "Instagram post created successfully",
                data=response_data,
                status_code=201
            )
            
        except Exception as e:
            logger.error(f"Error creating Instagram post for user {user.id}: {str(e)}", exc_info=True)
            return handle_exception(e, "Failed to create Instagram post")
    
    @staticmethod
    def publish_post(user, post_id: str):
        """
        Publish an Instagram post.
        
        Args:
            user: Django user object
            post_id: Post ID to publish
        
        Returns:
            JsonResponse with published post or error
        """
        try:
            if not post_id:
                return create_json_response(
                    "Post ID is required",
                    status='error',
                    status_code=400
                )
            
            try:
                instagram_post = InstagramPost.objects.get(id=post_id, user=user)
            except InstagramPost.DoesNotExist:
                return create_json_response(
                    "Post not found",
                    status='error',
                    status_code=404
                )
            
            # Initialize Instagram client
            success, client_or_error, connected_account = initialize_instagram_client(user)
            if not success:
                return create_json_response(
                    client_or_error,
                    status='error',
                    status_code=400
                )
            
            client = client_or_error
            
            # Determine media type for Instagram API
            media_type = "IMAGE" if instagram_post.media_type == 'image' else "VIDEO"
            
            # Create media container
            logger.info(f"Creating Instagram media container for post {post_id}")
            container_response = client.create_media_container(
                image_url=instagram_post.media_url,
                caption=instagram_post.caption or "",
                media_type=media_type
            )
            
            container_id = container_response.get('id')
            if not container_id:
                logger.error(f"No container ID in response: {container_response}")
                return create_json_response(
                    "Failed to create Instagram media container",
                    status='error',
                    status_code=500
                )
            
            # Publish the media
            logger.info(f"Publishing Instagram media container {container_id}")
            publish_response = client.publish_media(container_id)
            
            instagram_media_id = publish_response.get('id')
            if not instagram_media_id:
                logger.error(f"No media ID in publish response: {publish_response}")
                return create_json_response(
                    "Failed to publish to Instagram",
                    status='error',
                    status_code=500
                )
            
            # Update post status
            instagram_post.status = 'posted'
            instagram_post.instagram_post_id = instagram_media_id
            instagram_post.posted_at = timezone.now()
            instagram_post.save()
            
            logger.info(f"Successfully posted to Instagram: {instagram_media_id}")
            
            response_data = InstagramPostSerializer.to_dict(instagram_post)
            
            return create_json_response(
                "Post published to Instagram successfully",
                data=response_data
            )
            
        except Exception as e:
            logger.error(f"Error posting to Instagram: {str(e)}", exc_info=True)
            
            # Update post status to failed if we have the post object
            try:
                instagram_post.status = 'failed'
                instagram_post.save()
            except:
                pass
            
            return create_json_response(
                f"Failed to post to Instagram: {str(e)}",
                status='error',
                status_code=500
            )
    
    @staticmethod
    def get_user_posts(user):
        """
        Get user's Instagram posts.
        
        Args:
            user: Django user object
        
        Returns:
            JsonResponse with posts list or error
        """
        try:
            posts = InstagramPost.objects.filter(user=user).order_by('-created_at')
            posts_data = [InstagramPostSerializer.to_dict(post) for post in posts]
            
            return create_json_response(
                "Instagram posts retrieved successfully",
                data=posts_data
            )
            
        except Exception as e:
            logger.error(f"Error retrieving Instagram posts for user {user.id}: {str(e)}", exc_info=True)
            return handle_exception(e, "Failed to retrieve Instagram posts")
    
    @staticmethod
    def publish_social_media_post(user, post_id: str, connected_account_id: str, 
                                 publish_immediately: bool = True):
        """
        Publish a social media post to Instagram.
        
        Args:
            user: Django user object
            post_id: Social media post ID
            connected_account_id: Connected account ID
            publish_immediately: Whether to publish immediately
        
        Returns:
            JsonResponse with published post or error
        """
        try:
            if not post_id or not connected_account_id:
                return create_json_response(
                    "Post ID and connected account ID are required",
                    status='error',
                    status_code=400
                )
            
            try:
                social_media_post = SocialMediaPost.objects.get(id=post_id, user=user)
            except SocialMediaPost.DoesNotExist:
                return create_json_response(
                    "Social media post not found",
                    status='error',
                    status_code=404
                )
            
            try:
                from knowledge_base.models import ConnectedAccount
                connected_account = ConnectedAccount.objects.get(
                    id=connected_account_id, 
                    user=user, 
                    is_active=True
                )
            except ConnectedAccount.DoesNotExist:
                return create_json_response(
                    "Connected account not found or inactive",
                    status='error',
                    status_code=404
                )
            
            if not social_media_post.generated_image_url:
                return create_json_response(
                    "No image available for posting",
                    status='error',
                    status_code=400
                )
            
            # Update post status
            social_media_post.status = 'publishing'
            social_media_post.connected_account = connected_account
            social_media_post.save()
            
            try:
                # For now, simulate success
                # In the future, this would call the actual Instagram posting API
                social_media_post.status = 'published'
                social_media_post.instagram_post_id = f"ig_post_{social_media_post.id}"
                social_media_post.save()
                
                # Update linked ContentIdea status to published if it exists
                try:
                    from .models import ContentIdea
                    content_idea = ContentIdea.objects.filter(generated_post=social_media_post).first()
                    if content_idea:
                        content_idea.mark_published(social_media_post.instagram_post_id)
                        logger.info(f"Updated ContentIdea {content_idea.id} status to published")
                except Exception as e:
                    logger.warning(f"Failed to update ContentIdea status: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error publishing to Instagram: {str(e)}")
                social_media_post.status = 'failed'
                social_media_post.save()
                raise
            
            response_data = SocialMediaPostSerializer.to_dict(social_media_post)
            
            return create_json_response(
                "Social media post published successfully",
                data=response_data
            )
            
        except Exception as e:
            return handle_exception(e, "Failed to publish social media post")
