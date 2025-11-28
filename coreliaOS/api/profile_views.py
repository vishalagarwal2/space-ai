"""
Refactored business profile management views with improved modularity
"""
import json
import logging
from coreliaOS.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .helpers import create_json_response, handle_exception
from .services import BusinessProfileService, SocialMediaPostService, InstagramService

logger = logging.getLogger(__name__)


@login_required
@csrf_exempt
@require_http_methods(["GET"])
def get_company_profile_api(request):
    """Get user's business profile with fresh signed URLs"""
    return BusinessProfileService.get_profile_with_fresh_urls(request.user)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_company_profile_api(request):
    """Create or update user's business profile"""
    profile_data = {
        'company_name': request.POST.get('company_name'),
        'primary_color': request.POST.get('primary_color', '#3b82f6'),
        'secondary_color': request.POST.get('secondary_color', '#10b981'),
        'font_family': request.POST.get('font_family', 'Roboto'),
        'brand_voice': request.POST.get('brand_voice', ''),
        'industry': request.POST.get('industry', ''),
        'target_audience': request.POST.get('target_audience', ''),
        'business_description': request.POST.get('business_description', ''),
    }
    
    company_logo = request.FILES.get('company_logo')
    
    return BusinessProfileService.create_or_update_profile(
        request.user, profile_data, company_logo
    )


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def refresh_logo_url_api(request):
    """Manual refresh API for signed URL"""
    return BusinessProfileService.refresh_logo_url(request.user)


@login_required
@csrf_exempt
@require_http_methods(["GET", "POST"])
def company_profile_api(request):
    """Unified business profile API - handles both GET and POST"""
    if request.method == "GET":
        return get_company_profile_api(request)
    else:
        return create_company_profile_api(request)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_instagram_post_api(request):
    """Create a new Instagram post with media upload"""
    caption = request.POST.get('caption', '')
    media_file = request.FILES.get('media')
    
    return InstagramService.create_post(request.user, caption, media_file)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def generate_social_media_post_api(request):
    """Generate a complete social media post with image and caption"""
    try:
        data = json.loads(request.body)
        
        user_input = data.get('user_input', '')
        conversation_id = data.get('conversation_id')
        provided_business_profile = data.get('business_profile')
        
        logger.info(f"📥 [API] Received generate post request - User: {request.user.id}, Input: {user_input[:100] if user_input else 'None'}...")
        if provided_business_profile:
            logger.info(f"📥 [API] Provided business profile: company={provided_business_profile.get('company_name')}, font_family={provided_business_profile.get('font_family')}, brandGuidelines.fontFamily={provided_business_profile.get('brandGuidelines', {}).get('fontFamily') if isinstance(provided_business_profile.get('brandGuidelines'), dict) else 'N/A'}")
        else:
            logger.info(f"📥 [API] No business profile provided, will use database profile")
        
        response = SocialMediaPostService.generate_post(
            request.user, user_input, conversation_id, provided_business_profile
        )
        
        # Log response status
        if hasattr(response, 'content'):
            try:
                response_data = json.loads(response.content)
                logger.info(f"📤 [API] Response status: {response_data.get('status')}, Has data: {bool(response_data.get('data'))}")
                if response_data.get('data'):
                    logger.info(f"📤 [API] Post ID: {response_data.get('data', {}).get('id')}, Has layout_json: {bool(response_data.get('data', {}).get('layout_json'))}")
            except:
                pass
        
        return response
        
    except json.JSONDecodeError:
        logger.error("❌ [API] Invalid JSON in request body")
        return create_json_response(
            "Invalid JSON in request body",
            status='error',
            status_code=400
        )
    except Exception as e:
        logger.error(f"❌ [API] Error generating post: {str(e)}", exc_info=True)
        return handle_exception(e, "Failed to generate social media post")


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def refine_social_media_post_api(request):
    """Refine an existing social media post"""
    try:
        data = json.loads(request.body)
        
        post_id = data.get('post_id')
        refinements = data.get('refinements', {})
        
        return SocialMediaPostService.refine_post(request.user, post_id, refinements)
        
    except json.JSONDecodeError:
        return create_json_response(
            "Invalid JSON in request body",
            status='error',
            status_code=400
        )
    except Exception as e:
        return handle_exception(e, "Failed to refine social media post")


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def publish_social_media_post_api(request):
    """Publish a social media post to Instagram"""
    try:
        data = json.loads(request.body)
        
        post_id = data.get('post_id')
        connected_account_id = data.get('connected_account_id')
        publish_immediately = data.get('publish_immediately', True)
        
        logger.info(f"📥 [PUBLISH API] Received publish request - User: {request.user.id}")
        logger.info(f"📥 [PUBLISH API] Post ID: {post_id}, Account ID: {connected_account_id}")
        
        response = InstagramService.publish_social_media_post(
            request.user, post_id, connected_account_id, publish_immediately
        )
        
        # Log response
        if hasattr(response, 'content'):
            try:
                response_data = json.loads(response.content)
                logger.info(f"📤 [PUBLISH API] Response status: {response_data.get('status')}")
                if response_data.get('data'):
                    logger.info(f"📤 [PUBLISH API] Post status: {response_data.get('data', {}).get('status')}")
                    logger.info(f"📤 [PUBLISH API] Instagram post ID: {response_data.get('data', {}).get('instagram_post_id')}")
            except:
                pass
        
        return response
        
    except json.JSONDecodeError:
        logger.error("❌ [PUBLISH API] Invalid JSON in request body")
        return create_json_response(
            "Invalid JSON in request body",
            status='error',
            status_code=400
        )
    except Exception as e:
        logger.error(f"❌ [PUBLISH API] Error: {str(e)}", exc_info=True)
        return handle_exception(e, "Failed to publish social media post")


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def upload_post_image_api(request):
    """Upload an image for a social media post"""
    try:
        post_id = request.POST.get('post_id')
        image_file = request.FILES.get('image')
        
        if not post_id:
            return create_json_response(
                "Post ID is required",
                status='error',
                status_code=400
            )
        
        if not image_file:
            return create_json_response(
                "Image file is required",
                status='error',
                status_code=400
            )
        
        return SocialMediaPostService.upload_post_image(
            request.user, post_id, image_file
        )
        
    except Exception as e:
        return handle_exception(e, "Failed to upload post image")


@csrf_exempt
@require_http_methods(["GET"])
def get_instagram_posts_api(request):
    """Get user's Instagram posts"""
    # Check for business user first
    business_id = request.session.get('business_id')
    user_type = request.session.get('user_type')
    
    if business_id and user_type == 'business':
        # For now, return empty list for business users since we don't have Instagram posts for them yet
        return JsonResponse({
            'status': 'success',
            'message': 'Instagram posts retrieved successfully',
            'data': []
        })
    
    # Check for admin user
    if request.user.is_authenticated:
        return InstagramService.get_user_posts(request.user)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Not authenticated'
    }, status=401)


@csrf_exempt
@require_http_methods(["POST"])
def post_to_instagram_api(request):
    """Post to Instagram"""
    try:
        # Check for business user first
        business_id = request.session.get('business_id')
        user_type = request.session.get('user_type')
        
        if business_id and user_type == 'business':
            # For now, return not implemented for business users
            return JsonResponse({
                'status': 'error',
                'message': 'Instagram posting not yet implemented for business users'
            }, status=501)
        
        # Check for admin user
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'message': 'Not authenticated'
            }, status=401)
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            post_id = data.get('post_id')
        else:
            post_id = request.POST.get('post_id')
        
        # Debug logging
        logger.info(f"Content type: {request.content_type}")
        logger.info(f"Post ID received: {post_id}")
        
        return InstagramService.publish_post(request.user, post_id)
        
    except json.JSONDecodeError:
        return create_json_response(
            "Invalid JSON in request body",
            status='error',
            status_code=400
        )
    except Exception as e:
        return handle_exception(e, "Failed to post to Instagram")
