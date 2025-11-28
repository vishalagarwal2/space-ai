# knowledge_base/urls.py

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'knowledge_base'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Data Sources
    path('data-sources/', views.data_sources, name='data_sources'),
    path('data-sources/create/', views.create_data_source, name='create_data_source'),
    path('data-sources/<uuid:source_id>/edit/', views.edit_data_source, name='edit_data_source'),
    path('data-sources/<uuid:source_id>/sync/', views.sync_data_source, name='sync_data_source'),
    
    # Documents
    path('documents/', views.documents, name='documents'),
    path('documents/<uuid:document_id>/', views.document_detail, name='document_detail'),
    path('documents/upload/', views.upload_document, name='upload_document'),
    path('documents/bulk-delete/', views.bulk_delete_documents, name='bulk_delete_documents'),
    path('documents/<uuid:document_id>/restore/', views.restore_document, name='restore_document'),
    
    # AI Agents
    path('agents/', views.ai_agents, name='ai_agents'),
    path('agents/create/', views.create_agent, name='create_agent'),
    path('agents/<uuid:agent_id>/edit/', views.edit_agent, name='edit_agent'),
    path('agents/create-from-template/', views.create_agent_from_template, name='create_agent_from_template'),
    
    # Chat
    path('chat/<uuid:agent_id>/', views.chat_with_agent, name='chat_with_agent'),
    # path('chat/send-message/', views.send_message, name='send_message'),
    
    # Conversations
    path('conversations/', views.conversations, name='conversations'),
    path('conversations/<uuid:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    
    # Search
    path('search/', views.search_documents, name='search_documents'),
    
    # Settings
    path('settings/', views.kb_settings, name='settings'),
    
    # Analytics
    path('analytics/', views.analytics, name='analytics'),
    
    # API endpoints
    path('api/health/', views.api_health, name='api_health'),
]

# Add static files serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)