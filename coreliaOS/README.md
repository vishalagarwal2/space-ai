# CoreliaOS - Django Web Application

A comprehensive Django web application configured with PostgreSQL database, Redis caching, and environment-based configuration. Supports multiple deployment options from local development to production on AWS EC2.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Setup Options](#setup-options)
  - [Option A: Docker Setup (Recommended)](#option-a-docker-setup-recommended)
  - [Option B: Local Setup with Conda](#option-b-local-setup-with-conda)
- [Development Server](#development-server)
- [Production Deployment](#production-deployment)
  - [AWS EC2 Deployment](#aws-ec2-deployment)
  - [Local Production Setup](#local-production-setup)
- [Environment Configuration](#environment-configuration)
- [Common Commands](#common-commands)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 📦 Prerequisites

### Required Software
- **Python 3.12** (for local development)
- **Docker & Docker Compose** (for containerized setup)
- **Git** (for version control)
- **PostgreSQL** (if not using Docker)
- **Redis** (optional, for caching)

### Cloud Requirements (for AWS deployment)
- **AWS Account** with EC2 access
- **AWS CLI** configured
- **Key Pair** for EC2 instance access

## 🚀 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd coreliaos

# Copy environment configuration
cp .env.example .env

# Edit .env with your preferred settings
nano .env

# Choose your setup method below
```

## 🛠️ Setup Options

### Option A: Docker Setup (Recommended)

#### Database Only (Run Django locally)
```bash
# Start PostgreSQL, pgAdmin, and Redis
docker-compose -f docker-compose.db.yml up -d

# Setup local environment
conda create -n coreliaos python=3.12
conda activate coreliaos
pip install -r requirements.txt

# Run migrations and start server
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
celery -A coreliaOS worker --pool=threads --concurrency=4 --loglevel=info --loglevel=info (in separate terminal)
celery -A coreliaOS beat --loglevel=info (in separate terminal)
```

#### Complete Containerized Setup
```bash
# Build and start all services
docker-compose -f docker-compose.dev.yml up --build

# In another terminal, run migrations
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

### Option B: Local Setup with Conda

#### 1. Environment Setup
```bash
# Create and activate conda environment
conda create -n coreliaos python=3.12
conda activate coreliaos

# Install Django first
conda install django

# Install remaining dependencies
pip install psycopg2-binary python-dotenv whitenoise

# Or install all from requirements.txt
pip install -r requirements.txt
```

#### 3. Database Setup (PostgreSQL)

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Create Database:**
```bash
sudo -u postgres psql
CREATE DATABASE coreliaos_db;
CREATE USER coreliaos_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE coreliaos_db TO coreliaos_user;
\q
```

#### 4. Redis Setup (Optional)

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### 5. Generate Django Secret Key

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the generated key and paste it as the `SECRET_KEY` value in your `.env` file.

#### 6. Run Migrations

```bash
# Create and apply database migrations
python manage.py makemigrations
python manage.py migrate
```

#### 7. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

#### 8. Run the Development Server

```bash
python manage.py runserver
celery -A coreliaOS worker --pool=threads --concurrency=4 --loglevel=info --loglevel=info (in separate terminal)
celery -A coreliaOS beat --loglevel=info (in separate terminal)
```

Visit `http://127.0.0.1:8000/` in your browser to see the Django welcome page.

## 🔧 Development Server

### Local Development
```bash
# Activate environment
conda activate coreliaos

# Create your first app (if not already created)
python manage.py startapp api

# Apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (if not created)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Start development server
python manage.py runserver
celery -A coreliaOS worker --pool=threads --concurrency=4 --loglevel=info --loglevel=info (in separate terminal)
celery -A coreliaOS beat --loglevel=info (in separate terminal)

# Access the application
# Django API: http://127.0.0.1:8000
# Admin: http://127.0.0.1:8000/admin
```

### API Endpoints

The application includes a comprehensive API with session-based authentication:

#### Public APIs (No Authentication Required)
- `GET /` - Welcome page with API endpoint list
- `GET /api/public/` - Public API endpoint
- `GET /api/auth/status/` - Check authentication status

#### Authentication APIs
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout

#### Protected APIs (Authentication Required)
- `GET /api/protected/` - Protected API endpoint
- `GET /api/user/profile/` - Get user profile
- `PUT /api/user/update/` - Update user profile

#### Admin APIs (Admin/Staff Only)
- `GET /api/admin/users/` - Get all users (admin only)

### API Testing

#### Using curl:
```bash
# Test public API
curl -X GET http://127.0.0.1:8000/api/public/

# Register a new user
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}' \
  -c cookies.txt

# Login
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}' \
  -c cookies.txt

# Access protected API
curl -X GET http://127.0.0.1:8000/api/protected/ \
  -b cookies.txt
```

#### Using Postman:
1. Import the provided Postman collection (`CoreliaOS_API_Collection.json`)
2. Import the environment file (`CoreliaOS_Environment.json`)
3. Update admin credentials in the environment
4. Run the collection to test all endpoints

**Postman Collection Features:**
- ✅ All API endpoints covered
- ✅ Automated testing scripts
- ✅ Session cookie handling
- ✅ Error case testing
- ✅ Environment variables for easy configuration

### Docker Development
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up

# Access services:
# Django: http://localhost:8000
# pgAdmin: http://localhost:8080
# PostgreSQL: localhost:5432
```

## 🚀 Production Deployment

### AWS EC2 Deployment

#### 1. Launch EC2 Instance
```bash
# Launch Ubuntu 20.04 LTS instance
# Instance type: t3.medium or larger
# Security Group: Allow HTTP (80), HTTPS (443), SSH (22)
```

#### 2. Connect to EC2 Instance
```bash
# Connect via SSH
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y
```

#### 3. Install Dependencies
```bash
# Install Python, pip, and system dependencies
sudo apt install python3.12 python3.12-venv python3-pip nginx postgresql postgresql-contrib redis-server git -y

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
```

#### 4. Setup Application
```bash
# Clone repository
git clone <repository-url>
cd coreliaos

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
nano .env
```

Install poppler
Install ffmpeg
Install tesseract

#### 5. Configure Environment for Production
```bash
# Edit .env file
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-ec2-ip
SECRET_KEY=your-production-secret-key
DB_HOST=localhost
DB_NAME=coreliaos_prod
DB_USER=coreliaos_prod
DB_PASSWORD=your-strong-password
```

#### 6. Database Setup
```bash
# Configure PostgreSQL
sudo -u postgres psql
CREATE DATABASE coreliaos_prod;
CREATE USER coreliaos_prod WITH PASSWORD 'your-strong-password';
GRANT ALL PRIVILEGES ON DATABASE coreliaos_prod TO coreliaos_prod;
\q

# Run migrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

#### 7. Setup Gunicorn
```bash
# Test Gunicorn
gunicorn --bind 0.0.0.0:8000 coreliaOS.wsgi

# Create Gunicorn service
sudo nano /etc/systemd/system/coreliaos.service
```

**Gunicorn Service Configuration:**
```ini
[Unit]
Description=CoreliaOS Django Application
After=network.target

[Service]
Type=notify
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/coreliaos
Environment=PATH=/home/ubuntu/coreliaos/venv/bin
EnvironmentFile=/home/ubuntu/coreliaos/.env
ExecStart=/home/ubuntu/coreliaos/venv/bin/gunicorn --workers 3 --bind unix:/home/ubuntu/coreliaos/coreliaos.sock coreliaOS.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

#### 8. Configure Nginx
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/coreliaos
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com your-ec2-ip;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /home/ubuntu/coreliaos;
    }
    
    location /media/ {
        root /home/ubuntu/coreliaos;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/coreliaos/coreliaos.sock;
    }
}
```

#### 9. Enable Services
```bash
# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/coreliaos /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

# Enable Gunicorn service
sudo systemctl start coreliaos
sudo systemctl enable coreliaos
sudo systemctl status coreliaos
```

#### 10. SSL Certificate (Optional)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### Local Production Setup

#### Using Docker (Recommended)
```bash
# Create production docker-compose
cp docker-compose.dev.yml docker-compose.prod.yml

# Edit for production settings
# Set DEBUG=False, use production database, etc.

# Start production services
docker-compose -f docker-compose.prod.yml up -d --build
```

#### Using Gunicorn Locally
```bash
# Install production dependencies
pip install gunicorn

# Set production environment
export DEBUG=False
export ALLOWED_HOSTS=localhost,127.0.0.1

# Run with Gunicorn
gunicorn --bind 0.0.0.0:8000 coreliaOS.wsgi:application
```

## 🔧 Environment Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | `django-insecure-...` |
| `DEBUG` | Debug mode | `True` / `False` |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `DB_NAME` | Database name | `coreliaos_db` |
| `DB_USER` | Database user | `coreliaos_user` |
| `DB_PASSWORD` | Database password | `secure_password` |
| `DB_HOST` | Database host | `localhost` / `db` |
| `DB_PORT` | Database port | `5432` |
| `TIME_ZONE` | Timezone | `UTC` |
| `REDIS_URL` | Redis URL | `redis://localhost:6379/1` |

### Environment-Specific Settings

**Development:**
```env
DEBUG=True
DB_HOST=localhost
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Docker:**
```env
DEBUG=True
DB_HOST=db
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Production:**
```env
DEBUG=False
DB_HOST=your-db-host
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

## 📁 Project Structure

```
coreliaos/
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── .env.example                # Environment template
├── .env                        # Environment variables (not in git)
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
├── Dockerfile                  # Docker configuration
├── docker-compose.db.yml       # Database-only Docker setup
├── docker-compose.dev.yml      # Development Docker setup
├── CoreliaOS_API_Collection.json # Postman collection
├── CoreliaOS_Environment.json   # Postman environment
├── coreliaOS/                  # Django project directory
│   ├── __init__.py
│   ├── settings.py             # Django settings
│   ├── urls.py                 # URL routing
│   ├── wsgi.py                 # WSGI configuration
│   └── asgi.py                 # ASGI configuration
├── api/                        # API app directory
│   ├── __init__.py
│   ├── models.py               # Database models
│   ├── views.py                # API views
│   ├── urls.py                 # API URL routing
│   ├── admin.py                # Admin configuration
│   ├── apps.py                 # App configuration
│   └── tests.py                # API tests
├── static/                     # Static files (CSS, JS, images)
├── media/                      # User uploaded files
├── staticfiles/                # Collected static files
└── logs/                       # Application logs
```

## 🔨 Common Commands

### Docker Commands
```bash
# Development with database only
docker-compose -f docker-compose.db.yml up -d
docker-compose -f docker-compose.db.yml down

# Full development environment
docker-compose -f docker-compose.dev.yml up --build
docker-compose -f docker-compose.dev.yml down

# Execute commands in containers
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
docker-compose -f docker-compose.dev.yml exec web python manage.py shell
docker-compose -f docker-compose.db.yml exec db psql -U coreliaos_user -d coreliaos_db

# View logs
docker-compose -f docker-compose.dev.yml logs -f web
docker-compose -f docker-compose.db.yml logs -f db
```

### Django Management Commands
```bash
# App management
python manage.py startapp app_name

# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py dbshell

# User management
python manage.py createsuperuser
python manage.py changepassword username

# Static files
python manage.py collectstatic
python manage.py findstatic filename

# Development
python manage.py runserver
celery -A coreliaOS worker --pool=threads --concurrency=4 --loglevel=info --loglevel=info (in separate terminal)
celery -A coreliaOS beat --loglevel=info (in separate terminal)
python manage.py shell
python manage.py test

# API testing
python manage.py shell
# >>> from django.test import Client
# >>> c = Client()
# >>> response = c.get('/api/public/')
# >>> print(response.json())

# Production
python manage.py check --deploy
gunicorn coreliaOS.wsgi:application
```

### System Administration
```bash
# Service management (Ubuntu/Debian)
sudo systemctl start coreliaos
sudo systemctl stop coreliaos
sudo systemctl restart coreliaos
sudo systemctl status coreliaos

# Nginx management
sudo systemctl restart nginx
sudo systemctl reload nginx
sudo nginx -t

# Database backup
pg_dump -h localhost -U coreliaos_user coreliaos_db > backup.sql

# View application logs
tail -f logs/django.log
sudo journalctl -u coreliaos -f
```

## 🔍 Troubleshooting

### Common Issues & Solutions

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
psql -h localhost -U coreliaos_user -d coreliaos_db

# Reset database password
sudo -u postgres psql
ALTER USER coreliaos_user PASSWORD 'new_password';
```

#### Missing Python Packages
```bash
# Install missing packages individually
pip install whitenoise
pip install django-redis
pip install psycopg2-binary

# Or install all requirements
pip install -r requirements.txt
```

#### Environment File Issues
- **Problem**: Inline comments in `.env` file cause parsing errors
- **Solution**: Use separate lines for comments
  ```env
  # This is correct
  DB_PASSWORD=myPassword123
  
  # This is wrong and will cause errors:
  # DB_PASSWORD=myPassword123  # inline comment
  ```

#### Docker Container Issues
```bash
# If database user doesn't exist, recreate containers
docker-compose -f docker-compose.db.yml down -v
docker-compose -f docker-compose.db.yml up -d

# Wait for database to initialize
sleep 15

# Check container logs
docker-compose -f docker-compose.db.yml logs db
```

#### Static Files Not Loading
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check static files configuration
python manage.py findstatic admin/css/base.css

# Fix permissions
sudo chown -R www-data:www-data /path/to/static/
```

#### Docker Issues
```bash
# Rebuild containers
docker-compose -f docker-compose.dev.yml up --build --force-recreate

# Remove all containers and volumes
docker-compose -f docker-compose.dev.yml down -v
docker system prune -a

# Check container logs
docker logs container_name
```

#### Production Issues
```bash
# Check Gunicorn service
sudo systemctl status coreliaos
sudo journalctl -u coreliaos -f

# Check Nginx configuration
sudo nginx -t
sudo systemctl status nginx

# Check file permissions
ls -la /home/ubuntu/coreliaos/
sudo chown -R ubuntu:www-data /home/ubuntu/coreliaos/
```

### Performance Optimization

#### Database Optimization
```bash
# Create database indexes
python manage.py dbshell
CREATE INDEX idx_model_field ON app_model(field);

# Analyze database performance
python manage.py shell
from django.db import connection
print(connection.queries)
```

#### Caching
```bash
# Test Redis connection
redis-cli ping

# Clear cache
python manage.py shell
from django.core.cache import cache
cache.clear()
```

## 📊 Monitoring and Logs

### Log Files
- **Django Application:** `logs/django.log`
- **Gunicorn:** `sudo journalctl -u coreliaos`
- **Nginx:** `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- **PostgreSQL:** `/var/log/postgresql/postgresql-*.log`

### Health Checks
```bash
# Application health
curl -f http://localhost:8000/admin/login/ || echo "App down"

# Database health
python manage.py dbshell -c "SELECT 1;"

# Redis health
redis-cli ping
```

## 🛡️ Security Considerations

### Production Security Checklist
- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` generated
- [ ] Database credentials secured
- [ ] HTTPS enabled with SSL certificate
- [ ] Firewall configured (only allow necessary ports)
- [ ] Regular security updates applied
- [ ] Backup strategy implemented
- [ ] Error logging configured
- [ ] Rate limiting implemented
- [ ] CSRF protection enabled

### Backup Strategy
```bash
# Database backup
pg_dump -h localhost -U coreliaos_user coreliaos_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Media files backup
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz media/

# Automated backup script
#!/bin/bash
DB_BACKUP="/backups/db_backup_$(date +%Y%m%d_%H%M%S).sql"
pg_dump -h localhost -U coreliaos_user coreliaos_db > $DB_BACKUP
aws s3 cp $DB_BACKUP s3://your-backup-bucket/
```

## 🤝 Contributing

### Development Workflow
1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/new-feature`
3. **Make changes and test thoroughly**
4. **Run tests:** `python manage.py test`
5. **Check code style:** `flake8 .`
6. **Commit changes:** `git commit -m "Add new feature"`
7. **Push to branch:** `git push origin feature/new-feature`
8. **Create Pull Request**

### Code Style Guidelines
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for functions and classes
- Write tests for new features
- Update documentation as needed

### Testing
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test api

# Run specific test class
python manage.py test api.tests.APITestCase

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html

# API testing examples
python manage.py shell
>>> from django.test import Client
>>> c = Client()
>>> response = c.get('/api/public/')
>>> print(response.json())
>>> 
>>> # Test authentication
>>> response = c.post('/api/auth/login/', {'username': 'testuser', 'password': 'testpass123'})
>>> print(response.json())
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- **Issues:** GitHub Issues
- **Documentation:** This README
- **Email:** support@coreliaos.com

---

## 🎯 Next Steps

After successful setup, here are recommended next steps:

### 1. **API Development**
- **Extend the API**: Add more endpoints for your specific use case
- **Add API documentation**: Consider using Django REST Framework with Swagger
- **Implement rate limiting**: Add throttling for API endpoints
- **Add API versioning**: Structure for future API versions

### 2. **Frontend Integration**
- **React/Vue.js**: Build a frontend that consumes your API
- **Mobile app**: Create a mobile app using React Native or Flutter
- **API client libraries**: Generate client libraries for different languages

### 3. **Enhanced Features**
- **Email verification**: Add email verification for registration
- **Password reset**: Implement password reset functionality
- **Two-factor authentication**: Add 2FA for enhanced security
- **Social login**: Integrate OAuth with Google, GitHub, etc.

### 4. **Database Models**
- **Custom models**: Create models specific to your application
- **Database relationships**: Set up proper foreign keys and relationships
- **Database migrations**: Learn advanced migration techniques

### 5. **DevOps & Deployment**
- **CI/CD pipeline**: Set up GitHub Actions or GitLab CI
- **Container orchestration**: Use Docker Compose or Kubernetes
- **Monitoring**: Add application monitoring with Sentry or DataDog
- **Backup strategy**: Implement automated database backups

### 6. **Testing & Quality**
- **API tests**: Write comprehensive API tests
- **Integration tests**: Test full application workflows
- **Load testing**: Test API performance under load
- **Code quality**: Add linting, formatting, and pre-commit hooks

### 7. **Documentation**
- **API documentation**: Use tools like Swagger/OpenAPI
- **Code documentation**: Add docstrings and type hints
- **User guides**: Create guides for different user types
- **Architecture documentation**: Document system design

### Quick Start Commands:
```bash
# Create a new app for your specific domain
python manage.py startapp your_app_name

# Add models to api/models.py
# Add views to api/views.py  
# Add URLs to api/urls.py

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Test your new endpoints
curl -X GET http://127.0.0.1:8000/api/your-endpoint/
```

Happy coding! 🚀