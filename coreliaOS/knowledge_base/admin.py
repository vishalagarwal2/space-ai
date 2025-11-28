# knowledge_base/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg
import json

from .models import (
    DataSource, Document, DocumentChunk, AIAgent, Conversation, 
    Message, AgentUsage, FileType, KnowledgeBaseConfig
)


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    """Admin interface for DataSource model"""
    
    list_display = [
        'name', 'user', 'source_type', 'status', 'auto_sync', 
        'last_sync', 'created_at', 'document_count'
    ]
    list_filter = ['source_type', 'status', 'auto_sync', 'created_at']
    search_fields = ['name', 'user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_sync']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'name', 'source_type', 'status')
        }),
        ('Configuration', {
            'fields': ('config', 'credentials'),
            'classes': ('collapse',)
        }),
        ('Sync Settings', {
            'fields': ('auto_sync', 'sync_frequency', 'last_sync')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def document_count(self, obj):
        """Get document count for data source"""
        return obj.documents.count()
    document_count.short_description = 'Documents'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model"""
    
    list_display = [
        'title', 'user', 'data_source', 'status', 'file_size_display', 
        'created_at', 'chunk_count'
    ]
    list_filter = ['status', 'data_source__source_type', 'created_at', 'file_type']
    search_fields = ['title', 'user__username', 'processed_content']
    readonly_fields = ['id', 'created_at', 'updated_at', 'processing_log_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'data_source', 'file_type', 'title', 'status')
        }),
        ('File Information', {
            'fields': ('original_filename', 'file_path', 'file_size', 'mime_type')
        }),
        ('Content', {
            'fields': ('raw_content', 'processed_content'),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': ('processing_log_display',),
            'classes': ('collapse',)
        }),
        ('Lifecycle', {
            'fields': ('expires_at', 'soft_deleted_at')
        }),
        ('Metadata', {
            'fields': ('source_metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def file_size_display(self, obj):
        """Display file size in human readable format"""
        if obj.file_size:
            for unit in ['B', 'KB', 'MB', 'GB']:
                if obj.file_size < 1024.0:
                    return f"{obj.file_size:.1f} {unit}"
                obj.file_size /= 1024.0
        return "0 B"
    file_size_display.short_description = 'Size'
    
    def chunk_count(self, obj):
        """Get chunk count for document"""
        return obj.chunks.count()
    chunk_count.short_description = 'Chunks'
    
    def processing_log_display(self, obj):
        """Display processing log in formatted way"""
        if obj.processing_log:
            return format_html(
                '<pre>{}</pre>',
                json.dumps(obj.processing_log, indent=2)
            )
        return "No processing log"
    processing_log_display.short_description = 'Processing Log'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related(
            'user', 'data_source', 'file_type'
        )


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    """Admin interface for DocumentChunk model"""
    
    list_display = ['document', 'chunk_index', 'content_preview', 'created_at']
    list_filter = ['created_at', 'document__status']
    search_fields = ['content', 'document__title']
    readonly_fields = ['id', 'created_at', 'embeddings_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'document', 'chunk_index', 'content')
        }),
        ('Embeddings', {
            'fields': ('embeddings_display',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )
    
    def content_preview(self, obj):
        """Show content preview"""
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def embeddings_display(self, obj):
        """Display embeddings in formatted way"""
        if obj.embeddings:
            return format_html(
                '<pre>{}</pre>',
                json.dumps(obj.embeddings, indent=2)
            )
        return "No embeddings"
    embeddings_display.short_description = 'Embeddings'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('document')


@admin.register(AIAgent)
class AIAgentAdmin(admin.ModelAdmin):
    """Admin interface for AIAgent model"""
    
    list_display = [
        'name', 'user', 'agent_type', 'model_provider', 'model_name', 
        'is_active', 'created_at', 'conversation_count'
    ]
    list_filter = [
        'agent_type', 'model_provider', 'conversation_mode', 
        'is_active', 'created_at'
    ]
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['data_sources', 'file_types']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'name', 'description', 'agent_type', 'is_active')
        }),
        ('Model Configuration', {
            'fields': ('model_provider', 'model_name', 'model_parameters')
        }),
        ('Conversation Settings', {
            'fields': ('conversation_mode', 'context_window', 'memory_retention_days')
        }),
        ('Prompts', {
            'fields': ('system_prompt', 'user_prompt_template'),
            'classes': ('collapse',)
        }),
        ('Knowledge Base', {
            'fields': ('data_sources', 'file_types', 'max_documents', 'similarity_threshold')
        }),
        ('Rate Limiting', {
            'fields': ('rate_limit_per_hour', 'rate_limit_per_day')
        }),
        ('Domain Specific', {
            'fields': ('domain_keywords', 'expertise_areas'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def conversation_count(self, obj):
        """Get conversation count for agent"""
        return obj.conversations.count()
    conversation_count.short_description = 'Conversations'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin interface for Conversation model"""
    
    list_display = [
        'title', 'user', 'agent', 'message_count', 'created_at', 'updated_at'
    ]
    list_filter = ['agent__agent_type', 'created_at', 'updated_at']
    search_fields = ['title', 'user__username', 'agent__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'context_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'agent', 'title')
        }),
        ('Context', {
            'fields': ('context_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def message_count(self, obj):
        """Get message count for conversation"""
        return obj.messages.count()
    message_count.short_description = 'Messages'
    
    def context_display(self, obj):
        """Display context in formatted way"""
        if obj.context:
            return format_html(
                '<pre>{}</pre>',
                json.dumps(obj.context, indent=2)
            )
        return "No context"
    context_display.short_description = 'Context'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user', 'agent')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for Message model"""
    
    list_display = [
        'conversation', 'role', 'content_preview', 'created_at', 'cited_doc_count'
    ]
    list_filter = ['role', 'created_at']
    search_fields = ['content', 'conversation__title']
    readonly_fields = ['id', 'created_at', 'metadata_display']
    filter_horizontal = ['cited_documents']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'conversation', 'role', 'content')
        }),
        ('Citations', {
            'fields': ('cited_documents',)
        }),
        ('Metadata', {
            'fields': ('metadata_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )
    
    def content_preview(self, obj):
        """Show content preview"""
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def cited_doc_count(self, obj):
        """Get cited document count"""
        return obj.cited_documents.count()
    cited_doc_count.short_description = 'Citations'
    
    def metadata_display(self, obj):
        """Display metadata in formatted way"""
        if obj.metadata:
            return format_html(
                '<pre>{}</pre>',
                json.dumps(obj.metadata, indent=2)
            )
        return "No metadata"
    metadata_display.short_description = 'Metadata'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('conversation')


@admin.register(AgentUsage)
class AgentUsageAdmin(admin.ModelAdmin):
    """Admin interface for AgentUsage model"""
    
    list_display = [
        'user', 'agent', 'tokens_used', 'cost', 'response_time', 'created_at'
    ]
    list_filter = ['agent__agent_type', 'created_at']
    search_fields = ['user__username', 'agent__name']
    readonly_fields = ['id', 'created_at', 'request_data_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'agent')
        }),
        ('Usage Metrics', {
            'fields': ('tokens_used', 'cost', 'response_time')
        }),
        ('Request Data', {
            'fields': ('request_data_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )
    
    def request_data_display(self, obj):
        """Display request data in formatted way"""
        if obj.request_data:
            return format_html(
                '<pre>{}</pre>',
                json.dumps(obj.request_data, indent=2)
            )
        return "No request data"
    request_data_display.short_description = 'Request Data'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user', 'agent')


@admin.register(FileType)
class FileTypeAdmin(admin.ModelAdmin):
    """Admin interface for FileType model"""
    
    list_display = ['name', 'category', 'is_active', 'created_at', 'document_count']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'is_active')
        }),
        ('File Detection', {
            'fields': ('mime_types', 'extensions')
        }),
        ('Processing', {
            'fields': ('parsers', 'embedding_models')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def document_count(self, obj):
        """Get document count for file type"""
        return obj.document_set.count()
    document_count.short_description = 'Documents'


@admin.register(KnowledgeBaseConfig)
class KnowledgeBaseConfigAdmin(admin.ModelAdmin):
    """Admin interface for KnowledgeBaseConfig model"""
    
    list_display = [
        'user', 'default_embedding_model', 'default_chunk_size', 
        'document_retention_days', 'created_at'
    ]
    list_filter = ['default_embedding_model', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Embedding Settings', {
            'fields': ('default_embedding_model', 'default_chunk_size', 'default_chunk_overlap')
        }),
        ('Retention Settings', {
            'fields': ('document_retention_days', 'conversation_retention_days')
        }),
        ('Search Settings', {
            'fields': ('default_similarity_threshold', 'max_search_results')
        }),
        ('Notifications', {
            'fields': ('sync_notifications', 'error_notifications')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user')


# Custom admin actions
@admin.action(description='Soft delete selected documents')
def soft_delete_documents(modeladmin, request, queryset):
    """Soft delete selected documents"""
    count = 0
    for document in queryset:
        document.soft_delete()
        count += 1
    modeladmin.message_user(request, f'Soft deleted {count} documents.')


@admin.action(description='Restore selected documents')
def restore_documents(modeladmin, request, queryset):
    """Restore selected documents"""
    count = 0
    for document in queryset.filter(status='soft_deleted'):
        document.restore()
        count += 1
    modeladmin.message_user(request, f'Restored {count} documents.')


@admin.action(description='Activate selected agents')
def activate_agents(modeladmin, request, queryset):
    """Activate selected agents"""
    count = queryset.update(is_active=True)
    modeladmin.message_user(request, f'Activated {count} agents.')


@admin.action(description='Deactivate selected agents')
def deactivate_agents(modeladmin, request, queryset):
    """Deactivate selected agents"""
    count = queryset.update(is_active=False)
    modeladmin.message_user(request, f'Deactivated {count} agents.')


# Add actions to admin classes
DocumentAdmin.actions = [soft_delete_documents, restore_documents]
AIAgentAdmin.actions = [activate_agents, deactivate_agents]


# Admin site customization
admin.site.site_header = 'Knowledge Base Administration'
admin.site.site_title = 'Knowledge Base Admin'
admin.site.index_title = 'Welcome to Knowledge Base Administration'