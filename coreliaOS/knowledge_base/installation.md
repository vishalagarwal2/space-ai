# 🚀 Knowledge Base System - Complete Installation Guide

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **PostgreSQL**: 12 or higher
- **Redis**: 5.0 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 10GB+ available space

### Required Services
- PostgreSQL database server
- Redis server
- (Optional) Tesseract OCR for image processing
- (Optional) FFmpeg for audio/video processing

## 🔧 Step-by-Step Installation

### 1. Install System Dependencies

#### Ubuntu/Debian
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv python3-dev -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Redis
sudo apt install redis-server -y

# Install optional dependencies
sudo apt install tesseract-ocr ffmpeg -y
```

#### macOS
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 postgresql redis tesseract ffmpeg
```

#### Windows
```powershell
# Install Python from https://python.org
# Install PostgreSQL from https://www.postgresql.org/download/windows/
# Install Redis from https://redis.io/download
# Install Git from https://git-scm.com/download/win
```

### 2. Create Project Directory
```bash
mkdir knowledge-base-system
cd knowledge-base-system
```

### 3. Set up Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 4. Install Python Dependencies
Create `requirements.txt` with the provided content and install:
```bash
pip install -r requirements.txt
```

### 5. Set up Database

#### PostgreSQL Setup
```bash
# Start PostgreSQL service
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Create database and user
sudo -u postgres psql
```

In PostgreSQL shell:
```sql
CREATE DATABASE knowledge_base_db;
CREATE USER kb_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE knowledge_base_db TO kb_user;
ALTER USER kb_user CREATEDB;
\q
```

#### Enable pgvector Extension (Optional)
```sql
sudo -u postgres psql -d knowledge_base_db
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

### 6. Configure Environment Variables
Create `.env` file in project root:
```env
# Database configuration
DB_NAME=knowledge_base_db
DB_USER=kb_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Django settings
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
TIME_ZONE=UTC

# Redis configuration
REDIS_URL=redis://localhost:6379/1

# AI Model API Keys (Optional)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
COHERE_API_KEY=your_cohere_api_key

# Google API Configuration (Optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Email configuration (Optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Knowledge Base <noreply@example.com>
```

### 7. Create Project Structure
```bash
# Create the main Django project (if not exists)
django-admin startproject coreliaOS .

# Create the knowledge_base app directory
mkdir -p knowledge_base
mkdir -p knowledge_base/static/knowledge_base
mkdir -p static
mkdir -p media
mkdir -p logs
mkdir -p uploads
```

### 8. Copy Application Files
Copy all the provided Python files to their respective locations:

```
knowledge_base/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── views.py
├── urls.py
├── forms.py
├── parsers.py
├── embeddings.py
├── data_sources.py
├── ai_agents.py
├── utils.py
├── signals.py
├── tasks.py
├── celery.py
└── migrations/
    └── __init__.py
```

### 9. Update Django Settings
Update your `coreliaOS/settings.py` to include the knowledge_base app:
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'knowledge_base',
    'api',
]

# Add knowledge_base URLs
# In coreliaOS/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('knowledge-base/', include('knowledge_base.urls')),
    path('api/', include('api.urls')),
]
```

### 10. Run Database Migrations
```bash
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 11. Create Static Files
```bash
# Collect static files
python manage.py collectstatic --noinput
```

### 12. Start Services

#### Start Redis (if not running)
```bash
# Linux/macOS
redis-server

# Or as a service
sudo systemctl start redis-server  # Linux
brew services start redis          # macOS
```

#### Start Django Development Server
```bash
python manage.py runserver
```

#### Start Celery Worker (in separate terminal)
```bash
# Activate virtual environment
source venv/bin/activate

# Start Celery worker
celery -A knowledge_base worker --loglevel=info
```

#### Start Celery Beat (for periodic tasks, in separate terminal)
```bash
# Activate virtual environment
source venv/bin/activate

# Start Celery beat
celery -A knowledge_base beat --loglevel=info
```

### 13. Verify Installation

#### Check Web Interface
1. Open browser to `http://localhost:8000/knowledge-base/`
2. Login with superuser credentials
3. Verify dashboard loads correctly

#### Check Admin Interface
1. Go to `http://localhost:8000/admin/`
2. Verify all knowledge base models are visible
3. Check that default file types are created

#### Test API Health
```bash
curl http://localhost:8000/knowledge-base/api/health/
```

## 🔧 Configuration

### Google API Setup (for Gmail/Drive integration)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API and Google Drive API
4. Create OAuth 2.0 credentials
5. Download credentials JSON file
6. Place in project directory and update data source configuration

### File Processing Setup
Create directories for file processing:
```bash
mkdir -p media/uploads
mkdir -p media/processed
mkdir -p chroma_db
chmod 755 media/uploads media/processed
```

### Vector Database Setup
The system uses ChromaDB by default. For production, you might want to configure:
- Persistent storage location
- Collection naming strategy
- Performance optimization settings

## 🚀 Production Deployment

### Production Settings
Create `production.env`:
```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECRET_KEY=your-production-secret-key

# Database (consider using connection pooling)
DB_NAME=knowledge_base_production
DB_USER=kb_production_user
DB_PASSWORD=very_secure_production_password
DB_HOST=your-db-host
DB_PORT=5432

# Redis (consider using Redis Cluster)
REDIS_URL=redis://your-redis-host:6379/1

# Security settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Email (production SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your-smtp-server
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-smtp-username
EMAIL_HOST_PASSWORD=your-smtp-password
```

### Docker Deployment
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: knowledge_base_db
      POSTGRES_USER: kb_user
      POSTGRES_PASSWORD: your_secure_password

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=False
    volumes:
      - ./media:/app/media
      - ./logs:/app/logs

  celery:
    build: .
    command: celery -A knowledge_base worker --loglevel=info
    depends_on:
      - db
      - redis
    volumes:
      - ./media:/app/media
      - ./logs:/app/logs

  celery-beat:
    build: .
    command: celery -A knowledge_base beat --loglevel=info
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  redis_data:
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/staticfiles/;
    }

    location /media/ {
        alias /path/to/your/media/;
    }
}
```

## 🔍 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -l

# Test connection
python manage.py dbshell
```

#### Redis Connection Issues
```bash
# Check Redis is running
redis-cli ping

# Should return: PONG
```

#### Permission Issues
```bash
# Fix media directory permissions
sudo chown -R $USER:$USER media/
chmod -R 755 media/
```

#### Import Errors
```bash
# Check all dependencies are installed
pip check

# Reinstall requirements
pip install --force-reinstall -r requirements.txt
```

### Log Files
Check these locations for error logs:
- Django logs: `logs/django.log`
- Celery logs: Check terminal output
- PostgreSQL logs: `/var/log/postgresql/`
- Redis logs: `/var/log/redis/`

### Environment Variables
Verify environment variables are loaded:
```python
python manage.py shell
>>> import os
>>> print(os.getenv('DB_NAME'))
```

## 📚 Next Steps

1. **Configure Data Sources**: Set up Gmail, Google Drive, or file upload sources
2. **Create AI Agents**: Use templates or create custom agents
3. **Upload Documents**: Test document processing pipeline
4. **Test Chat Interface**: Verify AI agent responses
5. **Configure Monitoring**: Set up logging and health checks
6. **Optimize Performance**: Tune database queries and caching
7. **Set up Backups**: Configure regular data backups

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section
2. Review log files for error messages
3. Verify all dependencies are installed
4. Check environment variables are set correctly
5. Ensure all services (PostgreSQL, Redis) are running

For additional help:
- Check the README.md file
- Review the database diagram
- Examine the code documentation
- Test individual components

---

**System is now ready for use! 🎉**