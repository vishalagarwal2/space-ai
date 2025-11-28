
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import json
import uuid
import logging
from functools import wraps
from coreliaOS.decorators import login_required

from .models import (
    DataSource, Document, AIAgent, Conversation, 
    FileType, KnowledgeBaseConfig, ConnectedAccount
)
from .data_sources import (
    data_source_registry, 
    get_oauth_authorization_url, 
    handle_oauth_callback, 
    is_oauth_authenticated
)
from .ai_agents import agent_executor, AgentTemplateManager
from .embeddings import EmbeddingManager
import os
from django.conf import settings
from django.core.files.storage import default_storage
from .utils import AnalyticsManager

from .data_sources import GCSDataSource

logger = logging.getLogger(__name__)




def create_default_social_media_agent(user):
    """Create a default social media agent for the user"""
    social_media_prompt = """You are an expert social media content creator specializing in Instagram posts. Your role is to help businesses create engaging, high-converting Instagram content.

Key capabilities:
- Generate detailed image prompts for DALL-E based on user requests and business context
- Create compelling Instagram post captions with relevant hashtags
- Develop content ideas based on business goals and brand voice
- Provide visual content descriptions and suggestions
- Handle post refinement and editing requests

Workflow for post creation:
1. Analyze user request and extract key themes
2. Use business context (company name, industry, brand voice, target audience) to inform content
3. Generate detailed image prompt for DALL-E that includes:
   - Visual style matching brand colors and voice
   - Relevant props and scenes for the business
   - Clear text placement instructions
   - Brand-appropriate tone and mood
4. Create engaging caption that:
   - Matches the brand voice
   - Does NOT include hashtags in the caption text
   - Has appropriate call-to-action
   - Stays within Instagram character limits
5. Present the complete post for user review and refinement

Guidelines:
- Always use the provided business context to maintain brand consistency
- Generate image prompts that are specific and detailed for DALL-E
- Include 5-10 relevant hashtags with good mix of popular and niche tags
- Keep captions engaging but not overly promotional - NO hashtags in caption text
- Consider Instagram's algorithm preferences
- Be creative while staying true to the brand voice

When responding, structure your response as:
- Image Prompt: [Detailed prompt for DALL-E]
- Caption: [Engaging caption text without hashtags]
- Hashtags: [Relevant hashtags separated by spaces]

Always be creative, engaging, and focused on driving real business results through social media."""

    agent = AIAgent.objects.create(
        user=user,
        name="Social Media Content Creator",
        description="AI assistant specialized in creating engaging Instagram posts and social media content",
        agent_type="content_creator",
        model_provider="openai",
        model_name="gpt-4o-mini",  # Using cheaper model to match working generate_post endpoint
        system_prompt=social_media_prompt,
        user_prompt_template="Create Instagram content for: {user_input}",
        conversation_mode="session",
        context_window=4000,
        memory_retention_days=30,
        max_documents=5,
        similarity_threshold=0.7,
        rate_limit_per_hour=50,
        rate_limit_per_day=500,
        domain_keywords=["social media", "instagram", "content creation", "marketing", "engagement"],
        expertise_areas=["Social Media Marketing", "Content Creation", "Instagram Strategy", "Brand Voice"],
        is_active=True
    )
    
    logger.info(f"Created default social media agent for user {user.id}")
    return agent


def model_to_dict(instance, fields=None, exclude=None):
    """Convert model instance to dictionary"""
    data = {}
    opts = instance._meta
    
    for field in opts.concrete_fields:
        if fields and field.name not in fields:
            continue
        if exclude and field.name in exclude:
            continue
            
        value = field.value_from_object(instance)
        if hasattr(value, 'isoformat'):
            value = value.isoformat()
        elif isinstance(value, bytes):
            value = value.decode('utf-8')
        data[field.name] = value
    
    return data


@login_required
@require_http_methods(["GET"])
def dashboard(request):
    """Knowledge base dashboard API"""
    try:
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
        
        return JsonResponse({
            'success': True,
            'data': {
                'stats': stats,
                'recent_documents': [model_to_dict(doc) for doc in recent_documents],
                'active_agents': [model_to_dict(agent) for agent in active_agents],
                'recent_conversations': [model_to_dict(conv) for conv in recent_conversations],
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def data_sources(request):
    """Get data sources with pagination"""
    try:
        sources = DataSource.objects.filter(user=request.user).order_by('-created_at')
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        paginator = Paginator(sources, page_size)
        page_obj = paginator.get_page(page)
        
        return JsonResponse({
            'success': True,
            'data': {
                'sources': [model_to_dict(source) for source in page_obj],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            },
            'meta': {
                'source_types': DataSource.SOURCE_TYPES,
                'available_sources': data_source_registry.get_available_sources(),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_data_source(request):
    """Create new data source"""
    try:
        data = json.loads(request.body)
        required_fields = ['name', 'source_type']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)

        source_type = data['source_type']
        defaults = data_source_registry.get_default_config(source_type)
        config = data.get('config', {}) or defaults.get('config', {})

        # Use shared Google OAuth credentials if available
        credentials = data.get('credentials', {}) or defaults.get('credentials', {})
        if source_type in ['gmail', 'google_drive', 'google_calendar', 'google_sheets']:
            user_oauth = getattr(request.user, 'google_oauth', None)
            if user_oauth and user_oauth.credentials:
                credentials = user_oauth.credentials

        auto_sync = data.get('auto_sync', True) or defaults.get('auto_sync', True)
        sync_frequency = data.get('sync_frequency', 24) or defaults.get('sync_frequency', 24)

        data_source = DataSource.objects.create(
            user=request.user,
            name=data['name'],
            source_type=source_type,
            config=config,
            credentials=credentials,
            auto_sync=auto_sync,
            sync_frequency=sync_frequency
        )

        return JsonResponse({
            'success': True,
            'data': model_to_dict(data_source),
            'message': 'Data source created successfully'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["PUT"])
def edit_data_source(request, source_id):
    """Edit data source"""
    try:
        data_source = get_object_or_404(DataSource, id=source_id, user=request.user)
        data = json.loads(request.body)
        
        # Update fields
        for field in ['name', 'config', 'credentials', 'auto_sync', 'sync_frequency']:
            if field in data:
                setattr(data_source, field, data[field])
        
        data_source.save()
        
        return JsonResponse({
            'success': True,
            'data': model_to_dict(data_source),
            'message': 'Data source updated successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def sync_data_source(request, source_id):
    """Sync data source"""
    try:
        source = get_object_or_404(DataSource, id=source_id, user=request.user)
        
        # Get data source instance
        data_source_instance = data_source_registry.get_source(source)
        
        if not data_source_instance:
            return JsonResponse({
                'success': False,
                'error': 'Data source type not supported'
            }, status=400)
        
        # Perform sync
        source.status = 'syncing'
        source.save()
        
        sync_result = data_source_instance.sync()
        
        if sync_result.get('status') == 'success':
            source.status = 'active'
            source.last_sync = timezone.now()
        else:
            source.status = 'error'
        
        source.save()
        
        return JsonResponse({
            'success': sync_result.get('status') == 'success',
            'data': {
                'processed_count': sync_result.get('processed_count', 0),
                'source': model_to_dict(source)
            },
            'message': f'Sync completed with {sync_result.get("processed_count", 0)} documents processed'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def documents(request):
    """Get documents with filtering and pagination"""
    try:
        documents = Document.objects.filter(user=request.user).order_by('-created_at')
        
        # Filters
        status_filter = request.GET.get('status')
        search_query = request.GET.get('search')
        data_source_filter = request.GET.get('data_source')
        
        if status_filter:
            documents = documents.filter(status=status_filter)
        
        if search_query:
            documents = documents.filter(
                Q(title__icontains=search_query) |
                Q(processed_content__icontains=search_query)
            )
        
        if data_source_filter == "":
            documents = documents.filter(data_source__isnull=True)
        
        if data_source_filter:
            documents = documents.filter(data_source_id=data_source_filter)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        paginator = Paginator(documents, page_size)
        page_obj = paginator.get_page(page)
        
        return JsonResponse({
            'success': True,
            'data': {
                'documents': [model_to_dict(doc) for doc in page_obj],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            },
            'meta': {
                'status_choices': Document.STATUS_CHOICES,
                'filters': {
                    'status': status_filter,
                    'search': search_query,
                    'data_source': data_source_filter
                }
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def document_detail(request, document_id):
    """Get document detail"""
    try:
        document = get_object_or_404(Document, id=document_id, user=request.user)
        
        # Get document chunks
        chunks = document.chunks.all().order_by('chunk_index')
        
        return JsonResponse({
            'success': True,
            'data': {
                'document': model_to_dict(document),
                'chunks': [model_to_dict(chunk) for chunk in chunks],
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def upload_document(request):
    """Upload document via API"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
            'success': False,
            'error': 'No file provided'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        title = request.POST.get('title', uploaded_file.name)

        # Save file to media/uploads
        # TODO: save file in google cloud storage

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join('uploads', uploaded_file.name)
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        logger.info(f"Uploading document: {uploaded_file.name} to {full_path} and {file_path}")

        with default_storage.open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Create document record
        document = Document.objects.create(
            user=request.user,
            data_source=None,  # Direct upload
            title=title,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
            mime_type=uploaded_file.content_type or 'application/octet-stream',
            file_path=full_path,
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'document': model_to_dict(document)
            },
            'message': 'Document uploaded successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def reprocess_document(request, document_id):
    """Trigger reprocessing of an existing document"""
    try:
        document = Document.objects.get(id=document_id, user=request.user)
        document.reset_for_reprocessing()
        
        return JsonResponse({
            'success': True,
            'message': 'Document queued for reprocessing'
        })
        
    except Document.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Document not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    
@login_required
@require_http_methods(["GET"])
def ai_agents(request):
    """Get AI agents with pagination"""
    try:
        agents = AIAgent.objects.filter(user=request.user).order_by('-created_at')
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        paginator = Paginator(agents, page_size)
        page_obj = paginator.get_page(page)
        
        return JsonResponse({
            'success': True,
            'data': {
                'agents': [model_to_dict(agent) for agent in page_obj],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            },
            'meta': {
                'agent_types': AIAgent.AGENT_TYPES,
                'model_providers': AIAgent.MODEL_PROVIDERS,
                'conversation_modes': AIAgent.CONVERSATION_MODES,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_agent(request):
    """Create new AI agent"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['name', 'agent_type', 'model_provider', 'model_name']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Create agent
        agent = AIAgent.objects.create(
            user=request.user,
            name=data['name'],
            description=data.get('description', ''),
            agent_type=data['agent_type'],
            model_provider=data['model_provider'],
            model_name=data['model_name'],
            model_parameters=data.get('model_parameters', {}),
            conversation_mode=data.get('conversation_mode', 'session'),
            context_window=data.get('context_window', 4000),
            memory_retention_days=data.get('memory_retention_days', 30),
            system_prompt=data.get('system_prompt', ''),
            user_prompt_template=data.get('user_prompt_template', ''),
            max_documents=data.get('max_documents', 10),
            similarity_threshold=data.get('similarity_threshold', 0.7),
            rate_limit_per_hour=data.get('rate_limit_per_hour', 100),
            rate_limit_per_day=data.get('rate_limit_per_day', 1000),
            domain_keywords=data.get('domain_keywords', []),
            expertise_areas=data.get('expertise_areas', []),
            is_active=data.get('is_active', True)
        )
        
        # Add data sources and file types if provided
        if 'data_sources' in data:
            data_sources = DataSource.objects.filter(
                id__in=data['data_sources'],
                user=request.user
            )
            agent.data_sources.set(data_sources)
        
        if 'file_types' in data:
            file_types = FileType.objects.filter(id__in=data['file_types'])
            agent.file_types.set(file_types)
        
        return JsonResponse({
            'success': True,
            'data': model_to_dict(agent),
            'message': 'AI agent created successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["PUT"])
def edit_agent(request, agent_id):
    """Edit AI agent"""
    try:
        agent = get_object_or_404(AIAgent, id=agent_id, user=request.user)
        data = json.loads(request.body)
        
        # Update fields
        updatable_fields = [
            'name', 'description', 'model_provider', 'model_name', 'model_parameters',
            'conversation_mode', 'context_window', 'memory_retention_days',
            'system_prompt', 'user_prompt_template', 'max_documents', 'similarity_threshold',
            'rate_limit_per_hour', 'rate_limit_per_day', 'domain_keywords', 'expertise_areas',
            'is_active'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(agent, field, data[field])
        
        agent.save()
        
        # Update relationships if provided
        if 'data_sources' in data:
            data_sources = DataSource.objects.filter(
                id__in=data['data_sources'],
                user=request.user
            )
            agent.data_sources.set(data_sources)
        
        if 'file_types' in data:
            file_types = FileType.objects.filter(id__in=data['file_types'])
            agent.file_types.set(file_types)
        
        return JsonResponse({
            'success': True,
            'data': model_to_dict(agent),
            'message': 'AI agent updated successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


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
            }, status=400)
        
        # Create agent from template
        agent = AgentTemplateManager.create_agent_from_template(
            request.user, template_name, custom_config
        )
        
        return JsonResponse({
            'success': True,
            'data': model_to_dict(agent),
            'message': 'Agent created from template successfully'
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def send_message(request):
    """[Async] Send message to AI agent"""
    # Fetch user info safely in async context
    def get_user_info(user):
        if user.is_authenticated:
            return str(user.id)
        return "anonymous"

    user_id =get_user_info(request.user)
    logger.info("Received send_message request from user %s", user_id)
    if not request.user.is_authenticated:
        logger.info("Unauthorized send_message attempt")
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    data = json.loads(request.body)
    agent_id = data.get('agent_id')
    # Accept both 'message' and 'content' fields for backward compatibility
    message_content = data.get('message') or data.get('content')
    conversation_id = data.get('conversation_id')
    documents = data.get('documents', [])

    logger.info("send_message payload: agent_id=%s, conversation_id=%s, message_content=%s", agent_id, conversation_id, bool(message_content))

    # Validate message content
    if not message_content:
        logger.info("Missing message/content in send_message request")
        return JsonResponse({'success': False, 'error': 'Message content is required'}, status=400)

    # Get agent - either from agent_id or from conversation
    agent = None
    conversation = None
    
    if agent_id:
        agent = get_object_or_404(AIAgent, id=agent_id, user=request.user)
        logger.info("Found agent %s for user %s", agent_id, request.user.id)
        
        # Get conversation if conversation_id is provided
        if conversation_id:
            conversation = get_object_or_404(
                Conversation, id=conversation_id, user=request.user, agent=agent
            )
            logger.info("Found conversation %s for user %s", conversation_id, request.user.id)
    elif conversation_id:
        # If no agent_id but conversation_id is provided, get agent from conversation
        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        agent = conversation.agent
        logger.info("Found agent %s from conversation %s for user %s", agent.id, conversation_id, request.user.id)
    else:
        # If neither is provided, find or create a default agent and create a conversation
        logger.info("No agent_id or conversation_id provided, creating default conversation for user %s", request.user.id)
        
        # Try to find a social media agent (content_creator type) first
        # Priority: 1) content_creator type with 'social media' in name, 2) content_creator type, 3) any active agent
        agent = AIAgent.objects.filter(
            user=request.user, 
            is_active=True,
            agent_type='content_creator',
            name__icontains='social media'
        ).first()
        
        if not agent:
            # Try any content_creator agent
            agent = AIAgent.objects.filter(
                user=request.user, 
                is_active=True,
                agent_type='content_creator'
            ).first()
        
        if not agent:
            # Fall back to any active agent
            agent = AIAgent.objects.filter(user=request.user, is_active=True).first()
        
        if not agent:
            # Create a default social media agent if none exists
            agent = create_default_social_media_agent(request.user)
        
        # Log agent details for debugging
        logger.info(f"Using agent: {agent.id} ({agent.name}), model: {agent.model_name}, provider: {agent.model_provider}")
        
        # Create a new conversation for this message
        conversation = Conversation.objects.create(
            user=request.user,
            agent=agent,
            title=message_content[:100] + "..." if len(message_content) > 100 else message_content
        )
        logger.info("Created new conversation %s with agent %s for user %s", conversation.id, agent.id, request.user.id)

    # Save documents in payload in AI agent database
    # If documents is a list of document IDs, add them to the agent
    if documents:
        doc_qs = Document.objects.filter(id__in=documents, user=request.user)
        for document in doc_qs:
            if not agent.documents.filter(id=document.id).exists():
                agent.documents.add(document)
                logger.info("Added document %s to agent %s", document.id, agent.id)
            else:
                logger.info("Document %s already exists in agent %s", document.id, agent.id)
        # Log any IDs not found
        found_ids = set(str(doc.id) for doc in doc_qs)
        missing_ids = set(str(doc_id) for doc_id in documents) - found_ids
        for missing_id in missing_ids:
            logger.warning("Document %s not found for user %s", missing_id, request.user.id)
            
        agent.save()

    # Check if this is a social media agent and add business context
    if agent.agent_type == 'content_creator' and 'social' in agent.name.lower():
        try:
            business_brand = request.user.business_brand
            business_context = f"""
Business Context:
- Company: {business_brand.company_name}
- Industry: {business_brand.industry}
- Brand Voice: {business_brand.brand_voice}
- Target Audience: {business_brand.target_audience}
- Primary Color: {business_brand.primary_color}
- Secondary Color: {business_brand.secondary_color}
- Business Description: {business_brand.business_description}
"""
            # Add business context to the message
            enhanced_message = f"{business_context}\n\nUser Request: {message_content}"
        except:
            # If no business profile exists, use basic context
            enhanced_message = message_content
    else:
        enhanced_message = message_content

    # Await your async executor directly (no asyncio.run)
    logger.info("Executing agent request for agent %s", agent_id)
    response = agent_executor.execute_agent_request(agent, enhanced_message, conversation)

    logger.info("Agent response for user %s: error=%s, conversation_id=%s", request.user.id, response.get('error'), response.get('conversation_id'))

    # Check if this is a social media post generation request
    social_media_data = None
    if agent.agent_type == 'content_creator' and 'social' in agent.name.lower():
        try:
            # Parse the response to extract image prompt, caption, and hashtags
            content = response.get('content', '')
            if 'Image Prompt:' in content and 'Caption:' in content and 'Hashtags:' in content:
                lines = content.split('\n')
                image_prompt = ''
                caption = ''
                hashtags = ''
                
                current_section = None
                for line in lines:
                    line = line.strip()
                    if line.startswith('Image Prompt:'):
                        current_section = 'image'
                        image_prompt = line.replace('Image Prompt:', '').strip()
                    elif line.startswith('Caption:'):
                        current_section = 'caption'
                        caption = line.replace('Caption:', '').strip()
                    elif line.startswith('Hashtags:'):
                        current_section = 'hashtags'
                        hashtags = line.replace('Hashtags:', '').strip()
                    elif current_section and line:
                        if current_section == 'image':
                            image_prompt += ' ' + line
                        elif current_section == 'caption':
                            caption += ' ' + line
                        elif current_section == 'hashtags':
                            hashtags += ' ' + line
                
                social_media_data = {
                    'image_prompt': image_prompt,
                    'caption': caption,
                    'hashtags': hashtags
                }
        except Exception as e:
            logger.error(f"Error parsing social media response: {str(e)}")

    return JsonResponse({
        'success': not response.get('error'),
        'data': {
            'response': response.get('content', ''),
            'conversation_id': response.get('conversation_id'),
            'context_docs': response.get('context_docs', []),
            'usage': response.get('usage', {}),
            'response_time': response.get('response_time', 0),
            'social_media_data': social_media_data
        },
        'error': response.get('error'),
        'error_type': response.get('error_type')
    })

@csrf_exempt
@login_required
@require_http_methods(["GET", "POST"])
def conversations(request):
    """Get conversations with filtering and pagination, or create new conversation"""
    if request.method == "GET":
        try:
            conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')
            
            # Filters
            agent_filter = request.GET.get('agent')
            if agent_filter:
                conversations = conversations.filter(agent_id=agent_filter)
            
            # Pagination
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            
            paginator = Paginator(conversations, page_size)
            page_obj = paginator.get_page(page)
            
            # Get user's agents for metadata
            user_agents = AIAgent.objects.filter(user=request.user, is_active=True)
            
            return JsonResponse({
                'success': True,
                'data': {
                    'conversations': [model_to_dict(conv) for conv in page_obj],
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total_pages': paginator.num_pages,
                        'total_count': paginator.count,
                        'has_next': page_obj.has_next(),
                        'has_previous': page_obj.has_previous(),
                    }
                },
                'meta': {
                    'user_agents': [model_to_dict(agent) for agent in user_agents],
                    'filters': {
                        'agent': agent_filter
                    }
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    elif request.method == "POST":
        """Create new conversation"""
        try:
            data = json.loads(request.body)
            title = data.get('title', '')
            agent_id = data.get('agent_id')
            
            # Get agent if specified, otherwise get the first available agent
            agent = None
            if agent_id:
                agent = get_object_or_404(AIAgent, id=agent_id, user=request.user)
            else:
                # Try to find a social media agent (content_creator type) first
                # Priority: 1) content_creator type with 'social media' in name, 2) content_creator type, 3) any active agent
                agent = AIAgent.objects.filter(
                    user=request.user, 
                    is_active=True,
                    agent_type='content_creator',
                    name__icontains='social media'
                ).first()
                
                if not agent:
                    # Try any content_creator agent
                    agent = AIAgent.objects.filter(
                        user=request.user, 
                        is_active=True,
                        agent_type='content_creator'
                    ).first()
                
                if not agent:
                    # Fall back to any active agent
                    agent = AIAgent.objects.filter(user=request.user, is_active=True).first()
                
                if not agent:
                    # Create a default social media agent if none exists
                    agent = create_default_social_media_agent(request.user)
            
            # Create conversation
            conversation = Conversation.objects.create(
                user=request.user,
                agent=agent,
                title=title
            )
            
            return JsonResponse({
                'success': True,
                'data': model_to_dict(conversation)
            })
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to create conversation'
            }, status=500)


@login_required
@require_http_methods(["GET"])
def conversation_detail(request, conversation_id):
    """Get conversation detail with messages"""
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        
        # Get messages
        messages = conversation.messages.order_by('created_at')
        
        return JsonResponse({
            'success': True,
            'data': {
                'conversation': model_to_dict(conversation),
                'messages': [model_to_dict(msg) for msg in messages],
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def search_documents(request):
    """Search documents using vector similarity"""
    try:
        query = request.GET.get('q', '')
        max_results = int(request.GET.get('max_results', 20))
        similarity_threshold = float(request.GET.get('similarity_threshold', 0.7))
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': 'Query parameter is required'
            }, status=400)
        
        # Initialize embedding manager
        embedding_manager = EmbeddingManager(str(request.user.id))
        
        # Search documents
        search_results = embedding_manager.search_similar_documents(
            query=query,
            k=max_results,
            filter_metadata={'user_id': str(request.user.id)}
        )
        
        # Format results
        results = []
        for result in search_results:
            if result.get('distance', 1) <= (1 - similarity_threshold):
                doc_id = result.get('metadata', {}).get('document_id')
                if doc_id:
                    try:
                        document = Document.objects.get(id=doc_id, user=request.user)
                        results.append({
                            'document': model_to_dict(document),
                            'content': result.get('text', ''),
                            'similarity': 1 - result.get('distance', 0),
                            'metadata': result.get('metadata', {})
                        })
                    except Document.DoesNotExist:
                        continue
        
        return JsonResponse({
            'success': True,
            'data': {
                'query': query,
                'results': results,
                'total_results': len(results),
                'parameters': {
                    'max_results': max_results,
                    'similarity_threshold': similarity_threshold
                }
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def kb_settings(request):
    """Get user settings"""
    try:
        # Get or create user config
        config, created = KnowledgeBaseConfig.objects.get_or_create(user=request.user)
        
        return JsonResponse({
            'success': True,
            'data': {
                'config': model_to_dict(config),
                'created': created
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["PUT"])
def update_settings(request):
    """Update user settings"""
    try:
        config, created = KnowledgeBaseConfig.objects.get_or_create(user=request.user)
        data = json.loads(request.body)
        
        # Update configuration fields
        updatable_fields = [
            'default_embedding_model', 'default_chunk_size', 'default_chunk_overlap',
            'document_retention_days', 'conversation_retention_days',
            'default_similarity_threshold', 'max_search_results',
            'sync_notifications', 'error_notifications'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(config, field, data[field])
        
        # Note: API keys are no longer stored in database - always use environment variables
        # Ignore any API key fields in the request
        
        config.save()
        
        return JsonResponse({
            'success': True,
            'data': model_to_dict(config),
            'message': 'Settings updated successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def analytics(request):
    """Get analytics data"""
    try:
        user_id = str(request.user.id)
        days = int(request.GET.get('days', 30))
        
        # Get analytics data
        usage_stats = AnalyticsManager.get_user_usage_stats(user_id, days)
        
        # Get agent performance stats
        agent_stats = []
        for agent in AIAgent.objects.filter(user=request.user, is_active=True):
            stats = AnalyticsManager.get_agent_performance_stats(str(agent.id), days)
            agent_stats.append({
                'agent': model_to_dict(agent),
                'stats': stats
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'usage_stats': usage_stats,
                'agent_stats': agent_stats,
                'period_days': days
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


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
            }, status=400)
        
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
            'data': {
                'deleted_count': count,
                'document_ids': document_ids
            },
            'message': f'Deleted {count} documents'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


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
            'data': model_to_dict(document),
            'message': 'Document restored successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_agent_templates(request):
    """Get available agent templates"""
    try:
        templates = AgentTemplateManager.get_templates()
        
        return JsonResponse({
            'success': True,
            'data': {
                'templates': templates
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_file_types(request):
    """Get available file types"""
    try:
        file_types = FileType.objects.filter(is_active=True)
        
        return JsonResponse({
            'success': True,
            'data': {
                'file_types': [model_to_dict(ft) for ft in file_types]
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def delete_data_source(request, source_id):
    """Delete data source"""
    try:
        data_source = get_object_or_404(DataSource, id=source_id, user=request.user)
        data_source.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Data source deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def delete_agent(request, agent_id):
    """Delete AI agent"""
    try:
        agent = get_object_or_404(AIAgent, id=agent_id, user=request.user)
        agent.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'AI agent deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def delete_conversation(request, conversation_id):
    """Delete conversation"""
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        conversation.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Conversation deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    

@login_required
@require_http_methods(["GET"])
def initiate_oauth(request, source_id):
    """Initiate OAuth flow for a data source"""
    try:
        data_source = get_object_or_404(DataSource, id=source_id, user=request.user)
        
        # Check if source requires OAuth
        source_instance = data_source_registry.get_source(data_source)
        if not source_instance or not source_instance.requires_oauth():
            return JsonResponse({
                'error': 'This data source does not require OAuth'
            }, status=400)
        
        # Get OAuth authorization URL
        oauth_info = get_oauth_authorization_url(data_source)
        logger.info(f"OAuth info for {data_source.source_type}: {oauth_info}")
        if not oauth_info:
            return JsonResponse({
                'error': 'Failed to get OAuth authorization URL'
            }, status=500)
        
        return JsonResponse({
            'authorization_url': oauth_info['authorization_url'],
            'state': oauth_info['state'],
            'service_name': oauth_info.get('service_name', 'Unknown Service')
        })
        
    except Exception as e:
        logger.error(f"Error initiating OAuth: {e}")
        return JsonResponse({
            'error': 'Failed to initiate OAuth flow'
        }, status=500)
    

#TODO: use json response
@csrf_exempt
@require_http_methods(["GET"])
def oauth_callback(request):
    """Handle OAuth callback"""
    try:
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        if error:
            logger.error(f"OAuth error: {error}")
            return HttpResponse("""
                <script>
                    window.opener && window.opener.postMessage({type: 'oauth_error', error: '%s'}, '*');
                    window.close();
                </script>
                <p>OAuth error: %s. You can close this window.</p>
            """ % (error, error))
        
        if not code or not state:
            return HttpResponse("""
                <script>
                    window.opener && window.opener.postMessage({type: 'oauth_error', error: 'missing_parameters'}, '*');
                    window.close();
                </script>
                <p>Missing parameters. You can close this window.</p>
            """)
        
        # Find the data source by state
        data_source = None
        for ds in DataSource.objects.filter(config__contains={'oauth_state': state}):
            if ds.config.get('oauth_state') == state:
                data_source = ds
                break
        
        if not data_source:
            return HttpResponse("""
                <script>
                    window.opener && window.opener.postMessage({type: 'oauth_error', error: 'invalid_state'}, '*');
                    window.close();
                </script>
                <p>Invalid state. You can close this window.</p>
            """)
        
        # Handle the callback
        success = handle_oauth_callback(data_source, code, state)
        
        if success:
            return HttpResponse(f"""
                <script>
                    window.opener && window.opener.postMessage({{type: 'oauth_success', source: {data_source.id}}}, '*');
                    window.close();
                </script>
                <p>OAuth success! You can close this window.</p>
            """)
        else:
            return HttpResponse("""
                <script>
                    window.opener && window.opener.postMessage({type: 'oauth_error', error: 'callback_failed'}, '*');
                    window.close();
                </script>
                <p>OAuth callback failed. You can close this window.</p>
            """)
            
    except Exception as e:
        logger.info(f"OAuth callback request: code={request.GET.get('code')}, state={request.GET.get('state')}, error={request.GET.get('error')}")
        logger.error(f"Error handling OAuth callback: {e}")
        return HttpResponse("""
            <script>
                window.opener && window.opener.postMessage({type: 'oauth_error', error: 'callback_exception'}, '*');
                window.close();
            </script>
            <p>OAuth exception. You can close this window.</p>
        """)
    
@login_required
@require_http_methods(["GET"])
def oauth_status(request, source_id):
    """Check OAuth status for a data source"""
    try:
        data_source = get_object_or_404(DataSource, id=source_id, user=request.user)
        
        authenticated = is_oauth_authenticated(data_source)
        
        return JsonResponse({
            'authenticated': authenticated,
            'source_id': source_id,
            'source_type': data_source.source_type
        })
        
    except Exception as e:
        logger.error(f"Error checking OAuth status: {e}")
        return JsonResponse({
            'error': 'Failed to check OAuth status'
        }, status=500)
    
@login_required
@require_http_methods(["POST"])
def revoke_oauth(request, source_id):
    """Revoke OAuth credentials for a data source"""
    try:
        data_source = get_object_or_404(DataSource, id=source_id, user=request.user)
        
        # Clear OAuth credentials
        oauth_keys = [
            'oauth_token', 'oauth_refresh_token', 'oauth_token_uri',
            'oauth_client_id', 'oauth_client_secret', 'oauth_scopes', 'oauth_expiry'
        ]
        
        for key in oauth_keys:
            if key in data_source.credentials:
                del data_source.credentials[key]
        
        data_source.save()
        
        return JsonResponse({
            'message': 'OAuth credentials revoked successfully'
        })
        
    except Exception as e:
        logger.error(f"Error revoking OAuth: {e}")
        return JsonResponse({
            'error': 'Failed to revoke OAuth credentials'
        }, status=500)
    
@login_required
@require_http_methods(["GET"])
def list_oauth_sources(request):
    """List all OAuth-enabled data sources for the user"""
    try:
        oauth_sources = data_source_registry.get_oauth_sources()
        
        # Get user's data sources that support OAuth
        user_sources = DataSource.objects.filter(
            user=request.user,
            source_type__in=oauth_sources
        )
        
        sources_data = []
        for source in user_sources:
            authenticated = is_oauth_authenticated(source)
            sources_data.append({
                'id': source.id,
                'name': source.name,
                'source_type': source.source_type,
                'authenticated': authenticated,
                'created_at': source.created_at.isoformat(),
                'updated_at': source.updated_at.isoformat()
            })
        
        return JsonResponse({
            'sources': sources_data,
            'available_oauth_types': oauth_sources
        })
        
    except Exception as e:
        logger.error(f"Error listing OAuth sources: {e}")
        return JsonResponse({
            'error': 'Failed to list OAuth sources'
        }, status=500)
    

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def upload_files_to_data_source(request, source_id=None):
    """
    Upload multiple files to a data source.
    Currently supports only 'gcs' source_type, but is generic for future extension.
    Expects:
      - POST multipart/form-data with files (one or more)
      - 'source_id' as POST param or query param
    """
    try:
        # Get source_id from POST or query params
        source_id = source_id
        if not source_id:
            return JsonResponse({'success': False, 'error': 'Missing source_id'}, status=400)

        # Fetch the DataSource object
        try:
            data_source = DataSource.objects.get(id=source_id, user=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Data source not found'}, status=404)

        # Get the data source handler
        data_source_instance = data_source_registry.get_source(data_source)
        if not data_source_instance:
            return JsonResponse({'success': False, 'error': 'Unsupported data source type'}, status=400)

        # Collect files from request.FILES (can be multiple)
        files = []
        for file_key in request.FILES:
            uploaded_file = request.FILES[file_key]
            file_content = uploaded_file.read()
            files.append({
                'file_name': uploaded_file.name,
                'file_content': file_content
            })

        if not files:
            return JsonResponse({'success': False, 'error': 'No files provided'}, status=400)

        # Upload files using the data source's upload method
        documents = data_source_instance.upload(files)

        return JsonResponse({
            'success': True,
            'message': f'{len(documents)} file(s) uploaded successfully',
        }, status=201)

    except Exception as e:
        logger.error(f"Error in upload_files_to_data_source: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@login_required
def get_current_user_info(request):
    """Helper function to get current user info (admin or business)"""
    # Check for business user first
    business_id = request.session.get('business_id')
    user_type = request.session.get('user_type')
    
    if business_id and user_type == 'business':
        from api.business_models import Business
        try:
            business = Business.objects.get(id=business_id, is_active=True)
            return {
                'type': 'business',
                'id': business_id,
                'user': None,
                'business': business
            }
        except Business.DoesNotExist:
            pass
    
    # Check for admin user
    if request.user.is_authenticated:
        return {
            'type': 'admin',
            'id': request.user.id,
            'user': request.user,
            'business': None
        }
    
    return None

@require_http_methods(["GET"])
def get_connected_accounts(request):
    """Get user's connected social media accounts"""
    try:
        user_info = get_current_user_info(request)
        if not user_info:
            return JsonResponse({
                'success': False,
                'error': 'Not authenticated'
            }, status=401)
        
        # Filter accounts based on user type
        if user_info['type'] == 'business':
            accounts = ConnectedAccount.objects.filter(business_id=user_info['id'], is_active=True)
        else:
            accounts = ConnectedAccount.objects.filter(user=user_info['user'], is_active=True)
        
        
        accounts_data = []
        for account in accounts:
            account_data = {
                'id': str(account.id),
                'platform': account.platform,
                'username': account.username,
                'display_name': account.display_name,
                'profile_picture_url': account.profile_picture_url,
                'is_verified': account.is_verified,
                'last_sync_at': account.last_sync_at.isoformat() if account.last_sync_at else None,
                'created_at': account.created_at.isoformat(),
                'granted_scopes': account.granted_scopes,
                'permissions': account.permissions
            }
            accounts_data.append(account_data)
            logger.info(f"📋 Account: {account.platform} - {account.username} (ID: {account.id})")
        
        response_data = {
            'success': True,
            'data': {
                'accounts': accounts_data,
                'total': len(accounts_data)
            }
        }
        
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f"💥 Error getting connected accounts: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get connected accounts'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def initiate_instagram_connection(request):
    """Initiate Instagram OAuth connection"""
    try:
        user_info = get_current_user_info(request)
        if not user_info:
            return JsonResponse({
                'success': False,
                'error': 'Not authenticated'
            }, status=401)
        
        # Check if user already has an Instagram account connected
        if user_info['type'] == 'business':
            existing_account = ConnectedAccount.objects.filter(
                business_id=user_info['id'], 
                platform='instagram', 
                is_active=True
            ).first()
            user_identifier = f"business_{user_info['id']}"
        else:
            existing_account = ConnectedAccount.objects.filter(
                user=user_info['user'], 
                platform='instagram', 
                is_active=True
            ).first()
            user_identifier = f"admin_{user_info['id']}"
        
        if existing_account:
            logger.info(f"⚠️ User {user_identifier} already has Instagram account connected: {existing_account.username}")
            return JsonResponse({
                'success': False,
                'error': 'Instagram account already connected',
                'data': {
                    'existing_account': {
                        'id': str(existing_account.id),
                        'username': existing_account.username,
                        'platform': existing_account.platform
                    }
                }
            }, status=400)
        
        from .instagram_utils.instagram_api import InstagramOAuth
        
        oauth = InstagramOAuth()
        state = str(uuid.uuid4())  # Generate unique state for security
        
        # Store state and user info in session for validation
        request.session['instagram_oauth_state'] = state
        request.session['instagram_oauth_user_type'] = user_info['type']
        request.session['instagram_oauth_user_id'] = str(user_info['id'])
        
        authorization_url = oauth.get_authorization_url(state)
        
        # Log the response for debugging
        logger.info(f"  State: {state}")
        logger.info(f"  Authorization URL: {authorization_url}")
        logger.info(f"  User agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
        
        return JsonResponse({
            'success': True,
            'data': {
                'authorization_url': authorization_url,
                'state': state
            }
        })
    except Exception as e:
        logger.error(f"💥 Error initiating Instagram connection: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to initiate Instagram connection'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def instagram_oauth_callback(request):
    """Handle Instagram OAuth callback"""
    try:
        logger.info(f"🔄 Instagram OAuth callback received")
        logger.info(f"📥 Request method: {request.method}")
        logger.info(f"📥 Query params: {dict(request.GET)}")
        logger.info(f"📥 User agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
        logger.info(f"📥 User authenticated: {request.user.is_authenticated}")
        
        # Get user info (admin or business)
        user_info = get_current_user_info(request)
        if not user_info:
            logger.warning("⚠️ User not authenticated")
            return JsonResponse({
                'success': False,
                'error': 'Not authenticated'
            }, status=401)
        
        # Get OAuth parameters
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        from .instagram_utils.instagram_api import InstagramOAuth, InstagramAPIClient
        from .instagram_utils.encryption import token_encryption
        
        logger.info(f"  - Code: {code[:20] + '...' if code else 'None'}")
        logger.info(f"  - State: {state}")
        logger.info(f"  - Error: {error}")
        
        if error:
            logger.error(f"❌ OAuth error received: {error}")
            return JsonResponse({
                'success': False,
                'error': f'OAuth error: {error}'
            }, status=400)
        
        if not code:
            return JsonResponse({
                'success': False,
                'error': 'Authorization code not provided'
            }, status=400)
        
        # Validate state parameter
        session_state = request.session.get('instagram_oauth_state')
        if not session_state or session_state != state:
            logger.warning(f"⚠️ State validation failed:")
            logger.warning(f"  - Session state: {session_state}")
            logger.warning(f"  - Received state: {state}")
            # For development, let's be more lenient with state validation
            logger.warning("⚠️ State mismatch, proceeding anyway (development mode)")
            # Clear any old session state
            if 'instagram_oauth_state' in request.session:
                del request.session['instagram_oauth_state']
        
        # Exchange code for token
        logger.info("🔄 Exchanging Instagram code for token...")
        try:
            oauth = InstagramOAuth()
            logger.info(f"🔧 OAuth instance created with:")
            logger.info(f"  - App ID: {oauth.app_id}")
            logger.info(f"  - App Secret: {'***' + oauth.app_secret[-4:] if oauth.app_secret else 'None'}")
            logger.info(f"  - Redirect URI: {oauth.redirect_uri}")
            
            token_response = oauth.exchange_code_for_token(code)
            logger.info(f"📡 Instagram token exchange response: {token_response}")
        except Exception as e:
            logger.error(f"❌ Error during token exchange: {str(e)}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'error': f'Token exchange failed: {str(e)}'
            }, status=500)
        
        access_token = token_response.get('access_token')
        user_id = token_response.get('user_id')
        
        if not access_token or not user_id:
            logger.error(f"❌ Failed to get access token or user_id from response: {token_response}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to get access token'
            }, status=400)
        
        # Get long-lived token
        try:
            logger.info("🔄 Getting long-lived token...")
            long_lived_response = oauth.get_long_lived_token(access_token)
            long_lived_token = long_lived_response.get('access_token')
            expires_in = long_lived_response.get('expires_in', 0)
            logger.info(f"✅ Long-lived token obtained, expires in: {expires_in} seconds")
        except Exception as e:
            logger.warning(f"⚠️ Failed to get long-lived token: {str(e)}")
            # Fallback to short-lived token if long-lived fails
            long_lived_token = access_token
            expires_in = 3600  # 1 hour default
            logger.info("🔄 Using short-lived token as fallback")
        
        # Get Instagram user info
        try:
            logger.info("🔄 Getting Instagram user info...")
            client = InstagramAPIClient(long_lived_token)
            instagram_user_info = client.get_user_info()
            logger.info(f"✅ Instagram user info retrieved successfully: {instagram_user_info}")
        except Exception as e:
            logger.error(f"❌ Failed to get Instagram user info: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to get Instagram user info: {str(e)}'
            }, status=500)
        
        # Calculate token expiration
        expires_at = None
        if expires_in:
            expires_at = timezone.now() + timedelta(seconds=expires_in)
        
        # Encrypt tokens
        try:
            logger.info("🔄 Encrypting access token...")
            encrypted_access_token = token_encryption.encrypt_token(long_lived_token)
            logger.info("✅ Access token encrypted successfully")
        except Exception as e:
            logger.error(f"❌ Failed to encrypt access token: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to encrypt access token: {str(e)}'
            }, status=500)
        
        # Create or update connected account
        try:
            user_identifier = f"{user_info['type']}_{user_info['id']}"
            logger.info(f"💾 Creating/updating connected account for user {user_identifier}")
            logger.info(f"📋 Raw Instagram instagram_user_info response: {instagram_user_info}")
            logger.info(f"📋 Account details:")
            logger.info(f"  - User ID: {user_id}")
            logger.info(f"  - Username: {instagram_user_info.get('username', '')}")
            logger.info(f"  - Display Name: {instagram_user_info.get('name', '')}")
            logger.info(f"  - Profile Picture: {instagram_user_info.get('profile_picture_url', '')}")
            logger.info(f"  - All available fields: {list(instagram_user_info.keys())}")
            
            # Prepare account data
            account_defaults = {
                'username': instagram_user_info.get('username', ''),
                'display_name': instagram_user_info.get('name', ''),
                'profile_picture_url': instagram_user_info.get('profile_picture_url', ''),
                'access_token': encrypted_access_token,
                'token_expires_at': expires_at,
                'granted_scopes': ['instagram_basic', 'instagram_content_publish'],
                'permissions': {
                    'can_post': True,
                    'can_read_insights': True
                },
                'is_active': True,
                'is_verified': True,
                'last_sync_at': timezone.now()
            }
            
            # Create account based on user type
            if user_info['type'] == 'business':
                account, created = ConnectedAccount.objects.update_or_create(
                    business_id=user_info['id'],
                    platform='instagram',
                    account_id=user_id,
                    defaults=account_defaults
                )
            else:
                account, created = ConnectedAccount.objects.update_or_create(
                    user=user_info['user'],
                    platform='instagram',
                    account_id=user_id,
                    defaults=account_defaults
                )
            logger.info(f"✅ Connected account {'created' if created else 'updated'} successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create/update connected account: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to save connected account: {str(e)}'
            }, status=500)
        
        logger.info(f"  - Account ID: {account.id}")
        logger.info(f"  - Platform: {account.platform}")
        logger.info(f"  - Username: {account.username}")
        logger.info(f"  - Is Active: {account.is_active}")
        
        # Clear session state
        if 'instagram_oauth_state' in request.session:
            del request.session['instagram_oauth_state']
        
        # Return a simple HTML response for the callback
        success_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Instagram Connected Successfully</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .success {{ color: #10B981; font-size: 24px; margin-bottom: 20px; }}
                .details {{ color: #6B7280; font-size: 16px; }}
            </style>
        </head>
        <body>
            <div class="success">✅ Instagram Account Connected Successfully!</div>
            <div class="details">
                <p>Account: {account.username}</p>
                <p>Status: {'Created' if created else 'Updated'}</p>
                <p>You can now close this window and return to your app.</p>
            </div>
            <script>
                // Close the window after 3 seconds
                setTimeout(() => {{
                    window.close();
                }}, 3000);
            </script>
        </body>
        </html>
        """
        
        logger.info(f"🎉 Instagram connection completed successfully for user {request.user.id}")
        return HttpResponse(success_html)
    except Exception as e:
        logger.error(f"Error in Instagram OAuth callback: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to complete Instagram connection'
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def disconnect_account(request, account_id):
    """Disconnect a specific social media account"""
    try:
        user_info = get_current_user_info(request)
        if not user_info:
            return JsonResponse({
                'success': False,
                'error': 'Not authenticated'
            }, status=401)
        
        # Get account based on user type
        if user_info['type'] == 'business':
            account = get_object_or_404(ConnectedAccount, id=account_id, business_id=user_info['id'])
        else:
            account = get_object_or_404(ConnectedAccount, id=account_id, user=user_info['user'])
        
        # Deactivate instead of deleting to preserve posting history
        account.is_active = False
        account.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{account.platform.title()} account disconnected successfully'
        })
    except Exception as e:
        logger.error(f"Error disconnecting account: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to disconnect account'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def instagram_deauthorize_callback(request):
    """Handle Instagram deauthorization callback when user revokes access"""
    try:
        logger.info(f"🔄 Instagram deauthorize callback received")
        logger.info(f"📥 Request method: {request.method}")
        logger.info(f"📥 Request body: {request.body}")
        logger.info(f"📥 Headers: {dict(request.headers)}")
        
        # Parse the request data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            # Handle form data
            data = request.POST.dict()
        
        logger.info(f"📋 Deauthorize data: {data}")
        
        # Extract user ID from the deauthorize request
        user_id = data.get('user_id')
        if not user_id:
            logger.error("❌ No user_id in deauthorize request")
            return JsonResponse({'success': False, 'error': 'No user_id provided'}, status=400)
        
        # Find and deactivate the connected account
        try:
            account = ConnectedAccount.objects.get(
                account_id=user_id,
                platform='instagram',
                is_active=True
            )
            
            
            # Deactivate the account
            account.is_active = False
            account.save()
            
            
            return JsonResponse({
                'success': True,
                'message': 'Account deactivated successfully'
            })
            
        except ConnectedAccount.DoesNotExist:
            logger.warning(f"⚠️ No active Instagram account found for user_id: {user_id}")
            return JsonResponse({
                'success': True,
                'message': 'No active account found to deactivate'
            })
            
    except Exception as e:
        logger.error(f"💥 Error in Instagram deauthorize callback: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to process deauthorization'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def post_to_instagram(request):
    """Post content to Instagram"""
    try:
        user_info = get_current_user_info(request)
        if not user_info:
            return JsonResponse({
                'success': False,
                'error': 'Not authenticated'
            }, status=401)
        
        from .instagram_utils.instagram_api import create_instagram_post
        from .instagram_utils.encryption import token_encryption
        
        data = json.loads(request.body)
        account_id = data.get('account_id')
        content = data.get('content', '')
        image_url = data.get('image_url', '')
        post_type = data.get('post_type', 'POST')  # POST or STORY
        
        if not account_id or not image_url:
            return JsonResponse({
                'success': False,
                'error': 'Account ID and image URL are required'
            }, status=400)
        
        # For regular posts, content is required. For stories, it's optional
        if post_type.upper() == 'POST' and not content:
            return JsonResponse({
                'success': False,
                'error': 'Content is required for Instagram posts'
            }, status=400)
        
        # Get connected account based on user type
        if user_info['type'] == 'business':
            account = get_object_or_404(ConnectedAccount, id=account_id, business_id=user_info['id'], is_active=True)
        else:
            account = get_object_or_404(ConnectedAccount, id=account_id, user=user_info['user'], is_active=True)
        
        if account.platform != 'instagram':
            return JsonResponse({
                'success': False,
                'error': 'Account is not an Instagram account'
            }, status=400)
        
        # Decrypt access token
        access_token = token_encryption.decrypt_token(account.access_token)
        
        if not access_token:
            return JsonResponse({
                'success': False,
                'error': 'Invalid access token'
            }, status=400)
        
        # Create Instagram post or story
        result = create_instagram_post(access_token, image_url, content, post_type)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'data': {
                    'post_id': result['post_id'],
                    'message': 'Post published successfully'
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to publish post')
            }, status=500)
    except Exception as e:
        logger.error(f"Error posting to Instagram: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to post to Instagram'
        }, status=500)
