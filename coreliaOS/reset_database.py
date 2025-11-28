#!/usr/bin/env python
"""
Database Reset Script for Content Calendar Issues
This script will reset the database and recreate it with proper migrations
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coreliaOS.settings')
django.setup()

def reset_database():
    """Reset the database completely"""
    print("🔄 Resetting database...")
    
    # Remove existing database
    if os.path.exists('db.sqlite3'):
        os.remove('db.sqlite3')
        print("✅ Removed old database")
    
    # Remove migration files (but keep __init__.py)
    for app in ['api', 'knowledge_base', 'agent_tagging']:
        migrations_dir = f"{app}/migrations"
        if os.path.exists(migrations_dir):
            for file in os.listdir(migrations_dir):
                if file.endswith('.py') and file != '__init__.py':
                    os.remove(os.path.join(migrations_dir, file))
                    print(f"✅ Removed {app}/migrations/{file}")
    
    print("🔄 Creating fresh migrations...")
    
    # Create new migrations
    execute_from_command_line(['manage.py', 'makemigrations'])
    
    print("🔄 Applying migrations...")
    
    # Apply migrations
    execute_from_command_line(['manage.py', 'migrate'])
    
    print("🔄 Creating superuser...")
    
    # Create superuser
    from django.contrib.auth.models import User
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("✅ Created superuser (admin/admin123)")
    
    print("🎉 Database reset completed successfully!")
    print("🚀 You can now restart your Django server")

if __name__ == '__main__':
    reset_database()
