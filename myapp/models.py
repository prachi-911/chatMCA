import uuid
from django.db import models

class ChatSession(models.Model):
    """Represents a single conversation thread."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.id}"

class Message(models.Model):
    """Represents a single message within a ChatSession."""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('model', 'Model'),
    ]
    session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=5, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_role_display()} message at {self.timestamp}"

    class Meta:
        ordering = ['timestamp']