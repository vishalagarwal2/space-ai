from django.db import models
from django.contrib.auth.models import User
from uuid import uuid4

class CreateGroupModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Owner of this group")
    grp_id = models.UUIDField(default=uuid4, editable=False, unique=True, help_text="Unique group identifier")
    chat_id = models.UUIDField(default=uuid4, editable=False, unique=True, help_text="Unique chat session identifier")
    session_id = models.UUIDField(default=uuid4, editable=False, unique=True, help_text="Unique session identifier")
    agent_labels = models.JSONField(default=list, help_text="List of agent labels (e.g., ['Maavi', 'Lawanya'])")
    name = models.CharField(max_length=255, help_text="User-provided group name")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the group was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the group was last updated")

    class Meta:
        verbose_name = "Agent Group"
        verbose_name_plural = "Agent Groups"

    def __str__(self):
        return f"Group {self.grp_id} by {self.user.username}"