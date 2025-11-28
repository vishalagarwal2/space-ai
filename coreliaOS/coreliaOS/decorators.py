"""
Common decorators for the CoreliaOS project.
"""
from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required as django_login_required
import logging

logger = logging.getLogger(__name__)


def login_required(view_func):
    """
    Unified decorator that handles authentication for both web and API endpoints.
    Supports both admin (Django User) and business authentication.
    - For API requests (JSON expected): returns JSON error response
    - For web requests (HTML expected): redirects to login page
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check for admin authentication (Django User)
        is_admin_authenticated = request.user.is_authenticated
        
        # Check for business authentication (session-based)
        is_business_authenticated = (
            'business_id' in request.session and 
            request.session.get('user_type') == 'business'
        )
        
        # If either authentication method is valid, proceed
        if is_admin_authenticated or is_business_authenticated:
            return view_func(request, *args, **kwargs)
        
        # Neither authentication method is valid
        is_api_request = (
            request.path.startswith('/api/') or
            request.content_type == 'application/json' or
            'application/json' in request.META.get('HTTP_ACCEPT', '') or
            request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
        )
        
        if is_api_request:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }, status=401)
        else:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
    
    return _wrapped_view


def business_login_required(view_func):
    """
    Decorator that specifically requires business authentication.
    Only allows business users to access the endpoint.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        business_id = request.session.get('business_id')
        user_type = request.session.get('user_type')
        
        if not business_id or user_type != 'business':
            is_api_request = (
                request.path.startswith('/api/') or
                request.content_type == 'application/json' or
                'application/json' in request.META.get('HTTP_ACCEPT', '') or
                request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
            )
            
            if is_api_request:
                return JsonResponse({
                    'success': False,
                    'error': 'Business authentication required',
                    'code': 'BUSINESS_AUTH_REQUIRED'
                }, status=401)
            else:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def admin_login_required(view_func):
    """
    Decorator that specifically requires admin authentication.
    Only allows admin users (Django User) to access the endpoint.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            is_api_request = (
                request.path.startswith('/api/') or
                request.content_type == 'application/json' or
                'application/json' in request.META.get('HTTP_ACCEPT', '') or
                request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
            )
            
            if is_api_request:
                return JsonResponse({
                    'success': False,
                    'error': 'Admin authentication required',
                    'code': 'ADMIN_AUTH_REQUIRED'
                }, status=401)
            else:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view
