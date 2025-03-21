from django.urls import path

from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('', views.ai_home, name='ai_home'),
    path('new/', views.new_chat, name='new_chat'),
    path('chat/', views.research_assistant_chat, name='research_agent'),
    path('stream/', views.research_assistant_stream, name='research_stream'),
    path('load-chat/<int:session_id>/', views.load_chat, name='load_chat'),
]
