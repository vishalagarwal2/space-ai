from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'agent_tagging'

urlpatterns = [
    # Dashboard
    path('create-group/', views.create_agent_group, name='create group'),
    path('groups/get/', views.get_agent_group, name = 'get-agent-groups')
    
]
