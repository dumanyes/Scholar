from django.urls import path, re_path
from . import consumers

websocket_urlpatterns = [
    path("ws/chat/<int:room_id>/", consumers.ChatConsumer.as_asgi()),
    re_path(r'^ws/chat-list/$', consumers.ChatListConsumer.as_asgi()),
]
