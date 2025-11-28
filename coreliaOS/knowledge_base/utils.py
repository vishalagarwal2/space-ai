
import os
import json
import logging
import hashlib
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading

# Django imports
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from django.core.exceptions import ValidationError

# Third-party imports
import tiktoken
from pathlib import Path

logger = logging.getLogger(__name__)


class FileTypeDetector:
    """Utility class for detecting file types"""
    
    FILE_TYPE_MAPPING = {
        # Documents
        '.pdf': 'document',
        '.doc': 'document',
        '.docx': 'document',
        '.txt': 'document',
        '.rtf': 'document',
        '.odt': 'document',
        
        # Spreadsheets
        '.xls': 'document',
        '.xlsx': 'document',
        '.csv': 'document',
        '.ods': 'document',
        
        # Presentations
        '.ppt': 'document',
        '.pptx': 'document',
        '.odp': 'document',
        
        # Images
        '.jpg': 'image',
        '.jpeg': 'image',
        '.png': 'image',
        '.gif': 'image',
        '.bmp': 'image',
        '.tiff': 'image',
        '.webp': 'image',
        '.svg': 'image',
        
        # Audio
        '.mp3': 'audio',
        '.wav': 'audio',
        '.ogg': 'audio',
        '.flac': 'audio',
        '.aac': 'audio',
        '.m4a': 'audio',
        
        # Video
        '.mp4': 'video',
        '.avi': 'video',
        '.mkv': 'video',
        '.mov': 'video',
        '.wmv': 'video',
        '.flv': 'video',
        '.webm': 'video',
        
        # Code
        '.py': 'code',
        '.js': 'code',
        '.html': 'code',
        '.css': 'code',
        '.java': 'code',
        '.cpp': 'code',
        '.c': 'code',
        '.php': 'code',
        '.rb': 'code',
        '.go': 'code',
        '.rs': 'code',
        '.sql': 'code',
        
        # Data
        '.json': 'data',
        '.xml': 'data',
        '.yaml': 'data',
        '.yml': 'data',
        '.toml': 'data',
        
        # Archives
        '.zip': 'archive',
        '.rar': 'archive',
        '.7z': 'archive',
        '.tar': 'archive',
        '.gz': 'archive',
    }
    
    MIME_TYPE_MAPPING = {
        'application/pdf': 'document',
        'application/msword': 'document',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'document',
        'text/plain': 'document',
        'text/html': 'code',
        'text/css': 'code',
        'text/javascript': 'code',
        'application/json': 'data',
        'application/xml': 'data',
        'image/jpeg': 'image',
        'image/png': 'image',
        'image/gif': 'image',
        'audio/mpeg': 'audio',
        'audio/wav': 'audio',
        'video/mp4': 'video',
        'video/avi': 'video',
    }
    
    @classmethod
    def detect_file_type(cls, file_path: str = None, mime_type: str = None) -> str:
        """Detect file type from path or MIME type"""
        if file_path:
            ext = Path(file_path).suffix.lower()
            if ext in cls.FILE_TYPE_MAPPING:
                return cls.FILE_TYPE_MAPPING[ext]
        
        if mime_type and mime_type in cls.MIME_TYPE_MAPPING:
            return cls.MIME_TYPE_MAPPING[mime_type]
        
        return 'other'
    
    @classmethod
    def get_supported_extensions(cls, category: str = None) -> List[str]:
        """Get supported file extensions, optionally filtered by category"""
        if category:
            return [ext for ext, cat in cls.FILE_TYPE_MAPPING.items() if cat == category]
        return list(cls.FILE_TYPE_MAPPING.keys())


class TokenCounter:
    """Utility class for counting tokens in text"""
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except:
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            return len(self.encoding.encode(text))
        except:
            # Fallback: rough estimation
            return len(text.split()) * 1.3
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in a list of messages"""
        total = 0
        for message in messages:
            total += self.count_tokens(message.get('content', ''))
            total += 4  # Overhead per message
        return total
    
    def truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit"""
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)


class RateLimiter:
    """Rate limiter for API requests"""
    
    def __init__(self):
        self.requests = defaultdict(deque)
        self.daily_requests = defaultdict(int)
        self.daily_reset = defaultdict(datetime)
        self.lock = threading.Lock()
    
    def check_rate_limit(self, hourly_limit: int, daily_limit: int, 
                        key: str = 'default') -> bool:
        """Check if request is within rate limits"""
        with self.lock:
            now = datetime.now()
            
            # Check daily reset
            if key not in self.daily_reset or now.date() > self.daily_reset[key].date():
                self.daily_requests[key] = 0
                self.daily_reset[key] = now
            
            # Clean old hourly requests
            hour_ago = now - timedelta(hours=1)
            while self.requests[key] and self.requests[key][0] < hour_ago:
                self.requests[key].popleft()
            
            # Check limits
            if len(self.requests[key]) >= hourly_limit:
                return False
            
            if self.daily_requests[key] >= daily_limit:
                return False
            
            # Record request
            self.requests[key].append(now)
            self.daily_requests[key] += 1
            
            return True
    
    def get_remaining_requests(self, hourly_limit: int, daily_limit: int,
                             key: str = 'default') -> Dict[str, int]:
        """Get remaining requests for hour and day"""
        with self.lock:
            now = datetime.now()
            
            # Clean old requests
            hour_ago = now - timedelta(hours=1)
            while self.requests[key] and self.requests[key][0] < hour_ago:
                self.requests[key].popleft()
            
            # Check daily reset
            if key not in self.daily_reset or now.date() > self.daily_reset[key].date():
                self.daily_requests[key] = 0
                self.daily_reset[key] = now
            
            return {
                'hourly_remaining': hourly_limit - len(self.requests[key]),
                'daily_remaining': daily_limit - self.daily_requests[key]
            }


class DocumentProcessor:
    """Utility class for processing documents"""
    
    @staticmethod
    def generate_document_hash(content: str, metadata: Dict[str, Any] = None) -> str:
        """Generate a hash for document content"""
        hash_input = content
        if metadata:
            hash_input += json.dumps(metadata, sort_keys=True)
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 20) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction - can be improved with NLP libraries
        import re
        from collections import Counter
        
        # Remove punctuation and convert to lowercase
        text = re.sub(r'[^\w\s]', '', text.lower())
        
        # Common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'this', 'that', 'these', 'those',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'shall', 'not', 'no'
        }
        
        # Extract words
        words = text.split()
        
        # Filter words
        filtered_words = [
            word for word in words
            if len(word) > 2 and word not in stop_words
        ]
        
        # Count frequencies
        word_counts = Counter(filtered_words)
        
        # Return top keywords
        return [word for word, count in word_counts.most_common(max_keywords)]
    
    @staticmethod
    def summarize_text(text: str, max_sentences: int = 3) -> str:
        """Create a simple extractive summary"""
        import re
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= max_sentences:
            return text
        
        # Simple scoring: prefer sentences with more words
        sentence_scores = []
        for sentence in sentences:
            score = len(sentence.split())
            sentence_scores.append((score, sentence))
        
        # Sort by score and take top sentences
        sentence_scores.sort(reverse=True)
        top_sentences = [s for score, s in sentence_scores[:max_sentences]]
        
        # Maintain original order
        summary_sentences = []
        for sentence in sentences:
            if sentence in top_sentences:
                summary_sentences.append(sentence)
        
        return '. '.join(summary_sentences) + '.'


class ConfigurationManager:
    """Manages system configuration"""
    
    @staticmethod
    def get_default_embedding_config() -> Dict[str, Any]:
        """Get default embedding configuration"""
        return {
            'model_name': 'all-MiniLM-L6-v2',
            'dimension': 384,
            'chunk_size': 1000,
            'chunk_overlap': 200,
            'similarity_threshold': 0.7
        }
    
    @staticmethod
    def get_default_agent_config() -> Dict[str, Any]:
        """Get default agent configuration"""
        return {
            'model_provider': 'openai',
            'model_name': 'gpt-3.5-turbo',
            'temperature': 0.7,
            'max_tokens': 1000,
            'conversation_mode': 'session',
            'context_window': 4000,
            'max_documents': 10,
            'similarity_threshold': 0.7,
            'rate_limit_per_hour': 100,
            'rate_limit_per_day': 1000
        }
    
    @staticmethod
    def validate_agent_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate agent configuration"""
        errors = {}
        
        # Check required fields
        required_fields = ['model_provider', 'model_name']
        for field in required_fields:
            if field not in config:
                errors[field] = f"{field} is required"
        
        # Validate numeric fields
        numeric_fields = {
            'temperature': (0.0, 2.0),
            'max_tokens': (1, 32000),
            'context_window': (100, 32000),
            'max_documents': (1, 100),
            'similarity_threshold': (0.0, 1.0),
            'rate_limit_per_hour': (1, 10000),
            'rate_limit_per_day': (1, 100000)
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in config:
                try:
                    value = float(config[field])
                    if not (min_val <= value <= max_val):
                        errors[field] = f"{field} must be between {min_val} and {max_val}"
                except (ValueError, TypeError):
                    errors[field] = f"{field} must be a number"
        
        # Validate enum fields
        enum_fields = {
            'model_provider': ['openai', 'anthropic', 'cohere', 'huggingface', 'local'],
            'conversation_mode': ['stateless', 'session', 'persistent', 'contextual']
        }
        
        for field, valid_values in enum_fields.items():
            if field in config and config[field] not in valid_values:
                errors[field] = f"{field} must be one of: {', '.join(valid_values)}"
        
        if errors:
            raise ValidationError(errors)
        
        return config


class CacheManager:
    """Manages caching for the knowledge base"""
    
    CACHE_PREFIXES = {
        'embedding': 'kb_embedding_',
        'document': 'kb_document_',
        'agent_response': 'kb_agent_response_',
        'search_results': 'kb_search_',
        'user_config': 'kb_user_config_'
    }
    
    DEFAULT_TIMEOUTS = {
        'embedding': 3600,  # 1 hour
        'document': 1800,   # 30 minutes
        'agent_response': 300,  # 5 minutes
        'search_results': 600,  # 10 minutes
        'user_config': 7200     # 2 hours
    }
    
    @classmethod
    def get_cache_key(cls, cache_type: str, identifier: str) -> str:
        """Generate cache key"""
        prefix = cls.CACHE_PREFIXES.get(cache_type, 'kb_')
        return f"{prefix}{identifier}"
    
    @classmethod
    def set_cache(cls, cache_type: str, identifier: str, data: Any, 
                  timeout: int = None) -> bool:
        """Set cache data"""
        try:
            key = cls.get_cache_key(cache_type, identifier)
            timeout = timeout or cls.DEFAULT_TIMEOUTS.get(cache_type, 3600)
            cache.set(key, data, timeout)
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    @classmethod
    def get_cache(cls, cache_type: str, identifier: str) -> Any:
        """Get cache data"""
        try:
            key = cls.get_cache_key(cache_type, identifier)
            return cache.get(key)
        except Exception as e:
            logger.error(f"Error getting cache: {e}")
            return None
    
    @classmethod
    def delete_cache(cls, cache_type: str, identifier: str) -> bool:
        """Delete cache data"""
        try:
            key = cls.get_cache_key(cache_type, identifier)
            cache.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache: {e}")
            return False
    
    @classmethod
    def clear_user_cache(cls, user_id: str) -> bool:
        """Clear all cache for a user"""
        try:
            # This is a simplified implementation
            # In production, you might want to use cache patterns
            patterns = [
                f"kb_*_{user_id}_*",
                f"kb_user_config_{user_id}"
            ]
            
            # Django's cache doesn't support pattern deletion by default
            # You might need to implement this based on your cache backend
            logger.info(f"Cache clear requested for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing user cache: {e}")
            return False


class AnalyticsManager:
    """Manages analytics and metrics"""
    
    @staticmethod
    def get_user_usage_stats(user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user usage statistics"""
        from .models import AgentUsage, Document, Conversation
        
        # Date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Usage statistics
        usage_stats = AgentUsage.objects.filter(
            user_id=user_id,
            created_at__range=(start_date, end_date)
        ).aggregate(
            total_requests=Count('id'),
            total_tokens=Sum('tokens_used'),
            avg_response_time=Avg('response_time')
        )
        
        # Document statistics
        doc_stats = Document.objects.filter(
            user_id=user_id,
            created_at__range=(start_date, end_date)
        ).aggregate(
            total_documents=Count('id'),
            processed_documents=Count('id', filter=Q(status='processed')),
            failed_documents=Count('id', filter=Q(status='error'))
        )
        
        # Conversation statistics
        conv_stats = Conversation.objects.filter(
            user_id=user_id,
            created_at__range=(start_date, end_date)
        ).aggregate(
            total_conversations=Count('id')
        )
        
        return {
            'usage': usage_stats,
            'documents': doc_stats,
            'conversations': conv_stats,
            'period_days': days
        }
    
    @staticmethod
    def get_agent_performance_stats(agent_id: str, days: int = 30) -> Dict[str, Any]:
        """Get agent performance statistics"""
        from .models import AgentUsage, Message
        
        # Date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Performance statistics
        perf_stats = AgentUsage.objects.filter(
            agent_id=agent_id,
            created_at__range=(start_date, end_date)
        ).aggregate(
            total_requests=Count('id'),
            total_tokens=Sum('tokens_used'),
            avg_response_time=Avg('response_time'),
            total_cost=Sum('cost')
        )
        
        # Message statistics
        msg_stats = Message.objects.filter(
            conversation__agent_id=agent_id,
            created_at__range=(start_date, end_date)
        ).aggregate(
            total_messages=Count('id'),
            user_messages=Count('id', filter=Q(role='user')),
            assistant_messages=Count('id', filter=Q(role='assistant'))
        )
        
        return {
            'performance': perf_stats,
            'messages': msg_stats,
            'period_days': days
        }
    
    @staticmethod
    def get_system_health_stats() -> Dict[str, Any]:
        """Get system health statistics"""
        from .models import Document, DataSource, AIAgent
        
        # Document processing health
        doc_health = Document.objects.aggregate(
            total_documents=Count('id'),
            processed_documents=Count('id', filter=Q(status='processed')),
            processing_documents=Count('id', filter=Q(status='processing')),
            failed_documents=Count('id', filter=Q(status='error')),
            pending_documents=Count('id', filter=Q(status='pending'))
        )
        
        # Data source health
        source_health = DataSource.objects.aggregate(
            total_sources=Count('id'),
            active_sources=Count('id', filter=Q(status='active')),
            inactive_sources=Count('id', filter=Q(status='inactive')),
            error_sources=Count('id', filter=Q(status='error'))
        )
        
        # Agent health
        agent_health = AIAgent.objects.aggregate(
            total_agents=Count('id'),
            active_agents=Count('id', filter=Q(is_active=True)),
            inactive_agents=Count('id', filter=Q(is_active=False))
        )
        
        return {
            'documents': doc_health,
            'data_sources': source_health,
            'agents': agent_health,
            'timestamp': timezone.now().isoformat()
        }


class BackupManager:
    """Manages backup and restore operations"""
    
    @staticmethod
    def export_user_data(user_id: str) -> Dict[str, Any]:
        """Export user data for backup"""
        from .models import (
            DataSource, Document, AIAgent, Conversation, 
            Message, KnowledgeBaseConfig
        )
        
        # Export data
        export_data = {
            'user_id': user_id,
            'export_date': timezone.now().isoformat(),
            'data_sources': list(DataSource.objects.filter(user_id=user_id).values()),
            'documents': list(Document.objects.filter(user_id=user_id).values()),
            'agents': list(AIAgent.objects.filter(user_id=user_id).values()),
            'conversations': list(Conversation.objects.filter(user_id=user_id).values()),
            'messages': list(Message.objects.filter(conversation__user_id=user_id).values()),
            'config': {}
        }
        
        # Export config if exists
        try:
            config = KnowledgeBaseConfig.objects.get(user_id=user_id)
            export_data['config'] = {
                'default_embedding_model': config.default_embedding_model,
                'default_chunk_size': config.default_chunk_size,
                'default_chunk_overlap': config.default_chunk_overlap,
                'document_retention_days': config.document_retention_days,
                'conversation_retention_days': config.conversation_retention_days,
                'default_similarity_threshold': config.default_similarity_threshold,
                'max_search_results': config.max_search_results,
                'sync_notifications': config.sync_notifications,
                'error_notifications': config.error_notifications
            }
        except KnowledgeBaseConfig.DoesNotExist:
            pass
        
        return export_data
    
    @staticmethod
    def import_user_data(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Import user data from backup"""
        from .models import (
            DataSource, Document, AIAgent, Conversation, 
            Message, KnowledgeBaseConfig
        )
        
        results = {
            'imported': {},
            'errors': []
        }
        
        try:
            # Import data sources
            for source_data in data.get('data_sources', []):
                source_data['user_id'] = user_id
                source_data.pop('id', None)  # Remove original ID
                DataSource.objects.create(**source_data)
            results['imported']['data_sources'] = len(data.get('data_sources', []))
            
            # Import agents
            for agent_data in data.get('agents', []):
                agent_data['user_id'] = user_id
                agent_data.pop('id', None)
                AIAgent.objects.create(**agent_data)
            results['imported']['agents'] = len(data.get('agents', []))
            
            # Import configuration
            config_data = data.get('config', {})
            if config_data:
                config_data['user_id'] = user_id
                KnowledgeBaseConfig.objects.update_or_create(
                    user_id=user_id,
                    defaults=config_data
                )
                results['imported']['config'] = 1
            
            # Note: Documents, conversations, and messages would need special handling
            # due to file references and relationships
            
        except Exception as e:
            results['errors'].append(str(e))
        
        return results


class ErrorHandler:
    """Centralized error handling"""
    
    ERROR_TYPES = {
        'authentication': 'Authentication Error',
        'rate_limit': 'Rate Limit Exceeded',
        'parsing': 'Document Parsing Error',
        'embedding': 'Embedding Generation Error',
        'model': 'AI Model Error',
        'storage': 'Storage Error',
        'network': 'Network Error',
        'validation': 'Validation Error',
        'permission': 'Permission Error',
        'quota': 'Quota Exceeded',
        'unknown': 'Unknown Error'
    }
    
    @staticmethod
    def handle_error(error_type: str, error_message: str, 
                    context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle and log errors"""
        error_info = {
            'type': error_type,
            'message': error_message,
            'title': ErrorHandler.ERROR_TYPES.get(error_type, 'Error'),
            'context': context or {},
            'timestamp': timezone.now().isoformat()
        }
        
        # Log error
        logger.error(f"Error [{error_type}]: {error_message}", extra=error_info)
        
        # Return user-friendly error
        return {
            'error': True,
            'error_type': error_type,
            'error_title': error_info['title'],
            'error_message': error_message,
            'timestamp': error_info['timestamp']
        }
    
    @staticmethod
    def get_user_friendly_message(error_type: str, error_message: str) -> str:
        """Get user-friendly error message"""
        friendly_messages = {
            'authentication': 'Please check your credentials and try again.',
            'rate_limit': 'You have exceeded the rate limit. Please try again later.',
            'parsing': 'Unable to process this file. Please check the file format.',
            'embedding': 'Error processing document content. Please try again.',
            'model': 'AI service is temporarily unavailable. Please try again later.',
            'storage': 'Storage service is temporarily unavailable.',
            'network': 'Network connection error. Please check your connection.',
            'validation': 'Please check your input and try again.',
            'permission': 'You do not have permission to perform this action.',
            'quota': 'You have exceeded your usage quota.',
            'unknown': 'An unexpected error occurred. Please try again.'
        }
        
        return friendly_messages.get(error_type, error_message)


# Utility functions
def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    return filename


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


def validate_json_config(config: str) -> Dict[str, Any]:
    """Validate and parse JSON configuration"""
    try:
        parsed_config = json.loads(config)
        if not isinstance(parsed_config, dict):
            raise ValueError("Configuration must be a JSON object")
        return parsed_config
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")


def generate_unique_id(prefix: str = "") -> str:
    """Generate unique ID"""
    import uuid
    unique_id = str(uuid.uuid4())
    return f"{prefix}{unique_id}" if prefix else unique_id


def is_text_file(file_path: str) -> bool:
    """Check if file is a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)  # Try to read first 1KB
        return True
    except UnicodeDecodeError:
        return False
    except Exception:
        return False


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_configs(base_config: Dict[str, Any], 
                 override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configuration dictionaries"""
    merged = base_config.copy()
    merged.update(override_config)
    return merged


def get_file_hash(file_path: str) -> str:
    """Get MD5 hash of file"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {e}")
        return ""


class ProgressTracker:
    """Track progress of long-running operations"""
    
    def __init__(self, total_items: int, operation_name: str = "Operation"):
        self.total_items = total_items
        self.completed_items = 0
        self.operation_name = operation_name
        self.start_time = datetime.now()
        self.errors = []
    
    def update(self, increment: int = 1, message: str = ""):
        """Update progress"""
        self.completed_items += increment
        percentage = (self.completed_items / self.total_items) * 100
        
        elapsed = datetime.now() - self.start_time
        if self.completed_items > 0:
            rate = self.completed_items / elapsed.total_seconds()
            eta = (self.total_items - self.completed_items) / rate if rate > 0 else 0
        else:
            eta = 0
        
        logger.info(
            f"{self.operation_name}: {self.completed_items}/{self.total_items} "
            f"({percentage:.1f}%) - ETA: {eta:.0f}s - {message}"
        )
    
    def add_error(self, error_message: str):
        """Add error to tracker"""
        self.errors.append(error_message)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get operation summary"""
        elapsed = datetime.now() - self.start_time
        return {
            'operation': self.operation_name,
            'total_items': self.total_items,
            'completed_items': self.completed_items,
            'success_rate': (self.completed_items / self.total_items) * 100,
            'elapsed_time': elapsed.total_seconds(),
            'errors': self.errors,
            'error_count': len(self.errors)
        }