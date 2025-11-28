# Generated manually to add carousel support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_update_social_media_post_for_business_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentidea',
            name='post_format',
            field=models.CharField(choices=[('single', 'Single Post'), ('carousel', 'Carousel Post')], default='single', help_text='Format of the post (single or carousel)', max_length=20),
        ),
        migrations.AddField(
            model_name='socialmediapost',
            name='carousel_layouts',
            field=models.JSONField(default=list, help_text='Array of JSON layouts for carousel slides'),
        ),
        migrations.AddField(
            model_name='socialmediapost',
            name='post_type',
            field=models.CharField(choices=[('single', 'Single Post'), ('carousel', 'Carousel Post')], default='single', help_text='Type of post (single or carousel)', max_length=20),
        ),
    ]
