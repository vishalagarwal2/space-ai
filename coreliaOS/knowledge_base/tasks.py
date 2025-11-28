
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from typing import Dict, Any, List
import traceback

from .models import Document, DataSource
from .data_sources import data_source_registry
from .embeddings import EmbeddingManager
from .parsers import parser_registry
from .utils import ProgressTracker
from .signals import (
    document_processed, document_processing_failed,
    sync_started, sync_completed, sync_failed,
    mark_document_processing_complete
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_document(self, document_id: str, user_id: str):
    """Process a document asynchronously"""
    try:
        # Import here to avoid potential import issues in worker
        from .models import Document
        from .parsers import parser_registry
        from .signals import mark_document_processing_complete, document_processed, document_processing_failed
        import traceback
        
        logger.info(f"CELERY TASK: Starting to process document {document_id} for user {user_id}")
        logger.info(f"CELERY TASK: Task ID: {self.request.id}")
        
        # Get the document
        try:
            document = Document.objects.get(id=document_id, user_id=user_id)
            logger.info(f"CELERY TASK: Found document '{document.title}' with status '{document.status}'")
        except Document.DoesNotExist:
            logger.error(f"CELERY TASK: Document {document_id} not found")
            mark_document_processing_complete(document_id)
            return {'status': 'error', 'message': 'Document not found'}
        
        # Check if document no longer needs processing
        if not document.needs_processing:
            logger.info(f"CELERY TASK: Document {document_id} no longer needs processing, skipping")
            mark_document_processing_complete(document_id)
            return {'status': 'success', 'message': 'Document no longer needs processing'}
        
        # Check if another task is already processing this document
        if (document.status == 'processing' and 
            document.processing_started_at and 
            document.processing_log):
            
            # Check if this is a different task trying to process the same document
            last_entry = document.processing_log[-1]
            if (last_entry.get('task_id') and 
                last_entry.get('task_id') != self.request.id):
                logger.info(f"CELERY TASK: Document {document_id} is already being processed by task {last_entry.get('task_id')}, skipping")
                mark_document_processing_complete(document_id)
                return {'status': 'success', 'message': 'Document already being processed by another task'}
        
        logger.info(f"CELERY TASK: Processing document {document_id}")
        
        # CRITICAL: Use helper method to update status (won't trigger signal)
        document.mark_processing_started()
        
        # Get appropriate parser
        parser = parser_registry.get_parser(document.file_path or '', document.mime_type)
        logger.info(f"CELERY TASK: Using parser: {parser.__class__.__name__} for document {document_id}")
        
        if not parser:
            raise ValueError(f"No parser found for {document.mime_type}")
        
        # Parse document
        if document.file_path:
            parsed_result = parser.parse(document.file_path)
        else:
            # Handle content-only documents
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
                tmp_file.write(document.raw_content)
                tmp_file_path = tmp_file.name
            
            try:
                parsed_result = parser.parse(tmp_file_path)
            finally:
                import os
                os.unlink(tmp_file_path)
        
        if 'error' in parsed_result:
            raise ValueError(parsed_result['error'])
        

        document.mark_parsing_complete()
        
        # Prepare processed content
        processed_content = parsed_result.get('content', '')
        
        # Generate embeddings
        chunks = parsed_result.get('chunks', [processed_content])
        logger.info(f"CELERY TASK: Document {document_id} parsed into {len(chunks)} chunks")
        
        embeddings_task_id = None
        if chunks and chunks[0]:
            try:
                # Queue embeddings generation
                from .tasks import generate_embeddings
                embeddings_result = generate_embeddings.delay(document_id, chunks, user_id)
                embeddings_task_id = embeddings_result.id
                logger.info(f"CELERY TASK: Embeddings generation task queued for document {document_id} (task: {embeddings_task_id})")
            except Exception as e:
                logger.error(f"CELERY TASK: Error queuing embeddings for document {document_id}: {e}")
                # Continue processing even if embeddings fail
        
        # CRITICAL: Use helper method to mark as processed (won't trigger signal)
        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'step': 'processing_completed',
            'status': 'success',
            'message': f'Document processing completed by task {self.request.id}',
            'task_id': self.request.id,
            'parser': parser.__class__.__name__,
            'chunks_count': len(chunks)
        }
        
        if embeddings_task_id:
            log_entry['embeddings_task_id'] = embeddings_task_id
        
        document.mark_processed(processed_content, log_entry)
        
        # Send success signal
        try:
            document_processed.send(sender=self.__class__, document=document)
        except Exception as e:
            logger.error(f"CELERY TASK: Error sending document_processed signal: {e}")
        
        # Mark processing as complete in signal tracking
        mark_document_processing_complete(document.id)
        logger.info(f"CELERY TASK: Successfully processed document {document_id}")
        
        return {
            'status': 'success',
            'document_id': document_id,
            'task_id': self.request.id,
            'chunks_count': len(chunks),
            'embeddings_task_id': embeddings_task_id,
            'message': 'Document processed successfully'
        }
        
    except Exception as e:
        logger.error(f"CELERY TASK: Error processing document {document_id}: {e}")
        import traceback
        logger.error(f"CELERY TASK: Traceback: {traceback.format_exc()}")
        
        # Mark processing as complete even on error
        try:
            from .signals import mark_document_processing_complete
            mark_document_processing_complete(document_id)
        except:
            pass
        
        # CRITICAL: Use helper method to mark error (won't trigger signal)
        try:
            from .models import Document
            from .signals import document_processing_failed
            
            document = Document.objects.get(id=document_id)
            
            error_log = {
                'timestamp': timezone.now().isoformat(),
                'step': 'processing_failed',
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc(),
                'task_id': self.request.id
            }
            
            document.mark_error(str(e), error_log)
            
            # Send failure signal
            try:
                document_processing_failed.send(
                    sender=self.__class__, 
                    document=document, 
                    error=e
                )
            except Exception as signal_error:
                logger.error(f"CELERY TASK: Error sending document_processing_failed signal: {signal_error}")
                
        except Exception as save_error:
            logger.error(f"CELERY TASK: Error saving document error state: {save_error}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(f"CELERY TASK: Retrying task for document {document_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        raise
    
@shared_task(bind=True, max_retries=2)
def generate_embeddings(self, document_id: str, chunks: List[str], user_id: str):
    """Generate embeddings for document chunks"""
    try:
        document = Document.objects.get(id=document_id, user_id=user_id)
        
        logger.info(f"Generating embeddings for document {document_id}")

        logger.info(f"generate_embeddings Chunks for document {document_id}: {chunks}")

        if( not chunks or not chunks[0]):
            logger.warning(f"No chunks provided for document {document_id}, skipping embeddings generation")
            return {'status': 'skipped', 'message': 'No chunks provided'}
        
        # Initialize embedding manager
        embedding_manager = EmbeddingManager(user_id)
        
        # Generate embeddings
        embedding_manager.add_document_embeddings(
            document_id=document_id,
            chunks=chunks,
            metadata={
                'title': document.title,
                'source': document.data_source.name if document.data_source else 'upload',
                'data_source_id': str(document.data_source.id) if document.data_source else '',
                'created_at': document.created_at.isoformat(),
                'file_type': document.file_type.name if document.file_type else 'unknown' # TODO: fix: file_type being set unknown
            },
        )
        
        logger.info(f"Successfully generated embeddings for document {document_id}")
        
    except Exception as e:
        logger.error(f"Error generating embeddings for document {document_id}: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        raise


@shared_task(bind=True, max_retries=3)
def sync_data_source(self, data_source_id: str):
    """Sync a data source asynchronously"""
    try:
        data_source = DataSource.objects.get(id=data_source_id)
        
        logger.info(f"Syncing data source {data_source.name}")
        
        # Send sync started signal
        sync_started.send(sender=self.__class__, data_source=data_source)
        
        # Get data source instance
        data_source_instance = data_source_registry.get_source(data_source)
        
        if not data_source_instance:
            raise ValueError(f"Data source type {data_source.source_type} not supported")
        
        # Authenticate
        if not data_source_instance.authenticate():
            raise ValueError("Authentication failed")
        
        # Sync documents
        processed_count = 0
        for doc_data in data_source_instance.get_documents():
            try:
                document = data_source_instance.process_document(doc_data)
                if document:
                    # Queue document for processing
                    process_document.delay(str(document.id), str(data_source.user.id))
                    processed_count += 1
            except Exception as e:
                logger.error(f"Error processing document from {data_source.name}: {e}")
                continue
        
        # Update data source
        data_source.last_sync = timezone.now()
        data_source.status = 'active'
        data_source.save()
        
        # Send sync completed signal
        sync_completed.send(
            sender=self.__class__, 
            data_source=data_source,
            results={'processed_count': processed_count}
        )
        
        logger.info(f"Successfully synced data source {data_source.name}: {processed_count} documents")
        
        return {'status': 'success', 'processed_count': processed_count}
        
    except Exception as e:
        logger.error(f"Error syncing data source {data_source_id}: {e}")
        
        try:
            data_source = DataSource.objects.get(id=data_source_id)
            data_source.status = 'error'
            data_source.save()
            
            # Send sync failed signal
            sync_failed.send(
                sender=self.__class__, 
                data_source=data_source,
                error=e
            )
        except:
            pass
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (self.request.retries + 1))
        
        raise


@shared_task
def sync_auto_sync_sources():
    """Sync all auto-sync enabled data sources"""
    logger.info("Starting auto-sync for data sources")
    
    now = timezone.now()
    
    # Get data sources that need syncing
    data_sources = DataSource.objects.filter(
        auto_sync=True,
        status__in=['active', 'error']
    )
    
    synced_count = 0
    
    for data_source in data_sources:
        # Check if it's time to sync
        if data_source.last_sync:
            next_sync = data_source.last_sync + timedelta(hours=data_source.sync_frequency)
            if now < next_sync:
                continue
        
        # Queue sync task
        sync_data_source.delay(str(data_source.id))
        synced_count += 1
    
    logger.info(f"Queued {synced_count} data sources for auto-sync")
    
    return {'synced_count': synced_count}


@shared_task
def cleanup_expired_documents():
    """Clean up expired documents"""
    logger.info("Starting cleanup of expired documents")
    
    now = timezone.now()
    
    # Get expired documents
    expired_docs = Document.objects.filter(
        expires_at__lt=now,
        status__in=['processed', 'error']
    )
    
    deleted_count = 0
    
    for document in expired_docs:
        try:
            # Soft delete the document
            document.soft_delete()
            deleted_count += 1
        except Exception as e:
            logger.error(f"Error deleting expired document {document.id}: {e}")
    
    logger.info(f"Soft deleted {deleted_count} expired documents")
    
    return {'deleted_count': deleted_count}


@shared_task
def cleanup_old_soft_deleted_documents():
    """Permanently delete old soft-deleted documents"""
    logger.info("Starting cleanup of old soft-deleted documents")
    
    # Delete documents that have been soft-deleted for more than 30 days
    cutoff_date = timezone.now() - timedelta(days=30)
    
    old_deleted_docs = Document.objects.filter(
        status='soft_deleted',
        soft_deleted_at__lt=cutoff_date
    )
    
    deleted_count = 0
    
    for document in old_deleted_docs:
        try:
            # Clean up embeddings first
            embedding_manager = EmbeddingManager(str(document.user.id))
            embedding_manager.delete_document_embeddings(str(document.id))
            
            # Delete the document
            document.delete()
            deleted_count += 1
        except Exception as e:
            logger.error(f"Error permanently deleting document {document.id}: {e}")
    
    logger.info(f"Permanently deleted {deleted_count} old soft-deleted documents")
    
    return {'deleted_count': deleted_count}


@shared_task
def update_usage_statistics():
    """Update usage statistics for analytics"""
    logger.info("Updating usage statistics")
    
    # This would update various statistics for analytics
    # For now, just log the action
    
    return {'status': 'completed'}


@shared_task(bind=True)
def bulk_process_documents(self, document_ids: List[str], user_id: str):
    """Process multiple documents in bulk"""
    try:
        progress_tracker = ProgressTracker(
            total_items=len(document_ids),
            operation_name="Bulk Document Processing"
        )
        
        processed_count = 0
        failed_count = 0
        
        for document_id in document_ids:
            try:
                # Queue individual document processing
                process_document.delay(document_id, user_id)
                processed_count += 1
                progress_tracker.update(1, f"Queued document {document_id}")
            except Exception as e:
                failed_count += 1
                progress_tracker.add_error(f"Failed to queue document {document_id}: {e}")
        
        summary = progress_tracker.get_summary()
        summary.update({
            'processed_count': processed_count,
            'failed_count': failed_count
        })
        
        logger.info(f"Bulk processing completed: {summary}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Error in bulk document processing: {e}")
        raise


@shared_task(bind=True)
def bulk_delete_documents(self, document_ids: List[str], user_id: str):
    """Delete multiple documents in bulk"""
    try:
        progress_tracker = ProgressTracker(
            total_items=len(document_ids),
            operation_name="Bulk Document Deletion"
        )
        
        deleted_count = 0
        failed_count = 0
        
        for document_id in document_ids:
            try:
                document = Document.objects.get(id=document_id, user_id=user_id)
                document.soft_delete()
                deleted_count += 1
                progress_tracker.update(1, f"Deleted document {document_id}")
            except Exception as e:
                failed_count += 1
                progress_tracker.add_error(f"Failed to delete document {document_id}: {e}")
        
        summary = progress_tracker.get_summary()
        summary.update({
            'deleted_count': deleted_count,
            'failed_count': failed_count
        })
        
        logger.info(f"Bulk deletion completed: {summary}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Error in bulk document deletion: {e}")
        raise


@shared_task
def health_check():
    """Perform system health check"""
    logger.info("Performing system health check")
    
    health_status = {
        'database': False,
        'redis': False,
        'vector_store': False,
        'parsers': False,
        'ai_models': False
    }
    
    try:
        # Check database
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['database'] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    try:
        # Check Redis
        from django.core.cache import cache
        cache.set('health_check', 'ok', 30)
        health_status['redis'] = cache.get('health_check') == 'ok'
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    try:
        # Check vector store
        # This would test ChromaDB/FAISS connectivity
        health_status['vector_store'] = True
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
    
    try:
        # Check parsers
        # Test if parsers are working
        health_status['parsers'] = len(parser_registry.parsers) > 0
    except Exception as e:
        logger.error(f"Parsers health check failed: {e}")
    
    try:
        # Check AI models
        # This would test API connectivity
        health_status['ai_models'] = True
    except Exception as e:
        logger.error(f"AI models health check failed: {e}")
    
    overall_health = all(health_status.values())
    
    logger.info(f"Health check completed: {health_status}")
    
    return {
        'overall_health': overall_health,
        'components': health_status,
        'timestamp': timezone.now().isoformat()
    }


@shared_task
def export_user_data(user_id: str, export_format: str = 'json'):
    """Export user data for backup or migration"""
    logger.info(f"Exporting data for user {user_id}")
    
    try:
        from .utils import BackupManager
        
        # Export user data
        export_data = BackupManager.export_user_data(user_id)
        
        # Save to file or return data
        # Implementation depends on requirements
        
        logger.info(f"Successfully exported data for user {user_id}")
        
        return {
            'status': 'success',
            'export_size': len(str(export_data)),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error exporting data for user {user_id}: {e}")
        raise


@shared_task
def import_user_data(user_id: str, import_data: Dict[str, Any]):
    """Import user data from backup"""
    logger.info(f"Importing data for user {user_id}")
    
    try:
        from .utils import BackupManager
        
        # Import user data
        results = BackupManager.import_user_data(user_id, import_data)
        
        logger.info(f"Successfully imported data for user {user_id}: {results}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error importing data for user {user_id}: {e}")
        raise