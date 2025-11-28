from django.urls import path
from . import business_views

app_name = 'business'

urlpatterns = [
    # Business Authentication
    path('auth/register/', business_views.business_register_api, name='business_register'),
    path('auth/login/', business_views.business_login_api, name='business_login'),
    path('auth/logout/', business_views.business_logout_api, name='business_logout'),
    path('auth/status/', business_views.business_auth_status_api, name='business_auth_status'),
    
    # Business Profile
    path('profile/', business_views.business_profile_api, name='business_profile'),
    path('profile/update/', business_views.business_profile_update_api, name='business_profile_update'),
]

