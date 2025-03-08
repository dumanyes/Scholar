from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    # The home view for the AI assistant.
    path('', views.ai_home, name='ai_home'),
    # URL to create a new chat session.
    path('new_chat/', views.new_chat, name='new_chat'),
    # URL to process a chat message.
    path('chat/', views.gemini_flash_chat, name='gemini_flash_chat'),
]
