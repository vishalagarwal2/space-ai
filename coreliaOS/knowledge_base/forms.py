# knowledge_base/forms.py

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import json

from .models import DataSource, AIAgent, Document, FileType, KnowledgeBaseConfig
from .utils import ConfigurationManager


class DataSourceForm(forms.ModelForm):
    """Form for creating/editing data sources"""
    
    class Meta:
        model = DataSource
        fields = [
            'name', 'source_type', 'config', 'auto_sync', 'sync_frequency'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter data source name'
            }),
            'source_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'config': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter configuration as JSON'
            }),
            'auto_sync': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'sync_frequency': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 168  # 1 week
            })
        }
    
    def clean_config(self):
        """Validate JSON configuration"""
        config = self.cleaned_data.get('config')
        if config:
            try:
                json.loads(config)
            except json.JSONDecodeError:
                raise ValidationError("Configuration must be valid JSON")
        return config
    
    def clean_name(self):
        """Validate unique name per user"""
        name = self.cleaned_data.get('name')
        if name:
            # Check if name exists for this user (excluding current instance)
            queryset = DataSource.objects.filter(name=name)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError("A data source with this name already exists")
        return name


class AIAgentForm(forms.ModelForm):
    """Form for creating/editing AI agents"""
    
    class Meta:
        model = AIAgent
        fields = [
            'name', 'description', 'agent_type', 'model_provider', 'model_name',
            'model_parameters', 'conversation_mode', 'context_window', 'memory_retention_days',
            'system_prompt', 'user_prompt_template', 'data_sources', 'file_types',
            'max_documents', 'similarity_threshold', 'rate_limit_per_hour', 'rate_limit_per_day',
            'domain_keywords', 'expertise_areas', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter agent name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter agent description'
            }),
            'agent_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'model_provider': forms.Select(attrs={
                'class': 'form-control'
            }),
            'model_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., gpt-3.5-turbo'
            }),
            'model_parameters': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter model parameters as JSON'
            }),
            'conversation_mode': forms.Select(attrs={
                'class': 'form-control'
            }),
            'context_window': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 100,
                'max': 32000
            }),
            'memory_retention_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 365
            }),
            'system_prompt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter system prompt for the agent'
            }),
            'user_prompt_template': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter user prompt template (optional)'
            }),
            'data_sources': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'file_types': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'max_documents': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100
            }),
            'similarity_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.0,
                'max': 1.0,
                'step': 0.01
            }),
            'rate_limit_per_hour': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10000
            }),
            'rate_limit_per_day': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100000
            }),
            'domain_keywords': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter keywords as JSON array'
            }),
            'expertise_areas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter expertise areas as JSON array'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_model_parameters(self):
        """Validate model parameters JSON"""
        parameters = self.cleaned_data.get('model_parameters')
        if parameters:
            try:
                json.loads(parameters)
            except json.JSONDecodeError:
                raise ValidationError("Model parameters must be valid JSON")
        return parameters
    
    def clean_domain_keywords(self):
        """Validate domain keywords JSON"""
        keywords = self.cleaned_data.get('domain_keywords')
        if keywords:
            try:
                parsed = json.loads(keywords)
                if not isinstance(parsed, list):
                    raise ValidationError("Domain keywords must be a JSON array")
            except json.JSONDecodeError:
                raise ValidationError("Domain keywords must be valid JSON")
        return keywords
    
    def clean_expertise_areas(self):
        """Validate expertise areas JSON"""
        areas = self.cleaned_data.get('expertise_areas')
        if areas:
            try:
                parsed = json.loads(areas)
                if not isinstance(parsed, list):
                    raise ValidationError("Expertise areas must be a JSON array")
            except json.JSONDecodeError:
                raise ValidationError("Expertise areas must be valid JSON")
        return areas
    
    def clean_name(self):
        """Validate unique name per user"""
        name = self.cleaned_data.get('name')
        if name:
            # Check if name exists for this user (excluding current instance)
            queryset = AIAgent.objects.filter(name=name)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError("An AI agent with this name already exists")
        return name
    
    def clean(self):
        """Validate the entire form"""
        cleaned_data = super().clean()
        
        # Validate configuration using ConfigurationManager
        try:
            config = {
                'model_provider': cleaned_data.get('model_provider'),
                'model_name': cleaned_data.get('model_name'),
                'temperature': 0.7,  # Default
                'max_tokens': 1000,  # Default
                'context_window': cleaned_data.get('context_window'),
                'max_documents': cleaned_data.get('max_documents'),
                'similarity_threshold': cleaned_data.get('similarity_threshold'),
                'rate_limit_per_hour': cleaned_data.get('rate_limit_per_hour'),
                'rate_limit_per_day': cleaned_data.get('rate_limit_per_day'),
                'conversation_mode': cleaned_data.get('conversation_mode')
            }
            
            ConfigurationManager.validate_agent_config(config)
            
        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(f"Configuration validation failed: {e}")
        
        return cleaned_data


class DocumentUploadForm(forms.Form):
    """Form for uploading documents"""
    
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt,.csv,.json,.xml,.jpg,.jpeg,.png,.mp3,.mp4'
        })
    )
    
    title = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Document title (optional)'
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Document description (optional)'
        })
    )
    
    def clean_file(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 100MB)
            if file.size > 100 * 1024 * 1024:
                raise ValidationError("File size cannot exceed 100MB")
            
            # Check file type
            allowed_types = [
                'application/pdf', 'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/plain', 'text/csv', 'application/json', 'application/xml',
                'image/jpeg', 'image/png', 'image/gif',
                'audio/mpeg', 'audio/wav', 'video/mp4'
            ]
            
            if file.content_type not in allowed_types:
                raise ValidationError(f"File type {file.content_type} is not supported")
        
        return file


class FileTypeForm(forms.ModelForm):
    """Form for creating/editing file types"""
    
    class Meta:
        model = FileType
        fields = [
            'name', 'category', 'mime_types', 'extensions', 'parsers', 
            'embedding_models', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter file type name'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'mime_types': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter MIME types as JSON array'
            }),
            'extensions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter file extensions as JSON array'
            }),
            'parsers': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter parser classes as JSON array'
            }),
            'embedding_models': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter embedding models as JSON array'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_mime_types(self):
        """Validate MIME types JSON"""
        mime_types = self.cleaned_data.get('mime_types')
        if mime_types:
            try:
                parsed = json.loads(mime_types)
                if not isinstance(parsed, list):
                    raise ValidationError("MIME types must be a JSON array")
            except json.JSONDecodeError:
                raise ValidationError("MIME types must be valid JSON")
        return mime_types
    
    def clean_extensions(self):
        """Validate extensions JSON"""
        extensions = self.cleaned_data.get('extensions')
        if extensions:
            try:
                parsed = json.loads(extensions)
                if not isinstance(parsed, list):
                    raise ValidationError("Extensions must be a JSON array")
            except json.JSONDecodeError:
                raise ValidationError("Extensions must be valid JSON")
        return extensions
    
    def clean_parsers(self):
        """Validate parsers JSON"""
        parsers = self.cleaned_data.get('parsers')
        if parsers:
            try:
                parsed = json.loads(parsers)
                if not isinstance(parsed, list):
                    raise ValidationError("Parsers must be a JSON array")
            except json.JSONDecodeError:
                raise ValidationError("Parsers must be valid JSON")
        return parsers
    
    def clean_embedding_models(self):
        """Validate embedding models JSON"""
        models = self.cleaned_data.get('embedding_models')
        if models:
            try:
                parsed = json.loads(models)
                if not isinstance(parsed, list):
                    raise ValidationError("Embedding models must be a JSON array")
            except json.JSONDecodeError:
                raise ValidationError("Embedding models must be valid JSON")
        return models


class SearchForm(forms.Form):
    """Form for searching documents"""
    
    query = forms.CharField(
        max_length=1000,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter search query',
            'autofocus': True
        })
    )
    
    max_results = forms.IntegerField(
        min_value=1,
        max_value=100,
        initial=20,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        })
    )
    
    similarity_threshold = forms.FloatField(
        min_value=0.0,
        max_value=1.0,
        initial=0.7,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.01
        })
    )
    
    data_sources = forms.ModelMultipleChoiceField(
        queryset=DataSource.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        })
    )
    
    file_types = forms.ModelMultipleChoiceField(
        queryset=FileType.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['data_sources'].queryset = DataSource.objects.filter(user=user)


class BulkOperationForm(forms.Form):
    """Form for bulk operations on documents"""
    
    OPERATION_CHOICES = [
        ('delete', 'Delete'),
        ('restore', 'Restore'),
        ('reprocess', 'Reprocess'),
        ('change_source', 'Change Data Source'),
    ]
    
    operation = forms.ChoiceField(
        choices=OPERATION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    document_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    new_data_source = forms.ModelChoiceField(
        queryset=DataSource.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['new_data_source'].queryset = DataSource.objects.filter(user=user)
    
    def clean_document_ids(self):
        """Validate document IDs"""
        document_ids = self.cleaned_data.get('document_ids')
        if document_ids:
            try:
                ids = json.loads(document_ids)
                if not isinstance(ids, list):
                    raise ValidationError("Document IDs must be a JSON array")
                return ids
            except json.JSONDecodeError:
                raise ValidationError("Document IDs must be valid JSON")
        return []


class ConversationFilterForm(forms.Form):
    """Form for filtering conversations"""
    
    agent = forms.ModelChoiceField(
        queryset=AIAgent.objects.none(),
        required=False,
        empty_label="All Agents",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search conversations'
        })
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['agent'].queryset = AIAgent.objects.filter(user=user)


class ConfigurationForm(forms.ModelForm):
    """Form for user configuration"""
    
    class Meta:
        model = KnowledgeBaseConfig
        fields = [
            'default_embedding_model', 'default_chunk_size', 'default_chunk_overlap',
            'document_retention_days', 'conversation_retention_days',
            'default_similarity_threshold', 'max_search_results',
            'sync_notifications', 'error_notifications'
        ]
        widgets = {
            'default_embedding_model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., all-MiniLM-L6-v2'
            }),
            'default_chunk_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 100,
                'max': 5000
            }),
            'default_chunk_overlap': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 1000
            }),
            'document_retention_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 3650
            }),
            'conversation_retention_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 3650
            }),
            'default_similarity_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.0,
                'max': 1.0,
                'step': 0.01
            }),
            'max_search_results': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100
            }),
            'sync_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'error_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class ImportExportForm(forms.Form):
    """Form for importing/exporting data"""
    
    EXPORT_FORMATS = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('xml', 'XML'),
    ]
    
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    include_documents = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_conversations = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_agents = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_data_sources = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class ImportDataForm(forms.Form):
    """Form for importing data"""
    
    import_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.json,.csv,.xml'
        })
    )
    
    overwrite_existing = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Overwrite existing data with the same name/ID"
    )
    
    validate_before_import = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Validate data before importing"
    )
    
    def clean_import_file(self):
        """Validate import file"""
        file = self.cleaned_data.get('import_file')
        if file:
            # Check file size (max 50MB)
            if file.size > 50 * 1024 * 1024:
                raise ValidationError("Import file cannot exceed 50MB")
            
            # Check file type
            allowed_types = ['application/json', 'text/csv', 'application/xml']
            if file.content_type not in allowed_types:
                raise ValidationError(f"File type {file.content_type} is not supported")
        
        return file


class AgentTemplateForm(forms.Form):
    """Form for creating agents from templates"""
    
    template_name = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter agent name'
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter agent description'
        })
    )
    
    model_provider = forms.ChoiceField(
        choices=AIAgent.MODEL_PROVIDERS,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    model_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., gpt-3.5-turbo'
        })
    )
    
    data_sources = forms.ModelMultipleChoiceField(
        queryset=DataSource.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['data_sources'].queryset = DataSource.objects.filter(user=user)


class ChatMessageForm(forms.Form):
    """Form for chat messages"""
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Type your message...',
            'maxlength': 4000
        })
    )
    
    def clean_message(self):
        """Validate message"""
        message = self.cleaned_data.get('message')
        if message:
            # Basic validation
            if len(message.strip()) < 1:
                raise ValidationError("Message cannot be empty")
            if len(message) > 4000:
                raise ValidationError("Message cannot exceed 4000 characters")
        return message.strip()


class DocumentFilterForm(forms.Form):
    """Form for filtering documents"""
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Document.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    data_source = forms.ModelChoiceField(
        queryset=DataSource.objects.none(),
        required=False,
        empty_label="All Data Sources",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    file_type = forms.ModelChoiceField(
        queryset=FileType.objects.filter(is_active=True),
        required=False,
        empty_label="All File Types",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search documents'
        })
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['data_source'].queryset = DataSource.objects.filter(user=user)