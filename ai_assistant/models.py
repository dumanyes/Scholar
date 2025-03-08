from django.db import models
from django.contrib.auth.models import User

class ChatSession(models.Model):
    """
    Represents a chat session for a user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    started_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatSession for {self.user.username} started at {self.started_at}"

class ChatMessage(models.Model):
    """
    Represents an individual message in a chat session.
    """
    SESSION_SENDER_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
    )
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SESSION_SENDER_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.capitalize()}: {self.content[:30]}"

