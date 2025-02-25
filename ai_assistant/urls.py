from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('', views.ai_home, name='ai_home'),  # This now serves at /ai-assistant/
    path('chat/', views.gemini_flash_chat, name='gemini_flash_chat'),
]
