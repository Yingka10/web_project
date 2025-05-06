# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from mywebsite.models import ChatMessage
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 取得 URL 的 room_name
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # 加入聊天室群組
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # 離開聊天室群組
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # 處理來自 WebSocket 的訊息
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message')
        sender = data.get('sender')
        seller_id = data.get('seller_id')
        product_id = data.get('product_id')

        # 保存訊息到資料庫
        await self.save_message(sender, message, seller_id, product_id)

        # 廣播訊息到聊天室群組
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',  # 將調用下面的 chat_message 方法
                'message': message,
                'sender': sender,
            }
        )

    # 接收群組訊息，並發送回 WebSocket
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
        }))

    # 藉由同步函式保存訊息
    @database_sync_to_async
    def save_message(self, sender, message, seller_id, product_id):
        ChatMessage.objects.create(
            sender=sender,
            content=message,
            seller_id=seller_id,
            product_id=product_id,
        )