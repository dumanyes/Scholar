import json
from channels.generic.websocket import AsyncWebsocketConsumer

from channels.db import database_sync_to_async

from projects.models import ChatRoom, ChatMessage


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data.get('message', '').strip()
        if message_content:
            room = await self.get_room(self.room_id)
            sender = self.scope['user']
            chat_message = await self.create_chat_message(room, sender, message_content)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender': sender.username,
                    'sender_avatar': await self.get_user_avatar(sender),
                    'timestamp': chat_message.timestamp.strftime("%H:%M")
                }
            )

    @database_sync_to_async
    def get_room(self, room_id):
        return ChatRoom.objects.get(id=room_id)

    @database_sync_to_async
    def create_chat_message(self, room, sender, content):
        return ChatMessage.objects.create(room=room, sender=sender, content=content)

    @database_sync_to_async
    def get_user_avatar(self, user):
        if user.profile.avatar:
            return user.profile.avatar.url
        return ''

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'sender_avatar': event['sender_avatar'],
            'timestamp': event['timestamp']
        }))