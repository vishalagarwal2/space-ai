
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json
import uuid

class UserGoogleOAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='google_oauth')
    credentials = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class DataSource(models.Model):
    """Configurable data sources that can be plugged into the knowledge base"""
    
    SOURCE_TYPES = [
        ('gmail', 'Gmail'),
        ('google_drive', 'Google Drive'),
        ('salesforce', 'Salesforce'),
        ('file_upload', 'File Upload'),
        ('web_scraping', 'Web Scraping'),
        ('api', 'API Integration'),
        ('database', 'Database'),
        ('slack', 'Slack'),
        ('notion', 'Notion'),
        ('confluence', 'Confluence'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('syncing', 'Syncing'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_sources')
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Configuration for the data source
    config = models.JSONField(default=dict, help_text="Configuration specific to the data source type")
    
    # Authentication/credentials (encrypted)
    credentials = models.JSONField(default=dict, help_text="Encrypted credentials for the data source")
    
    # Sync settings
    auto_sync = models.BooleanField(default=True)
    sync_frequency = models.IntegerField(default=24, help_text="Sync frequency in hours")
    last_sync = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'name']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.source_type}) - {self.user.username}"


class FileType(models.Model):
    """Configurable file types and their processing rules"""
    
    CATEGORY_CHOICES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('code', 'Code'),
        ('data', 'Data'),
        ('archive', 'Archive'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    mime_types = models.JSONField(default=list, help_text="List of MIME types for this file type")
    extensions = models.JSONField(default=list, help_text="List of file extensions")
    
    # Processing configuration
    parsers = models.JSONField(default=list, help_text="List of parser classes to use")
    embedding_models = models.JSONField(default=list, help_text="List of embedding models to use")
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class Document(models.Model):
    """Documents from various data sources"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('error', 'Error'),
        ('soft_deleted', 'Soft Deleted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    file_type = models.ForeignKey(FileType, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Document metadata
    title = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255, blank=True)
    file_path = models.CharField(max_length=1000, blank=True)
    file_size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    
    # Content
    raw_content = models.TextField(blank=True)
    processed_content = models.TextField(blank=True)
    
    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processing_log = models.JSONField(default=list, help_text="Log of processing steps")
    
    # Metadata from source
    source_metadata = models.JSONField(default=dict, help_text="Metadata from the original source")
    
    # Expiry and lifecycle
    expires_at = models.DateTimeField(null=True, blank=True)
    soft_deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    needs_processing = models.BooleanField(default=True, help_text="Whether this document needs to be processed")
    processing_started_at = models.DateTimeField(null=True, blank=True, help_text="When processing started")

    # Add these helper methods
    def mark_processing_started(self):
        """Safely mark processing as started without triggering processing signals"""
        self.status = 'processing'
        self.needs_processing = False
        self.processing_started_at = timezone.now()
        self.processing_log.append({
            'timestamp': timezone.now().isoformat(),
            'step': 'processing_started',
            'message': 'Document processing started'
        })
        # CRITICAL: Using update_fields prevents signal from triggering
        self.save(update_fields=['status', 'needs_processing', 'processing_started_at', 'processing_log'])
    
    def mark_processed(self, content, log_entry=None):
        """Safely mark as processed without triggering processing signals"""
        self.status = 'processed'
        self.processed_content = content
        self.needs_processing = False  # No longer needs processing
        
        if log_entry:
            self.processing_log.append(log_entry)
        
        # CRITICAL: Using update_fields prevents signal from triggering
        self.save(update_fields=['status', 'processed_content', 'needs_processing', 'processing_log'])

    def mark_parsing_complete(self):
        """Safely mark as processed without triggering processing signals"""

        self.processing_log.append({
            'timestamp': timezone.now().isoformat(),
            'step': 'parsing_complete',
            'message': 'Document parsing completed'
        })
        
        # CRITICAL: Using update_fields prevents signal from triggering
        self.save(update_fields=['status', 'processing_log'])
    
    def mark_error(self, error_message, log_entry=None):
        """Safely mark as error"""
        self.status = 'error'
        self.needs_processing = True  # Allow retry
        
        if log_entry:
            self.processing_log.append(log_entry)
        
        # CRITICAL: Using update_fields prevents signal from triggering
        self.save(update_fields=['status', 'needs_processing', 'processing_log'])
    
    def reset_for_reprocessing(self):
        """Mark document to be reprocessed (useful for re-embedding existing docs)"""
        self.needs_processing = True
        self.processing_started_at = None
        self.save(update_fields=['needs_processing', 'processing_started_at'])
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['data_source', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def soft_delete(self):
        """Soft delete the document"""
        self.status = 'soft_deleted'
        self.soft_deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        """Restore a soft-deleted document"""
        if self.status == 'soft_deleted':
            self.status = 'processed'
            self.soft_deleted_at = None
            self.save()


# TODO: check if this can be used in code, its not being used anywhere
class DocumentChunk(models.Model):
    """Chunks of documents for vector storage"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    
    # Chunk content
    content = models.TextField()
    chunk_index = models.IntegerField(default=0)
    
    # Embeddings (stored as JSON for flexibility)
    embeddings = models.JSONField(default=dict, help_text="Embeddings from different models")
    
    # Metadata
    metadata = models.JSONField(default=dict, help_text="Additional metadata for the chunk")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['document', 'chunk_index']
        ordering = ['document', 'chunk_index']
    
    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title}"


class AIAgent(models.Model):
    """Configurable AI agents with different capabilities"""
    
    AGENT_TYPES = [
        ('generic', 'Generic Assistant'),
        ('domain_specific', 'Domain Specific'),
        ('code_assistant', 'Code Assistant'),
        ('data_analyst', 'Data Analyst'),
        ('content_creator', 'Content Creator'),
        ('customer_support', 'Customer Support'),
        ('research_assistant', 'Research Assistant'),
        ('custom', 'Custom'),
    ]
    
    CONVERSATION_MODES = [
        ('stateless', 'Stateless'),
        ('session', 'Session Based'),
        ('persistent', 'Persistent Memory'),
        ('contextual', 'Contextual Memory'),
    ]
    
    MODEL_PROVIDERS = [
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('cohere', 'Cohere'),
        ('huggingface', 'HuggingFace'),
        ('local', 'Local Model'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_agents')
    
    # Basic configuration
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    agent_type = models.CharField(max_length=50, choices=AGENT_TYPES)
    
    # Model configuration
    model_provider = models.CharField(max_length=50, choices=MODEL_PROVIDERS, default='openai')
    model_name = models.CharField(max_length=100, default='gpt-3.5-turbo')
    model_parameters = models.JSONField(default=dict, help_text="Model-specific parameters")
    
    # Conversation settings
    conversation_mode = models.CharField(max_length=20, choices=CONVERSATION_MODES, default='session')
    context_window = models.IntegerField(default=4000, help_text="Maximum context window size")
    memory_retention_days = models.IntegerField(default=30, help_text="Days to retain conversation memory")
    
    # Prompts and instructions
    system_prompt = models.TextField(help_text="System prompt for the agent")
    user_prompt_template = models.TextField(blank=True, help_text="Template for user prompts")
    
    # Knowledge base configuration
    data_sources = models.ManyToManyField(DataSource, blank=True, help_text="Data sources to use")
    file_types = models.ManyToManyField(FileType, blank=True, help_text="File types to include")
    documents = models.ManyToManyField(Document, blank=True, help_text="Documents to use")
    
    # Search and retrieval settings
    max_documents = models.IntegerField(default=10, help_text="Maximum documents to retrieve")
    similarity_threshold = models.FloatField(default=0.7, validators=[MinValueValidator(0), MaxValueValidator(1)])
    
    # Rate limiting
    rate_limit_per_hour = models.IntegerField(default=100)
    rate_limit_per_day = models.IntegerField(default=1000)
    
    # Domain-specific settings
    domain_keywords = models.JSONField(default=list, help_text="Keywords for domain-specific agents")
    expertise_areas = models.JSONField(default=list, help_text="Areas of expertise")
    
    # Status and metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'name']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.agent_type}) - {self.user.username}"


class Conversation(models.Model):
    """Conversations between users and AI agents"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name='conversations')
    
    title = models.CharField(max_length=255, blank=True)
    
    # Context and memory
    context = models.JSONField(default=dict, help_text="Conversation context and memory")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation with {self.agent.name} - {self.user.username}"


class Message(models.Model):
    """Messages in conversations"""
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    
    # Metadata
    metadata = models.JSONField(default=dict, help_text="Additional message metadata")
    
    # Citations and sources
    cited_documents = models.ManyToManyField(Document, blank=True, help_text="Documents cited in this message")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class AgentUsage(models.Model):
    """Track usage of AI agents"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_usage')
    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name='usage_logs')
    
    # Usage metrics
    tokens_used = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    response_time = models.FloatField(default=0, help_text="Response time in seconds")
    
    # Request details
    request_data = models.JSONField(default=dict, help_text="Request metadata")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['agent', 'created_at']),
        ]


class KnowledgeBaseConfig(models.Model):
    """User-specific configuration for the knowledge base"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kb_config')
    
    # General settings
    default_embedding_model = models.CharField(max_length=100, default='sentence-transformers')
    default_vector_store = models.CharField(max_length=100, default='chroma')
    default_chunk_size = models.IntegerField(default=1000)
    default_chunk_overlap = models.IntegerField(default=200)
    
    # Retention settings
    document_retention_days = models.IntegerField(default=365, help_text="Days to keep documents")
    conversation_retention_days = models.IntegerField(default=90, help_text="Days to keep conversations")
    
    # Search settings
    default_similarity_threshold = models.FloatField(default=0.7, validators=[MinValueValidator(0), MaxValueValidator(1)])
    max_search_results = models.IntegerField(default=20)
    
    # Notification settings
    sync_notifications = models.BooleanField(default=True)
    error_notifications = models.BooleanField(default=True)
    
    # Note: API keys are now always read from environment variables
    # No user-provided API keys are stored in the database
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Config for {self.user.username}"


class ConnectedAccount(models.Model):
    """Connected social media accounts for users"""
    
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Support both admin users (Django User) and business users (Business model)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connected_accounts', null=True, blank=True)
    business_id = models.UUIDField(null=True, blank=True, help_text="Business user ID for business-connected accounts")
    
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    
    # Account Information
    account_id = models.CharField(max_length=255, help_text="Platform-specific account ID")
    username = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True)
    profile_picture_url = models.URLField(max_length=1000, blank=True)
    
    # Authentication Tokens (Encrypted)
    access_token = models.TextField(help_text="Encrypted access token")
    refresh_token = models.TextField(blank=True, help_text="Encrypted refresh token")
    token_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Permissions & Scopes
    granted_scopes = models.JSONField(default=list, help_text="OAuth scopes granted")
    permissions = models.JSONField(default=dict, help_text="Platform-specific permissions")
    
    # Status & Metadata
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'knowledge_base_connected_account'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(business_id__isnull=False),
                name='connected_account_user_or_business_required'
            ),
            models.UniqueConstraint(
                fields=['user', 'platform', 'account_id'],
                condition=models.Q(user__isnull=False),
                name='unique_user_platform_account'
            ),
            models.UniqueConstraint(
                fields=['business_id', 'platform', 'account_id'],
                condition=models.Q(business_id__isnull=False),
                name='unique_business_platform_account'
            )
        ]
    
    def __str__(self):
        if self.user:
            return f"{self.platform.title()} - {self.username} (Admin: {self.user.username})"
        else:
            return f"{self.platform.title()} - {self.username} (Business: {self.business_id})"
    
    @property
    def owner_identifier(self):
        """Get a unique identifier for the account owner"""
        return f"user_{self.user.id}" if self.user else f"business_{self.business_id}"


    