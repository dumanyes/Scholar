import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from projects.models import ChatRoom, ChatMessage
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"[DEBUG] User {self.scope['user']} connected to room {self.room_id}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data.get('message', '').strip()
        if message_content:
            room = await self.get_room(self.room_id)
            sender = self.scope['user']
            chat_message = await self.create_chat_message(room, sender, message_content)

            # Broadcast the new message to everyone in the room.
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender': sender.username,
                    'sender_id': sender.id,
                    'sender_avatar': await self.get_user_avatar(sender),
                    'timestamp': chat_message.timestamp.strftime("%H:%M")
                }
            )

            # For each participant, broadcast updated unread count.
            participants = await self.get_room_participants(room)
            for participant in participants:
                # For the sender, unread_count is zero.
                if participant == sender:
                    unread_count = 0
                else:
                    unread_count = await self.get_unread_count(room, participant)
                await self.channel_layer.group_send(
                    f"chatlist_{participant.id}",
                    {
                        'type': 'chatlist_update',
                        'data': {
                            'chat_id': room.id,
                            'unread_count': unread_count,
                            'last_message': message_content,
                            'timestamp': chat_message.timestamp.strftime("%H:%M"),
                            'sender_id': sender.id
                        }
                    }
                )
                print(f"[DEBUG] Room {room.id}: Broadcast unread_count {unread_count} for user {participant.id}")

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

    @database_sync_to_async
    def get_room_participants(self, room):
        return list(room.participants.all())

    @database_sync_to_async
    def get_unread_count(self, room, user):
        # Only count messages not sent by the user that are still unread.
        return room.messages.filter(read=False).exclude(sender=user).count()

    async def chat_message(self, event):
        # Sends the new message to the chat page.
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'sender_avatar': event['sender_avatar'],
            'timestamp': event['timestamp']
        }))


class ChatListConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            self.user = self.scope["user"]
            self.group_name = f"chatlist_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            print(f"[DEBUG] ChatListConsumer connected for user {self.user.id}")
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f"[DEBUG] ChatListConsumer disconnected for user {self.user.id}")

    async def receive(self, text_data):
        # Optionally handle "typing" events, etc.
        pass

    async def chatlist_update(self, event):
        data = event["data"]
        print(f"[DEBUG] ChatListConsumer received update: {data}")
        # Immediately forward the update to the client.
        await self.send(text_data=json.dumps(data))

class MarketplaceConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            self.user = self.scope["user"]
            self.group_name = f"marketplace_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content):
        pass

    async def send_update(self, event):
        await self.send_json(event["data"])
