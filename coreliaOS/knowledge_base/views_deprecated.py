# knowledge_base/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
import json
import asyncio
from typing import Dict, Any

from .models import (
    DataSource, Document, AIAgent, Conversation, Message, 
    FileType, KnowledgeBaseConfig, AgentUsage
)
from .data_sources import data_source_registry
from .ai_agents import agent_executor, AgentTemplateManager
from .embeddings import EmbeddingManager
from .utils import (
    FileTypeDetector, ConfigurationManager, AnalyticsManager,
    ErrorHandler, ProgressTracker
)
from .forms import DataSourceForm, AIAgentForm, DocumentUploadForm


@login_required
def dashboard(request):
    """Knowledge base dashboard"""
    user = request.user
    
    # Get user statistics
    stats = AnalyticsManager.get_user_usage_stats(str(user.id))
    
    # Get recent documents
    recent_documents = Document.objects.filter(
        user=user,
        status='processed'
    ).order_by('-created_at')[:10]
    
    # Get active agents
    active_agents = AIAgent.objects.filter(
        user=user,
        is_active=True
    ).order_by('-created_at')[:5]
    
    # Get recent conversations
    recent_conversations = Conversation.objects.filter(
        user=user
    ).order_by('-updated_at')[:10]
    
    context = {
        'stats': stats,
        'recent_documents': recent_documents,
        'active_agents': active_agents,
        'recent_conversations': recent_conversations,
    }
    
    return render(request, 'knowledge_base/dashboard.html', context)


@login_required
def data_sources(request):
    """Data sources management"""
    sources = DataSource.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(sources, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'source_types': DataSource.SOURCE_TYPES,
        'available_sources': data_source_registry.get_available_sources(),
    }
    
    return render(request, 'knowledge_base/data_sources.html', context)


@login_required
def create_data_source(request):
    """Create new data source"""
    if request.method == 'POST':
        form = DataSourceForm(request.POST)
        if form.is_valid():
            data_source = form.save(commit=False)
            data_source.user = request.user
            data_source.save()
            messages.success(request, 'Data source created successfully!')
            return redirect('knowledge_base:data_sources')
    else:
        form = DataSourceForm()
    
    context = {
        'form': form,
        'source_types': DataSource.SOURCE_TYPES,
    }
    
    return render(request, 'knowledge_base/create_data_source.html', context)


@login_required
def edit_data_source(request, source_id):
    """Edit data source"""
    source = get_object_or_404(DataSource, id=source_id, user=request.user)
    
    if request.method == 'POST':
        form = DataSourceForm(request.POST, instance=source)
        if form.is_valid():
            form.save()
            messages.success(request, 'Data source updated successfully!')
            return redirect('knowledge_base:data_sources')
    else:
        form = DataSourceForm(instance=source)
    
    context = {
        'form': form,
        'source': source,
        'source_types': DataSource.SOURCE_TYPES,
    }
    
    return render(request, 'knowledge_base/edit_data_source.html', context)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def sync_data_source(request, source_id):
    """Sync data source"""
    source = get_object_or_404(DataSource, id=source_id, user=request.user)
    
    try:
        # Get data source instance
        data_source_instance = data_source_registry.get_source(source)
        
        if not data_source_instance:
            return JsonResponse({
                'success': False,
                'error': 'Data source type not supported'
            })
        
        # Perform sync
        source.status = 'syncing'
        source.save()
        
        sync_result = data_source_instance.sync()
        
        if sync_result.get('status') == 'success':
            source.status = 'active'
            source.last_sync = timezone.now()
            messages.success(request, f'Synced {sync_result.get("processed_count", 0)} documents')
        else:
            source.status = 'error'
            messages.error(request, f'Sync failed: {sync_result.get("error", "Unknown error")}')
        
        source.save()
        
        return JsonResponse({
            'success': sync_result.get('status') == 'success',
            'processed_count': sync_result.get('processed_count', 0),
            'error': sync_result.get('error')
        })
        
    except Exception as e:
        source.status = 'error'
        source.save()
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def documents(request):
    """Documents management"""
    documents = Document.objects.filter(user=request.user).order_by('-created_at')
    
    # Filters
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    
    if status_filter:
        documents = documents.filter(status=status_filter)
    
    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(processed_content__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': Document.STATUS_CHOICES,
        'current_status': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'knowledge_base/documents.html', context)


@login_required
def document_detail(request, document_id):
    """Document detail view"""
    document = get_object_or_404(Document, id=document_id, user=request.user)
    
    # Get document chunks
    chunks = document.chunks.all().order_by('chunk_index')
    
    context = {
        'document': document,
        'chunks': chunks,
    }
    
    return render(request, 'knowledge_base/document_detail.html', context)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def upload_document(request):
    """Upload document via AJAX"""
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Handle file upload
                uploaded_file = request.FILES['file']
                
                # Create document record
                document = Document.objects.create(
                    user=request.user,
                    data_source=None,  # Direct upload
                    title=uploaded_file.name,
                    original_filename=uploaded_file.name,
                    file_size=uploaded_file.size,
                    mime_type=uploaded_file.content_type or 'application/octet-stream',
                    status='pending'
                )
                
                # Save file and process
                # This would typically be done in a background task
                
                return JsonResponse({
                    'success': True,
                    'document_id': str(document.id),
                    'message': 'Document uploaded successfully'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request'
    })


@login_required
def ai_agents(request):
    """AI agents management"""
    agents = AIAgent.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(agents, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'agent_types': AIAgent.AGENT_TYPES,
    }
    
    return render(request, 'knowledge_base/ai_agents.html', context)


@login_required
def create_agent(request):
    """Create new AI agent"""
    if request.method == 'POST':
        form = AIAgentForm(request.POST)
        if form.is_valid():
            agent = form.save(commit=False)
            agent.user = request.user
            agent.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'AI agent created successfully!')
            return redirect('knowledge_base:ai_agents')
    else:
        form = AIAgentForm()
        form.fields['data_sources'].queryset = DataSource.objects.filter(user=request.user)
    
    context = {
        'form': form,
        'agent_types': AIAgent.AGENT_TYPES,
        'templates': AgentTemplateManager.get_templates(),
    }
    
    return render(request, 'knowledge_base/create_agent.html', context)


@login_required
def edit_agent(request, agent_id):
    """Edit AI agent"""
    agent = get_object_or_404(AIAgent, id=agent_id, user=request.user)
    
    if request.method == 'POST':
        form = AIAgentForm(request.POST, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, 'AI agent updated successfully!')
            return redirect('knowledge_base:ai_agents')
    else:
        form = AIAgentForm(instance=agent)
        form.fields['data_sources'].queryset = DataSource.objects.filter(user=request.user)
    
    context = {
        'form': form,
        'agent': agent,
        'agent_types': AIAgent.AGENT_TYPES,
    }
    
    return render(request, 'knowledge_base/edit_agent.html', context)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_agent_from_template(request):
    """Create agent from template"""
    try:
        data = json.loads(request.body)
        template_name = data.get('template_name')
        custom_config = data.get('custom_config', {})
        
        if not template_name:
            return JsonResponse({
                'success': False,
                'error': 'Template name is required'
            })
        
        # Create agent from template
        agent = AgentTemplateManager.create_agent_from_template(
            request.user, template_name, custom_config
        )
        
        return JsonResponse({
            'success': True,
            'agent_id': str(agent.id),
            'message': 'Agent created from template successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def chat_with_agent(request, agent_id):
    """Chat interface with AI agent"""
    agent = get_object_or_404(AIAgent, id=agent_id, user=request.user)
    
    # Get or create conversation
    conversation_id = request.GET.get('conversation_id')
    if conversation_id:
        conversation = get_object_or_404(
            Conversation, id=conversation_id, user=request.user, agent=agent
        )
    else:
        conversation = Conversation.objects.create(
            user=request.user,
            agent=agent,
            title="New Conversation"
        )
    
    # Get messages
    messages = conversation.messages.order_by('created_at')
    
    context = {
        'agent': agent,
        'conversation': conversation,
        'messages': messages,
    }
    
    return render(request, 'knowledge_base/chat.html', context)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def send_message(request):
    """Send message to AI agent"""
    try:
        data = json.loads(request.body)
        agent_id = data.get('agent_id')
        message_content = data.get('message')
        conversation_id = data.get('conversation_id')
        
        if not agent_id or not message_content:
            return JsonResponse({
                'success': False,
                'error': 'Agent ID and message are required'
            })
        
        # Get agent and conversation
        agent = get_object_or_404(AIAgent, id=agent_id, user=request.user)
        
        conversation = None
        if conversation_id:
            conversation = get_object_or_404(
                Conversation, id=conversation_id, user=request.user, agent=agent
            )
        
        # Execute agent request
        response = asyncio.run(
            agent_executor.execute_agent_request(
                agent, message_content, conversation
            )
        )
        
        return JsonResponse({
            'success': not response.get('error'),
            'response': response.get('content', ''),
            'conversation_id': response.get('conversation_id'),
            'context_docs': response.get('context_docs', []),
            'usage': response.get('usage', {}),
            'error': response.get('error')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def conversations(request):
    """Conversations management"""
    conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')
    
    # Filters
    agent_filter = request.GET.get('agent')
    if agent_filter:
        conversations = conversations.filter(agent_id=agent_filter)
    
    # Pagination
    paginator = Paginator(conversations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get user's agents for filter
    user_agents = AIAgent.objects.filter(user=request.user, is_active=True)
    
    context = {
        'page_obj': page_obj,
        'user_agents': user_agents,
        'current_agent': agent_filter,
    }
    
    return render(request, 'knowledge_base/conversations.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """Conversation detail view"""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    
    # Get messages
    messages = conversation.messages.order_by('created_at')
    
    context = {
        'conversation': conversation,
        'messages': messages,
    }
    
    return render(request, 'knowledge_base/conversation_detail.html', context)


@login_required
def search_documents(request):
    """Search documents"""
    query = request.GET.get('q', '')
    results = []
    
    if query:
        try:
            # Initialize embedding manager
            embedding_manager = EmbeddingManager(str(request.user.id))
            
            # Search documents
            search_results = embedding_manager.search_similar_documents(
                query=query,
                k=20,
                filter_metadata={'user_id': str(request.user.id)}
            )
            
            # Format results
            for result in search_results:
                doc_id = result.get('metadata', {}).get('document_id')
                if doc_id:
                    try:
                        document = Document.objects.get(id=doc_id, user=request.user)
                        results.append({
                            'document': document,
                            'content': result.get('text', ''),
                            'similarity': result.get('similarity', 0),
                            'metadata': result.get('metadata', {})
                        })
                    except Document.DoesNotExist:
                        continue
                        
        except Exception as e:
            messages.error(request, f'Search error: {e}')
    
    context = {
        'query': query,
        'results': results,
    }
    
    return render(request, 'knowledge_base/search.html', context)


@login_required
def settings(request):
    """Knowledge base settings"""
    # Get or create user config
    config, created = KnowledgeBaseConfig.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update configuration
        config.default_embedding_model = request.POST.get('default_embedding_model', config.default_embedding_model)
        config.default_chunk_size = int(request.POST.get('default_chunk_size', config.default_chunk_size))
        config.default_chunk_overlap = int(request.POST.get('default_chunk_overlap', config.default_chunk_overlap))
        config.document_retention_days = int(request.POST.get('document_retention_days', config.document_retention_days))
        config.conversation_retention_days = int(request.POST.get('conversation_retention_days', config.conversation_retention_days))
        config.default_similarity_threshold = float(request.POST.get('default_similarity_threshold', config.default_similarity_threshold))
        config.max_search_results = int(request.POST.get('max_search_results', config.max_search_results))
        config.sync_notifications = request.POST.get('sync_notifications') == 'on'
        config.error_notifications = request.POST.get('error_notifications') == 'on'
        
        # API keys (if provided)
        if request.POST.get('openai_api_key'):
            config.openai_api_key = request.POST.get('openai_api_key')
        if request.POST.get('anthropic_api_key'):
            config.anthropic_api_key = request.POST.get('anthropic_api_key')
        if request.POST.get('cohere_api_key'):
            config.cohere_api_key = request.POST.get('cohere_api_key')
        
        config.save()
        messages.success(request, 'Settings updated successfully!')
        return redirect('knowledge_base:settings')
    
    context = {
        'config': config,
    }
    
    return render(request, 'knowledge_base/settings.html', context)


@login_required
def analytics(request):
    """Analytics dashboard"""
    user_id = str(request.user.id)
    
    # Get analytics data
    usage_stats = AnalyticsManager.get_user_usage_stats(user_id)
    
    # Get agent performance stats
    agent_stats = []
    for agent in AIAgent.objects.filter(user=request.user, is_active=True):
        stats = AnalyticsManager.get_agent_performance_stats(str(agent.id))
        agent_stats.append({
            'agent': agent,
            'stats': stats
        })
    
    context = {
        'usage_stats': usage_stats,
        'agent_stats': agent_stats,
    }
    
    return render(request, 'knowledge_base/analytics.html', context)


@require_http_methods(["GET"])
def api_health(request):
    """API health check"""
    try:
        # Check system health
        health_stats = AnalyticsManager.get_system_health_stats()
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'stats': health_stats
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def bulk_delete_documents(request):
    """Bulk delete documents"""
    try:
        data = json.loads(request.body)
        document_ids = data.get('document_ids', [])
        
        if not document_ids:
            return JsonResponse({
                'success': False,
                'error': 'No documents selected'
            })
        
        # Soft delete documents
        documents = Document.objects.filter(
            id__in=document_ids,
            user=request.user
        )
        
        count = 0
        for doc in documents:
            doc.soft_delete()
            count += 1
        
        return JsonResponse({
            'success': True,
            'deleted_count': count,
            'message': f'Deleted {count} documents'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def restore_document(request, document_id):
    """Restore soft-deleted document"""
    try:
        document = get_object_or_404(
            Document, id=document_id, user=request.user, status='soft_deleted'
        )
        
        document.restore()
        
        return JsonResponse({
            'success': True,
            'message': 'Document restored successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })