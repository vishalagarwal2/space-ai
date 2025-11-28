# knowledge_base/management/commands/init_kb_data.py

from django.core.management.base import BaseCommand
from django.db import transaction
from knowledge_base.models import FileType


class Command(BaseCommand):
    help = 'Initialize default Knowledge Base data (file types, configurations)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing data',
        )

    def handle(self, *args, **options):
        self.stdout.write('Initializing Knowledge Base data...')
        
        try:
            with transaction.atomic():
                self.create_file_types(force=options['force'])
                
            self.stdout.write(
                self.style.SUCCESS('Successfully initialized Knowledge Base data')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error initializing data: {e}')
            )

    def create_file_types(self, force=False):
        """Create default file types"""
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
        updated_count = 0
        
        for file_type_data in default_file_types:
            if force:
                # Update or create
                file_type, created = FileType.objects.update_or_create(
                    name=file_type_data['name'],
                    defaults=file_type_data
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            else:
                # Only create if doesn't exist
                file_type, created = FileType.objects.get_or_create(
                    name=file_type_data['name'],
                    defaults=file_type_data
                )
                if created:
                    created_count += 1
        
        if created_count > 0:
            self.stdout.write(f'Created {created_count} file types')
        if updated_count > 0:
            self.stdout.write(f'Updated {updated_count} file types')
        if created_count == 0 and updated_count == 0:
            self.stdout.write('All file types already exist')