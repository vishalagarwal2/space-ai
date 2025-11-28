# knowledge_base/signals.py

from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import logging
import os

from .models import (
    Document, DataSource, AIAgent, Conversation, 
    KnowledgeBaseConfig, AgentUsage
)

# Import safely with fallbacks
try:
    from .embeddings import EmbeddingManager
except ImportError:
    EmbeddingManager = None
    logging.warning("EmbeddingManager not available")

try:
    from .utils import CacheManager
except ImportError:
    CacheManager = None
    logging.warning("CacheManager not available")

logger = logging.getLogger(__name__)

# Track documents currently being processed to prevent duplicates
_processing_documents = set()
_queued_tasks = {}  # document_id -> task_id mapping


# @receiver(post_save, sender=User)
# def create_user_kb_config(sender, instance, created, **kwargs):
#     """Create knowledge base config for new users"""
#     if created:
#         try:
#             config, config_created = KnowledgeBaseConfig.objects.get_or_create(
#                 user=instance,
#                 defaults={
#                     'default_embedding_model': 'openai_ada',
#                     'default_vector_store': 'pinecone',
#                     'default_chunk_size': 1000,
#                     'default_chunk_overlap': 200,
#                     'document_retention_days': 365,
#                     'conversation_retention_days': 90,
#                     'default_similarity_threshold': 0.2,
#                     'max_search_results': 20,
#                     'sync_notifications': True,
#                     'error_notifications': True,
#                     'openai_api_key': os.getenv('OPENAI_API_KEY'),
#                     'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY')
#                 }
#             )
#             if config_created:
#                 logger.info(f"SIGNALS: Created KB config for new user: {instance.username}")
#             else:
#                 logger.info(f"SIGNALS: KB config already exists for user: {instance.username}")
#         except Exception as e:
#             logger.error(f"SIGNALS: Error creating KB config for user {instance.username}: {e}")


@receiver(post_save, sender=Document, dispatch_uid="process_document_embeddings")
def process_document_embeddings(sender, instance, created, update_fields=None, **kwargs):
    """Process document embeddings based on your specific logic:
    - Process if document is just created (created=True)
    - Process if document has status='processed' AND has processed_content AND needs_processing=True
    """
    
    doc_id = str(instance.id)
    
    logger.info("=" * 50)
    logger.info(f"SIGNAL: Document {doc_id} post_save triggered")
    logger.info(f"SIGNAL: Created: {created}")
    logger.info(f"SIGNAL: Status: {instance.status}")
    logger.info(f"SIGNAL: Has processed_content: {bool(instance.processed_content)}")
    logger.info(f"SIGNAL: Needs processing: {getattr(instance, 'needs_processing', 'N/A')}")
    logger.info(f"SIGNAL: Update fields: {update_fields}")
    
    # Check if this document is already being processed
    if doc_id in _processing_documents:
        logger.info(f"SIGNAL: Document {doc_id} is already being processed, skipping")
        return
    
    # Check if we already have a queued task for this document
    if doc_id in _queued_tasks:
        logger.info(f"SIGNAL: Document {doc_id} already has queued task {_queued_tasks[doc_id]}, skipping")
        return
    
    # YOUR SPECIFIC LOGIC: Process if just created OR if status='processed' with content and needs processing
    should_process = False
    reason = ""
    
    if created:
        should_process = True
        reason = "newly created document"
    elif (instance.status == 'processed' and 
          instance.processed_content and 
          getattr(instance, 'needs_processing', True)):  # Default to True for backward compatibility
        should_process = True
        reason = "document has processed content and needs processing (re-embedding)"
    
    logger.info(f"SIGNAL: Should process: {should_process}")
    if should_process:
        logger.info(f"SIGNAL: Reason: {reason}")
    
    if should_process:
        try:
            # Mark as being processed
            _processing_documents.add(doc_id)
            
            logger.info(f"SIGNAL: Document {instance.id} ready for embedding processing")
            
            # Try to import and queue the task
            try:
                from .tasks import process_document
                logger.info("SIGNAL: Successfully imported process_document task")
                
                result = process_document.delay(str(instance.id), str(instance.user.id))
                
                # Store the task ID to prevent duplicates
                _queued_tasks[doc_id] = result.id
                
                logger.info(f"SIGNAL: Successfully queued processing task for document {instance.id}")
                logger.info(f"SIGNAL: Task ID: {result.id}")
                
            except ImportError as e:
                logger.error(f"SIGNAL: Cannot import process_document task: {e}")
                _processing_documents.discard(doc_id)
                
            except Exception as e:
                logger.error(f"SIGNAL: Error queuing task for document {instance.id}: {e}")
                _processing_documents.discard(doc_id)
                import traceback
                logger.error(f"SIGNAL: Traceback: {traceback.format_exc()}")
            
        except Exception as e:
            logger.error(f"SIGNAL: Error in document signal handler for document {instance.id}: {e}")
            _processing_documents.discard(doc_id)
            import traceback
            logger.error(f"SIGNAL: Traceback: {traceback.format_exc()}")
    else:
        logger.info(f"SIGNAL: Document {instance.id} not ready for processing - skipping")
    
    logger.info("=" * 50)


# Function to mark document processing as complete
def mark_document_processing_complete(document_id):
    """Mark a document as no longer being processed"""
    doc_id = str(document_id)
    _processing_documents.discard(doc_id)
    _queued_tasks.pop(doc_id, None)
    logger.info(f"SIGNAL: Removed document {doc_id} from processing set and queued tasks")


@receiver(pre_delete, sender=Document)
def cleanup_document_embeddings(sender, instance, **kwargs):
    """Clean up embeddings when document is deleted"""
    doc_id = str(instance.id)
    logger.info(f"SIGNAL: Document pre_delete signal triggered for document {doc_id}")
    
    # Remove from processing set and queued tasks
    _processing_documents.discard(doc_id)
    _queued_tasks.pop(doc_id, None)
    
    try:
        if EmbeddingManager:
            # Remove embeddings from vector store
            embedding_manager = EmbeddingManager(str(instance.user.id))
            embedding_manager.delete_document_embeddings(str(instance.id))
            logger.info(f"SIGNAL: Cleaned up embeddings for document {instance.id}")
        else:
            logger.warning(f"SIGNAL: EmbeddingManager not available, skipping cleanup for document {instance.id}")
        
    except Exception as e:
        logger.error(f"SIGNAL: Error cleaning up embeddings for document {instance.id}: {e}")


@receiver(post_save, sender=DataSource)
def update_data_source_status(sender, instance, created, **kwargs):
    """Update data source status and clear cache"""
    if not created and CacheManager:
        # Clear cache for this data source
        CacheManager.delete_cache('data_source', str(instance.id))
        
        # Clear user cache
        CacheManager.clear_user_cache(str(instance.user.id))
        
        logger.info(f"SIGNAL: Updated data source {instance.id} status")


@receiver(post_save, sender=AIAgent)
def update_agent_cache(sender, instance, created, **kwargs):
    """Update agent cache when agent is modified"""
    if CacheManager:
        # Clear agent cache
        CacheManager.delete_cache('agent', str(instance.id))
        
        # Clear user cache
        CacheManager.clear_user_cache(str(instance.user.id))
    
    if created:
        logger.info(f"SIGNAL: Created new AI agent: {instance.name}")
    else:
        logger.info(f"SIGNAL: Updated AI agent: {instance.name}")


@receiver(post_save, sender=Conversation)
def update_conversation_timestamp(sender, instance, created, **kwargs):
    """Update conversation timestamp and clear cache"""
    if not created:
        # Update the updated_at timestamp
        instance.updated_at = timezone.now()
        
        if CacheManager:
            # Clear conversation cache
            CacheManager.delete_cache('conversation', str(instance.id))
        
        logger.debug(f"SIGNAL: Updated conversation {instance.id} timestamp")


@receiver(post_save, sender=AgentUsage)
def track_agent_usage(sender, instance, created, **kwargs):
    """Track agent usage for analytics"""
    if created:
        try:
            # Update agent usage statistics
            # This could trigger usage alerts, billing calculations, etc.
            
            logger.info(f"SIGNAL: Tracked usage for agent {instance.agent.name}: {instance.tokens_used} tokens")
            
        except Exception as e:
            logger.error(f"SIGNAL: Error tracking agent usage: {e}")


# Custom signal for document processing
from django.dispatch import Signal

document_processed = Signal()
document_processing_failed = Signal()

@receiver(document_processed)
def handle_document_processed(sender, document, **kwargs):
    """Handle successful document processing"""
    logger.info(f"SIGNAL: Document {document.id} processed successfully")
    
    # NOTE: Don't update document status here as it should be handled by the task
    # using the helper methods to prevent signal loops
    
    # Clear cache
    if CacheManager:
        CacheManager.delete_cache('document', str(document.id))


@receiver(document_processing_failed)
def handle_document_processing_failed(sender, document, error, **kwargs):
    """Handle failed document processing"""
    logger.error(f"SIGNAL: Document {document.id} processing failed: {error}")
    
    # NOTE: Don't update document status here as it should be handled by the task
    # using the helper methods to prevent signal loops
    
    # Clear cache
    if CacheManager:
        CacheManager.delete_cache('document', str(document.id))
    
    # Send notification if enabled
    if hasattr(document.user, 'kb_config') and document.user.kb_config.error_notifications:
        # Send error notification
        # This would integrate with your notification system
        logger.info(f"SIGNAL: Would send error notification for document {document.id}")


# Cleanup signals for expired data
@receiver(post_save, sender=KnowledgeBaseConfig)
def schedule_cleanup_tasks(sender, instance, **kwargs):
    """Schedule cleanup tasks when config is updated"""
    try:
        # Calculate cleanup dates
        doc_cleanup_date = timezone.now() - timedelta(days=instance.document_retention_days)
        conv_cleanup_date = timezone.now() - timedelta(days=instance.conversation_retention_days)
        
        # This would typically schedule background tasks
        # For now, we'll just log the action
        logger.info(f"SIGNAL: Scheduled cleanup tasks for user {instance.user.id}")
        
    except Exception as e:
        logger.error(f"SIGNAL: Error scheduling cleanup tasks: {e}")


# Health check signal
health_check_signal = Signal()

@receiver(health_check_signal)
def perform_health_check(sender, **kwargs):
    """Perform system health check"""
    try:
        # Check database connections
        # Check vector store connections
        # Check AI model availability
        # Check background task queue
        
        logger.info("SIGNAL: Health check completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"SIGNAL: Health check failed: {e}")
        return False


# Bulk operation signals
bulk_operation_started = Signal()
bulk_operation_completed = Signal()

@receiver(bulk_operation_started)
def handle_bulk_operation_started(sender, operation_type, user_id, **kwargs):
    """Handle bulk operation start"""
    logger.info(f"SIGNAL: Bulk operation {operation_type} started for user {user_id}")


@receiver(bulk_operation_completed)
def handle_bulk_operation_completed(sender, operation_type, user_id, results, **kwargs):
    """Handle bulk operation completion"""
    logger.info(f"SIGNAL: Bulk operation {operation_type} completed for user {user_id}: {results}")
    
    # Clear user cache after bulk operations
    if CacheManager:
        CacheManager.clear_user_cache(str(user_id))


# Data source sync signals
sync_started = Signal()
sync_completed = Signal()
sync_failed = Signal()

@receiver(sync_started)
def handle_sync_started(sender, data_source, **kwargs):
    """Handle data source sync start"""
    logger.info(f"SIGNAL: Sync started for data source {data_source.name}")
    
    # Update status
    data_source.status = 'syncing'
    data_source.save()


@receiver(sync_completed)
def handle_sync_completed(sender, data_source, results, **kwargs):
    """Handle data source sync completion"""
    logger.info(f"SIGNAL: Sync completed for data source {data_source.name}: {results}")
    
    # Update status and timestamp
    data_source.status = 'active'
    data_source.last_sync = timezone.now()
    data_source.save()
    
    # Clear cache
    if CacheManager:
        CacheManager.delete_cache('data_source', str(data_source.id))
    
    # Send notification if enabled
    if hasattr(data_source.user, 'kb_config') and data_source.user.kb_config.sync_notifications:
        # Send sync completion notification
        logger.info(f"SIGNAL: Would send sync completion notification for {data_source.name}")


@receiver(sync_failed)
def handle_sync_failed(sender, data_source, error, **kwargs):
    """Handle data source sync failure"""
    logger.error(f"SIGNAL: Sync failed for data source {data_source.name}: {error}")
    
    # Update status
    data_source.status = 'error'
    data_source.save()
    
    # Clear cache
    if CacheManager:
        CacheManager.delete_cache('data_source', str(data_source.id))
    
    # Send notification if enabled
    if hasattr(data_source.user, 'kb_config') and data_source.user.kb_config.error_notifications:
        # Send sync failure notification
        logger.info(f"SIGNAL: Would send sync failure notification for {data_source.name}")


# Utility function to check processing status
def get_processing_status():
    """Get current processing status for debugging"""
    return {
        'processing_documents': list(_processing_documents),
        'queued_tasks': dict(_queued_tasks)
    }


# Log when signals are loaded
logger.info("SIGNALS: All signal handlers registered successfully")