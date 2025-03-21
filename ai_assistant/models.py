# ai_assistant/models.py
from django.db import models
from django.contrib.auth.models import User


class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = 'started_at'

    def __str__(self):
        return f"ChatSession for {self.user.username} started at {self.started_at}"


class ChatMessage(models.Model):
    SESSION_SENDER_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
    )

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SESSION_SENDER_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # Remove the formatted_content field and save override
    def __str__(self):
        return f"{self.sender.capitalize()}: {self.content[:30]}"