# Generated manually for adding selected_template field to ContentIdea

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_remove_user_generated_content_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentidea',
            name='selected_template',
            field=models.CharField(blank=True, help_text='Selected template ID for post generation', max_length=100, null=True),
        ),
    ]
