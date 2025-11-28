# knowledge_base/apps.py

from django.apps import AppConfig
from django.db import connection
from django.core.management.color import no_style
import logging

logger = logging.getLogger(__name__)


class KnowledgeBaseConfig(AppConfig):
    """Configuration for the Knowledge Base app"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'knowledge_base'
    verbose_name = 'Knowledge Base'
    
    def ready(self):
        """Initialize the app when Django starts"""
        # Import signals with explicit logging
        try:
            from . import signals  # Use relative import
            logger.info("Successfully imported knowledge_base signals")
        except ImportError as e:
            logger.error(f"Failed to import knowledge_base signals: {e}")
        except Exception as e:
            logger.error(f"Unexpected error importing signals: {e}")
        
        # Only initialize default data if we're not in a migration context
        # and the tables actually exist
        if self._tables_exist():
            self.create_default_file_types()
            self.initialize_default_configs()
    
    def _tables_exist(self):
        """Check if the required tables exist"""
        try:
            from django.db import connection
            table_names = connection.introspection.table_names()
            required_tables = [
                'knowledge_base_filetype',
                'knowledge_base_knowledgebaseconfig'
            ]
            return all(table in table_names for table in required_tables)
        except Exception as e:
            logger.debug(f"Error checking table existence: {e}")
            return False
    
    def create_default_file_types(self):
        """Create default file types if they don't exist"""
        try:
            # Import here to avoid circular imports
            from .models import FileType
            
            default_file_types = [
                {
                    'name': 'PDF Document',
                    'category': 'document',
                    'mime_types': ['application/pdf'],
                    'extensions': ['.pdf'],
                    'parsers': ['PDFParser'],
                    'embedding_models': ['sentence_transformer']
                },
                {
                    'name': 'Word Document',
                    'category': 'document',
                    'mime_types': [
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'application/msword'
                    ],
                    'extensions': ['.docx', '.doc'],
                    'parsers': ['DocumentParser'],
                    'embedding_models': ['sentence_transformer']
                },
                {
                    'name': 'Excel Spreadsheet',
                    'category': 'document',
                    'mime_types': [
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        'application/vnd.ms-excel'
                    ],
                    'extensions': ['.xlsx', '.xls'],
                    'parsers': ['DocumentParser'],
                    'embedding_models': ['sentence_transformer']
                },
                {
                    'name': 'PowerPoint Presentation',
                    'category': 'document',
                    'mime_types': [
                        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                        'application/vnd.ms-powerpoint'
                    ],
                    'extensions': ['.pptx', '.ppt'],
                    'parsers': ['DocumentParser'],
                    'embedding_models': ['sentence_transformer']
                },
                {
                    'name': 'Text File',
                    'category': 'document',
                    'mime_types': ['text/plain'],
                    'extensions': ['.txt'],
                    'parsers': ['TextParser'],
                    'embedding_models': ['sentence_transformer']
                },
                {
                    'name': 'CSV File',
                    'category': 'data',
                    'mime_types': ['text/csv'],
                    'extensions': ['.csv'],
                    'parsers': ['TextParser'],
                    'embedding_models': ['sentence_transformer']
                },
                {
                    'name': 'JSON File',
                    'category': 'data',
                    'mime_types': ['application/json'],
                    'extensions': ['.json'],
                    'parsers': ['TextParser'],
                    'embedding_models': ['sentence_transformer']
                },
                {
                    'name': 'XML File',
                    'category': 'data',
                    'mime_types': ['application/xml', 'text/xml'],
                    'extensions': ['.xml'],
                    'parsers': ['TextParser'],
                    'embedding_models': ['sentence_transformer']
                },
                {
                    'name': 'Image File',
                    'category': 'image',
                    'mime_types': ['image/jpeg', 'image/png', 'image/gif', 'image/bmp'],
                    'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
                    'parsers': ['ImageParser'],
                    'embedding_models': ['sentence_transformer']
                },
                {
                    'name': 'Audio File',
                    'category': 'audio',
                    'mime_types': ['audio/mpeg', 'audio/wav', 'audio/ogg'],
                    'extensions': ['.mp3', '.wav', '.ogg'],
                    'parsers': ['AudioParser'],
                    'embedding_models': ['sentence_transformer']
                },
                {
                    'name': 'Video File',
                    'category': 'video',
                    'mime_types': ['video/mp4', 'video/avi', 'video/quicktime'],
                    'extensions': ['.mp4', '.avi', '.mov'],
                    'parsers': ['VideoParser'],
                    'embedding_models': ['sentence_transformer']
                },
                {
                    'name': 'Python Code',
                    'category': 'code',
                    'mime_types': ['text/x-python'],
                    'extensions': ['.py'],
                    'parsers': ['TextParser'],
                    'embedding_models': ['sentence_transformer']
                },
                {
                    'name': 'JavaScript Code',
                    'category': 'code',
                    'mime_types': ['text/javascript', 'application/javascript'],
                    'extensions': ['.js'],
                    'parsers': ['TextParser'],
                    'embedding_models': ['sentence_transformer']
                },
                {
                    'name': 'HTML File',
                    'category': 'code',
                    'mime_types': ['text/html'],
                    'extensions': ['.html', '.htm'],
                    'parsers': ['TextParser'],
                    'embedding_models': ['sentence_transformer']
                },
                {
                    'name': 'CSS File',
                    'category': 'code',
                    'mime_types': ['text/css'],
                    'extensions': ['.css'],
                    'parsers': ['TextParser'],
                    'embedding_models': ['sentence_transformer']
                }
            ]
            
            created_count = 0
            for file_type_data in default_file_types:
                file_type, created = FileType.objects.get_or_create(
                    name=file_type_data['name'],
                    defaults=file_type_data
                )
                if created:
                    created_count += 1
            
            if created_count > 0:
                logger.info(f"Created {created_count} default file types")
                
        except Exception as e:
            logger.error(f"Error creating default file types: {e}")
    
    def initialize_default_configs(self):
        """Initialize default configurations"""
        try:
            # This will be called when the app is ready
            # Can be used to set up default system configurations
            logger.debug("Default configurations initialized")
        except Exception as e:
            logger.error(f"Error initializing default configs: {e}")