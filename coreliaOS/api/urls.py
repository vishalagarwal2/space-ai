from django.urls import path, include
from . import views
from . import profile_views
from django.http import JsonResponse

def home_view(request):
    """Simple home page API"""
    return JsonResponse({
        'message': 'Welcome to CoreliaOS API',
        'status': 'success',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/',
            'public_api': '/api/public/',
            'auth_status': '/api/auth/status/',
            'login': '/api/auth/login/',
            'register': '/api/auth/register/',
            'logout': '/api/auth/logout/',
            'protected': '/api/protected/',
            'user_profile': '/api/user/profile/',
            'admin_users': '/api/admin/users/',
        }
    })

app_name = 'api'

urlpatterns = [
    # Home API
    path('', home_view, name='home'),
    
    # Business APIs (separate authentication system)
    path('business/', include('api.business_urls')),
    
    # Public APIs
    path('public/', views.public_api, name='public_api'),
    path('public/async/', views.public_async_api, name='public_data_api'),
    path('auth/status/', views.auth_status_api, name='auth_status'),
    
    # Authentication APIs
    path('auth/login/', views.login_api, name='login'),
    path('auth/register/', views.register_api, name='register'),
    path('auth/logout/', views.logout_api, name='logout'),
    
    # Protected APIs
    path('protected/', views.protected_api, name='protected_api'),
    path('user/profile/', views.user_profile_api, name='user_profile'),
    path('user/update/', views.update_profile_api, name='update_profile'),
    
    # Admin-only APIs
    path('admin/users/', views.admin_only_api, name='admin_users'),
    path('company-profile/', profile_views.company_profile_api, name='company-profile'),
    path('company-profile/refresh-logo/', profile_views.refresh_logo_url_api, name='refresh-logo'),
    
    # Instagram Post APIs
    path('instagram-posts/', profile_views.get_instagram_posts_api, name='instagram-posts'),
    path('instagram-posts/create/', profile_views.create_instagram_post_api, name='create-instagram-post'),
    path('instagram-posts/post/', profile_views.post_to_instagram_api, name='post-to-instagram'),
    
    # Social Media Post APIs
    path('social-media/generate-post/', profile_views.generate_social_media_post_api, name='generate-social-media-post'),
    path('social-media/refine-post/', profile_views.refine_social_media_post_api, name='refine-social-media-post'),
    path('social-media/publish-post/', profile_views.publish_social_media_post_api, name='publish-social-media-post'),
    path('social-media/upload-image/', profile_views.upload_post_image_api, name='upload-post-image'),
    
    # Content Calendar APIs
    path('content-calendar/generate/', views.generate_content_calendar, name='generate_content_calendar'),
    path('content-calendar/', views.get_content_calendars, name='get_content_calendars'),
    path('content-calendar/<uuid:calendar_id>/delete/', views.delete_content_calendar, name='delete_content_calendar'),
    path('content-calendar/ideas/<uuid:idea_id>/approve/', views.approve_content_idea, name='approve_content_idea'),
    path('content-calendar/ideas/<uuid:idea_id>/unschedule/', views.unschedule_content_idea, name='unschedule_content_idea'),
    path('content-calendar/ideas/<uuid:idea_id>/generate-post/', views.generate_post_for_content_idea, name='generate_post_for_content_idea'),
    path('content-calendar/ideas/<uuid:idea_id>/', views.update_content_idea, name='update_content_idea'),
]