# Generated manually to remove 'user_generated' from ContentIdea content_type choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contentidea',
            name='content_type',
            field=models.CharField(
                choices=[
                    ('promo', 'Promotional'),
                    ('educational', 'Educational'), 
                    ('behind_scenes', 'Behind the Scenes'),
                    ('testimonial', 'Testimonial'),
                    ('holiday', 'Holiday')
                ],
                max_length=50
            ),
        ),
    ]
