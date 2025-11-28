# knowledge_base/urls.py

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'knowledge_base'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Data Sources
    path('data-sources/', views.data_sources, name='data_sources'),
    path('data-sources/create/', views.create_data_source, name='create_data_source'),
    path('data-sources/<uuid:source_id>/', views.edit_data_source, name='edit_data_source'),
    path('data-sources/<uuid:source_id>/sync/', views.sync_data_source, name='sync_data_source'),
    path('data-sources/<uuid:source_id>/delete/', views.delete_data_source, name='delete_data_source'),
    path('data-sources/<uuid:source_id>/upload/', views.upload_files_to_data_source, name='test_data_source'),

    # Data Sources OAuth
    path('oauth/initiate/<uuid:source_id>/', views.initiate_oauth, name='initiate_oauth'),
    path('google/oauth2callback/', views.oauth_callback, name='oauth_callback'),
    path('oauth/status/<uuid:source_id>/', views.oauth_status, name='oauth_status'),
    path('oauth/revoke/<uuid:source_id>/', views.revoke_oauth, name='revoke_oauth'),
    path('oauth/sources/', views.list_oauth_sources, name='list_oauth_sources'),
    
    # Documents
    path('documents/', views.documents, name='documents'),
    path('documents/<uuid:document_id>/', views.document_detail, name='document_detail'),
    path('documents/<uuid:document_id>/reprocess/', views.reprocess_document, name='reprocess_document'),
    path('documents/upload/', views.upload_document, name='upload_document'),
    path('documents/bulk-delete/', views.bulk_delete_documents, name='bulk_delete_documents'),
    path('documents/<uuid:document_id>/restore/', views.restore_document, name='restore_document'),
    
    # AI Agents
    path('agents/', views.ai_agents, name='ai_agents'),
    path('agents/create/', views.create_agent, name='create_agent'),
    path('agents/<uuid:agent_id>/', views.edit_agent, name='edit_agent'),
    path('agents/<uuid:agent_id>/delete/', views.delete_agent, name='delete_agent'),
    path('agents/templates/', views.get_agent_templates, name='get_agent_templates'),
    path('agents/create-from-template/', views.create_agent_from_template, name='create_agent_from_template'),
    # Chat
    path('chat/send/', views.send_message, name='send_message'),
    
    # Conversations
    path('conversations/', views.conversations, name='conversations'),
    path('conversations/<uuid:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversations/<uuid:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
    
    # Search
    path('search/', views.search_documents, name='search_documents'),
    
    # Settings
    path('settings/', views.kb_settings, name='settings'),
    path('settings/update/', views.update_settings, name='update_settings'),
    
    # Analytics
    path('analytics/', views.analytics, name='analytics'),
    
    # File Types
    path('file-types/', views.get_file_types, name='get_file_types'),
    
    # Health Check
    path('health/', views.api_health, name='api_health'),
    
    # Connected Accounts
    path('connected-accounts/', views.get_connected_accounts, name='get_connected_accounts'),
    path('connected-accounts/instagram/connect/', views.initiate_instagram_connection, name='initiate_instagram_connection'),
    path('connected-accounts/instagram/callback/', views.instagram_oauth_callback, name='instagram_oauth_callback'),
    path('connected-accounts/instagram/deauthorize/', views.instagram_deauthorize_callback, name='instagram_deauthorize_callback'),
    
    # Simple Instagram callback for testing
    path('instagram/callback/', views.instagram_oauth_callback, name='instagram_oauth_callback_simple'),
    path('instagram/deauthorize/', views.instagram_deauthorize_callback, name='instagram_deauthorize_callback_simple'),
    path('connected-accounts/<uuid:account_id>/disconnect/', views.disconnect_account, name='disconnect_account'),
    path('connected-accounts/instagram/post/', views.post_to_instagram, name='post_to_instagram'),

    # file upload gcs
    # path('gcs/upload/direct/', views.gcs_file_upload_direct, name='gcs-file-upload-direct'),
    # path('gcs/upload/with-uuid/', views.gcs_file_upload_with_uuid, name='gcs-file-upload-with-uuid'),
    # path('gcs/file-upload-single-folder/', views.gcs_file_upload_single_uuid, name='gcs-file-upload-single'),

]

# Add static files serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)