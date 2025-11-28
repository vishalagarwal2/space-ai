# Generated migration file for Business and BusinessProfile models

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_add_selected_template_to_contentidea'),
    ]

    operations = [
        migrations.CreateModel(
            name='Business',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('password', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Business User',
                'verbose_name_plural': 'Business Users',
                'db_table': 'api_business',
            },
        ),
        migrations.CreateModel(
            name='BusinessProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('business_name', models.CharField(blank=True, max_length=255)),
                ('website_url', models.URLField(blank=True, max_length=500)),
                ('instagram_handle', models.CharField(blank=True, max_length=100)),
                ('logo_url', models.URLField(blank=True, max_length=1000, null=True)),
                ('primary_color', models.CharField(default='#3B82F6', max_length=7)),
                ('secondary_color', models.CharField(default='#10B981', max_length=7)),
                ('accent_color', models.CharField(blank=True, default='#F59E0B', max_length=7)),
                ('font_family', models.CharField(blank=True, max_length=100)),
                ('brand_mission', models.TextField(blank=True)),
                ('brand_values', models.TextField(blank=True)),
                ('business_basic_details', models.TextField(blank=True)),
                ('business_services', models.TextField(blank=True)),
                ('business_additional_details', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('business', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='api.business')),
            ],
            options={
                'verbose_name': 'Business Profile',
                'verbose_name_plural': 'Business Profiles',
                'db_table': 'api_business_profile',
            },
        ),
    ]

