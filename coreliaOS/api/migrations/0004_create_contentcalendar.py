# Alter ContentCalendar model to support business users

import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_add_selected_template_to_contentidea"),
        ("api", "0003_business_businessprofile"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Remove the unique_together constraint first (if it exists)
        migrations.AlterUniqueTogether(
            name="contentcalendar",
            unique_together=set(),
        ),
        # Make user field nullable
        migrations.AlterField(
            model_name="contentcalendar",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="content_calendars",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Add business_id field
        migrations.AddField(
            model_name="contentcalendar",
            name="business_id",
            field=models.UUIDField(
                blank=True,
                help_text="Business user ID for business-created calendars",
                null=True,
            ),
        ),
        # Add constraint to ensure either user or business_id is set
        migrations.AddConstraint(
            model_name="contentcalendar",
            constraint=models.CheckConstraint(
                check=models.Q(
                    ("user__isnull", False),
                    ("business_id__isnull", False),
                    _connector="OR",
                ),
                name="content_calendar_user_or_business_required",
            ),
        ),
    ]
