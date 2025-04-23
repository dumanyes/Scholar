from django.urls import path, re_path
from . import consumers
from .consumers import ChatConsumer

websocket_urlpatterns = [
    path("ws/chat/<int:room_id>/", consumers.ChatConsumer.as_asgi()),
    re_path(r'^ws/chat-list/$', consumers.ChatListConsumer.as_asgi()),

    re_path(r'ws/chat/(?P<chat_id>\d+)/$', ChatConsumer.as_asgi()),
    re_path(r'ws/marketplace/$', consumers.MarketplaceConsumer.as_asgi()),
]
