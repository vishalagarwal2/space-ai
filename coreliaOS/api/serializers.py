"""
Serializers for API data transformation
"""
from django.contrib.auth.models import User

class BusinessBrandSerializer:
    """
    Serializer for BusinessBrand model
    """
    
    @staticmethod
    def to_dict(business_brand):
        """
        Convert BusinessBrand instance to dictionary
        
        Args:
            business_brand: BusinessBrand instance
        
        Returns:
            dict: Serialized business brand data
        """
        return {
            'id': business_brand.id,
            'company_name': business_brand.company_name,
            'logo_url': business_brand.logo_url,
            'primary_color': business_brand.primary_color,
            'secondary_color': business_brand.secondary_color,
            'font_family': business_brand.font_family,
            'brand_voice': business_brand.brand_voice,
            'industry': business_brand.industry,
            'target_audience': business_brand.target_audience,
            'business_description': business_brand.business_description,
            'created_at': business_brand.created_at.isoformat() if business_brand.created_at else None,
            'updated_at': business_brand.updated_at.isoformat() if business_brand.updated_at else None,
        }


class ContentCalendarSerializer:
    """
    Serializer for ContentCalendar model
    """
    
    @staticmethod
    def to_dict(content_calendar):
        """
        Convert ContentCalendar instance to dictionary
        
        Args:
            content_calendar: ContentCalendar instance
        
        Returns:
            dict: Serialized content calendar data
        """
        return {
            'id': str(content_calendar.id),
            'user': str(content_calendar.user.id) if content_calendar.user else None,
            'business_id': str(content_calendar.business_id) if content_calendar.business_id else None,
            'owner_type': 'admin' if content_calendar.user else 'business',
            'business_profile_id': content_calendar.business_profile_id,
            'title': content_calendar.title,
            'month': content_calendar.month,
            'year': content_calendar.year,
            'business_profile_data': content_calendar.business_profile_data,
            'generation_prompt': content_calendar.generation_prompt,
            'created_at': content_calendar.created_at.isoformat() if content_calendar.created_at else None,
            'updated_at': content_calendar.updated_at.isoformat() if content_calendar.updated_at else None,
        }


class ContentIdeaSerializer:
    """
    Serializer for ContentIdea model
    """
    
    @staticmethod
    def to_dict(content_idea):
        """
        Convert ContentIdea instance to dictionary
        
        Args:
            content_idea: ContentIdea instance
        
        Returns:
            dict: Serialized content idea data
        """
        return {
            'id': str(content_idea.id),
            'content_calendar': str(content_idea.content_calendar.id),
            'title': content_idea.title,
            'description': content_idea.description,
            'content_type': content_idea.content_type,
            'post_format': content_idea.post_format,  # 'single' or 'carousel'
            'generation_prompt': content_idea.generation_prompt,
            'scheduled_date': content_idea.scheduled_date.isoformat() if content_idea.scheduled_date else None,
            'scheduled_time': content_idea.scheduled_time.isoformat() if content_idea.scheduled_time else None,
            'status': content_idea.status,
            'generated_post_data': SocialMediaPostSerializer.to_dict(content_idea.generated_post) if content_idea.generated_post else None,
            'published_post_id': content_idea.published_post_id,
            'selected_template': content_idea.selected_template,
            'user_notes': content_idea.user_notes,
            'media_urls': content_idea.media_urls,
            'created_at': content_idea.created_at.isoformat() if content_idea.created_at else None,
            'updated_at': content_idea.updated_at.isoformat() if content_idea.updated_at else None,
            'approved_at': content_idea.approved_at.isoformat() if content_idea.approved_at else None,
            'published_at': content_idea.published_at.isoformat() if content_idea.published_at else None,
        }


class SocialMediaPostSerializer:
    """
    Serializer for SocialMediaPost model
    """
    
    @staticmethod
    def _get_business_profile_data(social_media_post):
        """
        Get business profile data for both admin and business users.
        
        Args:
            social_media_post: SocialMediaPost instance
            
        Returns:
            dict: Business profile data or None
        """
        if social_media_post.business_profile:
            # Admin user: has BusinessBrand profile
            return {
                'company_name': social_media_post.business_profile.company_name,
                'industry': social_media_post.business_profile.industry,
                'brand_voice': social_media_post.business_profile.brand_voice,
                'primary_color': social_media_post.business_profile.primary_color,
                'secondary_color': social_media_post.business_profile.secondary_color,
                'font_family': social_media_post.business_profile.font_family,
                'logo_url': social_media_post.business_profile.logo_url,
            }
        elif social_media_post.business_id:
            # Business user: get BusinessProfile by business_id
            try:
                from .helpers import get_business_profile_by_business_id
                business_profile_data = get_business_profile_by_business_id(social_media_post.business_id)
                if business_profile_data:
                    return {
                        'company_name': business_profile_data.get('company_name'),
                        'industry': business_profile_data.get('industry', ''),
                        'brand_voice': business_profile_data.get('brand_mission', ''),  # Use brand_mission as brand_voice
                        'primary_color': business_profile_data.get('primary_color'),
                        'secondary_color': business_profile_data.get('secondary_color'),
                        'font_family': business_profile_data.get('font_family'),
                        'logo_url': business_profile_data.get('logo_url'),
                    }
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to get business profile for business_id {social_media_post.business_id}: {str(e)}")
        
        return None
    
    @staticmethod
    def to_dict(social_media_post):
        """
        Convert SocialMediaPost instance to dictionary
        
        Args:
            social_media_post: SocialMediaPost instance
        
        Returns:
            dict: Serialized social media post data
        """
        return {
            'id': str(social_media_post.id),
            'post_type': social_media_post.post_type,  # 'single' or 'carousel'
            'image_prompt': social_media_post.image_prompt,
            'layout_json': social_media_post.layout_json,
            'carousel_layouts': social_media_post.carousel_layouts if social_media_post.carousel_layouts else [],  # Array of carousel slide layouts
            'generated_image_url': social_media_post.generated_image_url,
            'caption': social_media_post.caption,
            'hashtags': social_media_post.hashtags,
            'status': social_media_post.status,
            'user_input': social_media_post.user_input,
            'instagram_post_id': social_media_post.instagram_post_id,
            'connected_account_id': str(social_media_post.connected_account.id) if social_media_post.connected_account else None,
            'business_profile': SocialMediaPostSerializer._get_business_profile_data(social_media_post),
            'business_id': str(social_media_post.business_id) if social_media_post.business_id else None,
            'created_at': social_media_post.created_at.isoformat(),
            'updated_at': social_media_post.updated_at.isoformat(),
        }


class InstagramPostSerializer:
    """
    Serializer for InstagramPost model
    """
    
    @staticmethod
    def to_dict(instagram_post):
        """
        Convert InstagramPost instance to dictionary
        
        Args:
            instagram_post: InstagramPost instance
        
        Returns:
            dict: Serialized Instagram post data
        """
        return {
            'id': instagram_post.id,
            'caption': instagram_post.caption,
            'media_url': instagram_post.media_url,
            'media_type': instagram_post.media_type,
            'status': instagram_post.status,
            'instagram_post_id': instagram_post.instagram_post_id,
            'scheduled_at': instagram_post.scheduled_at.isoformat() if instagram_post.scheduled_at else None,
            'posted_at': instagram_post.posted_at.isoformat() if instagram_post.posted_at else None,
            'created_at': instagram_post.created_at.isoformat() if instagram_post.created_at else None,
            'updated_at': instagram_post.updated_at.isoformat() if instagram_post.updated_at else None,
        }
