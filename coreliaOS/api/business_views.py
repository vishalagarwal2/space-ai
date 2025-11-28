from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone
from .business_models import Business, BusinessProfile
import json
import logging
import traceback
from django.conf import settings

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def business_register_api(request):
    """Business user registration API endpoint"""
    try:
        data = json.loads(request.body)
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        password = data.get('password')
        
        # Validation
        if not first_name or not last_name or not email or not password:
            return JsonResponse({
                'error': 'First name, last name, email, and password are required',
                'status': 'error'
            }, status=400)
        
        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'error': 'Invalid email format',
                'status': 'error'
            }, status=400)
        
        # Check if email already exists
        if Business.objects.filter(email=email).exists():
            return JsonResponse({
                'error': 'Email already registered',
                'status': 'error'
            }, status=400)
        
        # Use database transaction to ensure atomicity
        with transaction.atomic():
            # Create business user
            business = Business(
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            business.set_password(password)
            business.save()
            
            # Create empty business profile
            BusinessProfile.objects.create(business=business)
        
        # Store business ID in session
        request.session['business_id'] = str(business.id)
        request.session['user_type'] = 'business'
        request.session.save()
        
        return JsonResponse({
            'message': 'Business account created successfully',
            'status': 'success',
            'business': {
                'id': str(business.id),
                'first_name': business.first_name,
                'last_name': business.last_name,
                'email': business.email,
            }
        }, status=201)
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in business_register_api: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            'error': 'Invalid JSON data',
            'status': 'error'
        }, status=400)
    except Exception as e:
        logger.error(f"Exception in business_register_api: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            'error': 'Registration failed. Please try again.',
            'status': 'error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def business_login_api(request):
    """Business user login API endpoint"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({
                'error': 'Email and password are required',
                'status': 'error'
            }, status=400)
        
        # Find business by email
        try:
            business = Business.objects.get(email=email, is_active=True)
        except Business.DoesNotExist:
            return JsonResponse({
                'error': 'Invalid credentials',
                'status': 'error'
            }, status=401)
        
        # Check password
        if not business.check_password(password):
            return JsonResponse({
                'error': 'Invalid credentials',
                'status': 'error'
            }, status=401)
        
        # Update last login
        business.last_login = timezone.now()
        business.save()
        
        # Store business ID in session
        request.session['business_id'] = str(business.id)
        request.session['user_type'] = 'business'
        request.session.save()
        
        
        response = JsonResponse({
            'message': 'Login successful',
            'status': 'success',
            'business': {
                'id': str(business.id),
                'first_name': business.first_name,
                'last_name': business.last_name,
                'email': business.email,
            }
        })
        
        # Ensure session cookie is set properly for cross-origin requests
        response.set_cookie(
            'sessionid',
            request.session.session_key,
            max_age=1209600,  # 2 weeks
            secure=True,      # Required for SameSite=None
            samesite='None',  # Allow cross-site cookies
            httponly=True     # Security
        )
        
        return response
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data',
            'status': 'error'
        }, status=400)
    except Exception as e:
        logger.error(f"Exception in business_login_api: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def business_logout_api(request):
    """Business user logout API endpoint"""
    if 'business_id' in request.session:
        del request.session['business_id']
        if 'user_type' in request.session:
            del request.session['user_type']
        return JsonResponse({
            'message': 'Logout successful',
            'status': 'success'
        })
    else:
        return JsonResponse({
            'error': 'Not authenticated',
            'status': 'error'
        }, status=401)


@require_http_methods(["GET"])
def business_profile_api(request):
    """Get current business user's profile"""
    business_id = request.session.get('business_id')
    
    
    if not business_id:
        logger.warning("[Business Profile API] No business_id in session")
        return JsonResponse({
            'error': 'Not authenticated',
            'status': 'error'
        }, status=401)
    
    try:
        business = Business.objects.get(id=business_id, is_active=True)
        
        profile = BusinessProfile.objects.get(business=business)
        
        profile_dict = profile.to_dict()
        
        response_data = {
            'message': 'Profile retrieved successfully',
            'status': 'success',
            'business': {
                'id': str(business.id),
                'first_name': business.first_name,
                'last_name': business.last_name,
                'email': business.email,
                'user_type': 'business',
            },
            'profile': profile_dict
        }
        return JsonResponse(response_data)
        
    except Business.DoesNotExist:
        logger.error(f"[Business Profile API] Business not found for ID: {business_id}")
        return JsonResponse({
            'error': 'Business not found',
            'status': 'error'
        }, status=404)
    except BusinessProfile.DoesNotExist:
        logger.error(f"[Business Profile API] Profile not found for business ID: {business_id}")
        return JsonResponse({
            'error': 'Profile not found',
            'status': 'error'
        }, status=404)
    except Exception as e:
        logger.error(f"[Business Profile API] Exception: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            'error': 'Failed to retrieve profile',
            'status': 'error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST", "PUT"])
def business_profile_update_api(request):
    """Create or update business profile"""
    business_id = request.session.get('business_id')
    
    if not business_id:
        return JsonResponse({
            'error': 'Not authenticated',
            'status': 'error'
        }, status=401)
    
    try:
        business = Business.objects.get(id=business_id, is_active=True)
        profile, created = BusinessProfile.objects.get_or_create(business=business)
        
        # Handle file upload (logo)
        logo_file = request.FILES.get('logo')
        
        if logo_file:
            # Use the same S3 service as business profile tab
            try:
                from services.s3_service import s3_service
                
                logo_url = s3_service.upload_business_logo(logo_file, business.id)
                if not logo_url:
                    return JsonResponse({
                        'error': 'Failed to upload logo. Please try again.',
                        'status': 'error'
                    }, status=500)
                
                profile.logo_url = logo_url
                
            except Exception as e:
                logger.error(f"Logo upload error: {str(e)}")
                return JsonResponse({
                    'error': 'Failed to upload logo',
                    'status': 'error'
                }, status=500)
        
        # Update profile fields from POST data
        updatable_fields = [
            'business_name', 'website_url', 'instagram_handle',
            'primary_color', 'secondary_color', 'accent_color', 'font_family',
            'brand_mission', 'brand_values', 'business_basic_details',
            'business_services', 'business_additional_details'
        ]
        
        for field in updatable_fields:
            value = request.POST.get(field)
            if value is not None:
                setattr(profile, field, value)
        
        profile.save()
        
        return JsonResponse({
            'message': 'Profile updated successfully',
            'status': 'success',
            'profile': profile.to_dict()
        })
    
    except Business.DoesNotExist:
        return JsonResponse({
            'error': 'Business not found',
            'status': 'error'
        }, status=404)
    except Exception as e:
        logger.error(f"Exception in business_profile_update_api: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            'error': f'Failed to update profile: {str(e)}',
            'status': 'error'
        }, status=500)


@require_http_methods(["GET"])
def business_auth_status_api(request):
    """Check business authentication status"""
    business_id = request.session.get('business_id')
    user_type = request.session.get('user_type')
    
    
    if business_id and user_type == 'business':
        try:
            business = Business.objects.get(id=business_id, is_active=True)
            response_data = {
                'authenticated': True,
                'user_type': 'business',
                'status': 'success',
                'business': {
                    'id': str(business.id),
                    'first_name': business.first_name,
                    'last_name': business.last_name,
                    'email': business.email,
                }
            }
            return JsonResponse(response_data)
        except Business.DoesNotExist:
            logger.warning(f"[Business Auth Status] Business not found for ID: {business_id}")
            return JsonResponse({
                'authenticated': False,
                'status': 'success',
                'message': 'Business not found'
            })
    else:
        return JsonResponse({
            'authenticated': False,
            'status': 'success',
            'message': 'Not authenticated'
        })

