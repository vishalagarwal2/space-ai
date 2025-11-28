# 🧠 Advanced Knowledge Base System

A comprehensive, scalable knowledge base system with AI agents, multi-source data ingestion, and advanced document processing capabilities.

## 🚀 Features

### 🔌 Universal Data Source Integration
- **Gmail**: Automatically sync emails with OAuth2 authentication
- **Google Drive**: Import documents, spreadsheets, presentations
- **File Upload**: Direct file uploads with drag-and-drop support
- **Web Scraping**: Extract content from websites
- **Salesforce**: Customer data and documents (extensible)
- **API Integration**: RESTful API for custom integrations
- **Plugin Architecture**: Easy to add new data sources

### 📄 Advanced Document Processing
- **Multi-Format Support**: PDF, Word, Excel, PowerPoint, Images, Audio, Video
- **Intelligent Parsing**: OCR for images, speech-to-text for audio/video
- **Content Extraction**: Text, metadata, structured data
- **Chunking & Embedding**: Configurable text chunking with multiple embedding models
- **Version Control**: Document versioning and change tracking
- **Lifecycle Management**: Soft delete, restoration, automatic expiry

### 🤖 Configurable AI Agents
- **Multiple AI Models**: OpenAI, Anthropic, Cohere, HuggingFace support
- **Agent Templates**: Pre-built templates for common use cases
- **Conversation Modes**: Stateless, session-based, persistent, contextual memory
- **Custom Prompts**: System prompts and user prompt templates
- **Domain Expertise**: Specialized agents for specific domains
- **Rate Limiting**: Per-user, per-agent request limits
- **Usage Tracking**: Comprehensive analytics and cost tracking

### 🔍 Intelligent Search & Retrieval
- **Vector Search**: Semantic search using embeddings
- **Hybrid Search**: Combine keyword and semantic search
- **Contextual Retrieval**: Retrieve relevant documents for AI agents
- **Filtering**: By date, type, source, metadata
- **Similarity Thresholds**: Configurable relevance filtering
- **Bulk Operations**: Mass operations on documents

### 🛠️ Production-Ready Features
- **Scalable Architecture**: Horizontal scaling support
- **Caching**: Multi-level caching for performance
- **Background Processing**: Async document processing
- **Health Monitoring**: System health checks and alerting
- **Rate Limiting**: Prevent abuse and manage costs
- **User Management**: Multi-tenant with data isolation
- **Configuration Management**: Extensive customization options

## 🏗️ Architecture

### Database Schema
```
Users (Django Auth)
├── KnowledgeBaseConfig (1:1)
├── DataSources (1:N)
│   └── Documents (1:N)
│       └── DocumentChunks (1:N)
├── AIAgents (1:N)
│   └── Conversations (1:N)
│       └── Messages (1:N)
├── AgentUsage (1:N)
└── FileTypes (N:N with AIAgents)
```

### Core Components
1. **Data Sources**: Pluggable connectors for various data sources
2. **Parsers**: File type-specific content extractors
3. **Embeddings**: Multiple embedding models and vector stores
4. **AI Agents**: Configurable AI assistants with memory
5. **Knowledge Retrieval**: Context-aware document retrieval
6. **User Interface**: Web-based management interface

## 📦 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis (for caching and background tasks)
- Git

### 1. Clone the Repository
```bash
git clone <repository-url>
cd knowledge-base
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up Environment Variables
Create a `.env` file in the project root:
```env
# Database
DB_NAME=knowledge_base_db
DB_USER=kb_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Redis
REDIS_URL=redis://localhost:6379/1

# API Keys (Optional)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
COHERE_API_KEY=your_cohere_api_key

# Google API (for Gmail/Drive integration)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### 5. Database Setup
```bash
# Create PostgreSQL database
createdb knowledge_base_db

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 6. Install Additional Dependencies

#### For OCR Support (Optional)
```bash
# Install Tesseract
sudo apt-get install tesseract-ocr  # Ubuntu/Debian
brew install tesseract  # macOS

# Install EasyOCR
pip install easyocr
```

#### For Audio/Video Processing (Optional)
```bash
# Install FFmpeg
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg  # macOS

# Install Python packages
pip install whisper pydub opencv-python
```

### 7. Start the Development Server
```bash
python manage.py runserver
```

Visit `http://localhost:8000/knowledge-base/` to access the knowledge base interface.

## 🔧 Configuration

### Data Source Configuration

#### Gmail Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create credentials (OAuth 2.0 Client ID)
5. Download credentials JSON file
6. Configure in data source:
```json
{
  "credentials_file": "path/to/credentials.json",
  "token_file": "path/to/token.json",
  "query": "is:unread",
  "max_results": 100
}
```

#### Google Drive Setup
1. Enable Google Drive API in Google Cloud Console
2. Use same OAuth credentials as Gmail
3. Configure in data source:
```json
{
  "credentials_file": "path/to/credentials.json",
  "token_file": "path/to/token.json",
  "file_types": ["application/pdf", "text/plain"],
  "max_results": 100
}
```

#### File Upload Setup
```json
{
  "upload_dir": "uploads/",
  "allowed_extensions": [".pdf", ".docx", ".txt", ".jpg"],
  "max_file_size": 104857600
}
```

### AI Agent Configuration

#### OpenAI Agent
```json
{
  "model_name": "gpt-3.5-turbo",
  "temperature": 0.7,
  "max_tokens": 1000,
  "api_key": "your-openai-api-key"
}
```

#### Anthropic Agent
```json
{
  "model_name": "claude-3-sonnet-20240229",
  "temperature": 0.7,
  "max_tokens": 1000,
  "api_key": "your-anthropic-api-key"
}
```

### Embedding Configuration

#### Sentence Transformers
```json
{
  "model_name": "all-MiniLM-L6-v2",
  "dimension": 384,
  "max_tokens": 512
}
```

#### OpenAI Embeddings
```json
{
  "model_name": "text-embedding-ada-002",
  "dimension": 1536,
  "api_key": "your-openai-api-key"
}
```

### Vector Store Configuration

#### ChromaDB (Default)
```json
{
  "persist_directory": "./chroma_db",
  "collection_name": "user_documents"
}
```

#### FAISS (Optional)
```json
{
  "dimension": 384,
  "index_file": "./faiss_index.index",
  "metadata_file": "./faiss_metadata.json"
}
```

## 🚀 Usage

### 1. Create Data Sources
1. Go to Data Sources in the web interface
2. Click "Add Data Source"
3. Select source type (Gmail, Google Drive, File Upload, etc.)
4. Configure authentication and settings
5. Click "Create and Sync"

### 2. Create AI Agents
1. Go to AI Agents
2. Click "Create Agent"
3. Choose from templates or create custom
4. Configure model, prompts, and knowledge base access
5. Set rate limits and conversation settings

### 3. Upload Documents
1. Go to Documents
2. Click "Upload" or drag and drop files
3. Documents are automatically processed and indexed
4. View processing status and extracted content

### 4. Chat with Agents
1. Go to AI Agents
2. Click "Chat" on any active agent
3. Start conversation - agent will use knowledge base context
4. View cited sources and conversation history

### 5. Search Knowledge Base
1. Use the search bar to find relevant documents
2. Apply filters by date, type, source
3. View similarity scores and document previews
4. Access full document content

## 🔍 API Usage

### Authentication
All API endpoints require authentication. Use Django's built-in authentication or add API key authentication.

### Search Documents
```bash
curl -X GET "http://localhost:8000/knowledge-base/api/search/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -G -d "q=machine learning" -d "max_results=10"
```

### Chat with Agent
```bash
curl -X POST "http://localhost:8000/knowledge-base/api/chat/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-uuid",
    "message": "What is machine learning?",
    "conversation_id": "conversation-uuid"
  }'
```

### Upload Document
```bash
curl -X POST "http://localhost:8000/knowledge-base/api/upload/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "title=My Document"
```

## 🛠️ Customization

### Adding New Data Sources
1. Create a new class inheriting from `BaseDataSource`
2. Implement required methods: `authenticate()`, `sync()`, `get_documents()`
3. Register in `DataSourceRegistry`

```python
class CustomDataSource(BaseDataSource):
    def authenticate(self) -> bool:
        # Implement authentication logic
        return True
    
    def sync(self) -> Dict[str, Any]:
        # Implement sync logic
        return {'status': 'success', 'processed_count': 0}
    
    def get_documents(self) -> Iterator[Dict[str, Any]]:
        # Yield document data
        yield {'title': 'Document', 'content': 'Content'}

# Register the data source
data_source_registry.register_source('custom', CustomDataSource)
```

### Adding New Parsers
1. Create a new class inheriting from `BaseParser`
2. Implement required methods: `can_parse()`, `parse()`
3. Register in `ParserRegistry`

```python
class CustomParser(BaseParser):
    def can_parse(self, file_path: str, mime_type: str) -> bool:
        return file_path.endswith('.custom')
    
    def parse(self, file_path: str, **kwargs) -> Dict[str, Any]:
        # Parse file and return content
        return {'content': 'parsed content', 'metadata': {}}

# Register the parser
parser_registry.register_parser(CustomParser())
```

### Adding New AI Models
1. Create a new class inheriting from `BaseAIModel`
2. Implement `generate_response()` method
3. Register in `AIAgentExecutor`

```python
class CustomAIModel(BaseAIModel):
    async def generate_response(self, messages: List[Dict[str, str]], 
                               context: str = "", **kwargs) -> Dict[str, Any]:
        # Generate response using custom model
        return {
            'content': 'Generated response',
            'usage': {'total_tokens': 100}
        }
```

## 📊 Monitoring and Analytics

### System Health
- Document processing success/failure rates
- AI agent response times and error rates
- Vector store performance metrics
- Background task queue status

### Usage Analytics
- User activity and engagement metrics
- Document upload and processing statistics
- AI agent usage and conversation metrics
- Cost tracking and optimization insights

### Performance Monitoring
- Database query performance
- Vector search latency
- Memory and CPU usage
- API response times

## 🔒 Security

### Data Protection
- User data isolation in multi-tenant environment
- Encrypted storage of API keys and sensitive data
- Secure file upload with virus scanning
- Access control and permission management

### API Security
- Rate limiting to prevent abuse
- Input validation and sanitization
- CORS configuration for web clients
- Authentication and authorization

### Privacy
- Data retention policies
- Soft delete for data recovery
- Export and deletion of user data
- Compliance with privacy regulations

## 🚀 Deployment

### Production Deployment
1. Set up PostgreSQL database
2. Configure Redis for caching
3. Set up background task processing (Celery)
4. Configure web server (Nginx + Gunicorn)
5. Set up monitoring and logging
6. Configure backup and disaster recovery

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### Environment Variables for Production
```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379/1

# Security settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test knowledge_base.tests.test_parsers

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Data Sources
```python
from knowledge_base.data_sources import FileUploadDataSource
from knowledge_base.models import DataSource

# Create test data source
data_source = DataSource.objects.create(
    user=user,
    name="Test Source",
    source_type="file_upload",
    config={"upload_dir": "test_uploads/"}
)

# Test sync
source_instance = FileUploadDataSource(data_source)
result = source_instance.sync()
```

## 📚 Documentation

### API Documentation
- OpenAPI/Swagger documentation available at `/api/docs/`
- Interactive API testing interface
- Code examples for different programming languages

### User Documentation
- Web-based help system
- Video tutorials and walkthroughs
- Best practices and use cases
- FAQ and troubleshooting guides

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests for new functionality
5. Run tests and ensure they pass
6. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write comprehensive docstrings
- Add unit tests for new features

### Issue Reporting
- Use GitHub issues for bug reports
- Include reproduction steps
- Provide system information
- Add relevant logs and error messages

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🙏 Acknowledgments

- [LangChain](https://github.com/hwchase17/langchain) for AI agent framework
- [ChromaDB](https://github.com/chroma-core/chroma) for vector database
- [Sentence Transformers](https://github.com/UKPLab/sentence-transformers) for embeddings
- [Django](https://www.djangoproject.com/) for web framework
- [OpenAI](https://openai.com/) for AI models
- [Anthropic](https://www.anthropic.com/) for Claude models

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review existing issues and discussions
- Contact the maintainers

---

**Built with ❤️ for the future of knowledge management**
