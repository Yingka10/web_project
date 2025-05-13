# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from chat.models import Message, Conversation
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("DEBUG: Attempting to connect WebSocket...") # 新增
        conversation_id_str = self.scope['url_route']['kwargs'].get('conversation_id')
        print(f"DEBUG: conversation_id_str from URL: '{conversation_id_str}'") # 新增

        if not conversation_id_str:
            print("DEBUG: Closing connection - conversation_id_str is missing.") # 新增
            await self.close()
            return

        self.room_prefix = "chat"

        try:
            self.conversation_id = int(conversation_id_str)
            print(f"DEBUG: Parsed conversation_id: {self.conversation_id}") # 新增
        except ValueError:
            print(f"DEBUG: Closing connection - ValueError converting conversation_id_str: '{conversation_id_str}'") # 新增
            await self.close()
            return

        # 檢查使用者是否已通過身份驗證
        if not self.scope["user"].is_authenticated:
            print(f"DEBUG: Closing connection - User '{self.scope['user']}' is not authenticated.") # 新增
            await self.close()
            return
        else: # 新增
            print(f"DEBUG: User '{self.scope['user']}' is authenticated.") # 新增


        self.room_group_name = f"{self.room_prefix}_{self.conversation_id}"
        print(f"DEBUG: room_group_name set to: '{self.room_group_name}'") # 新增

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        print(f"DEBUG: Added to group '{self.room_group_name}'.") # 新增

        await self.accept()
        print(f"WebSocket connected: user {self.scope['user'].username}, group {self.room_group_name}")

    async def disconnect(self, close_code):
        print(f"DEBUG: WebSocket disconnecting with code: {close_code}") # 新增
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            print(f"WebSocket disconnected: user {self.scope['user'].username}, group {self.room_group_name}")
        else:
            # 如果 self.scope['user'] 可能未驗證或為 AnonymousUser，需要安全地訪問 username
            user_display = str(self.scope.get("user", "Unknown user"))
            if hasattr(self.scope.get("user"), "username"):
                user_display = self.scope["user"].username
            print(f"WebSocket disconnected (no room_group_name set): user {user_display}")

    # async def connect(self):

    #     kwargs = self.scope.get("url_route", {}).get("kwargs", {})
    #     room_prefix = kwargs.get("room_prefix")
    #     conversation_id_str = kwargs.get("conversation_id")
    #     if not (room_prefix and conversation_id_str):
    #         await self.close()
    #         return

    #     try:
    #         conversation_id = int(conversation_id_str)
    #     except ValueError:
    #         await self.close()
    #         return

    #     self.conversation_id = conversation_id
    #     self.room_group_name = f"{room_prefix}_{conversation_id}"

    #     # 加入聊天室群組
    #     await self.channel_layer.group_add(
    #         self.room_group_name,
    #         self.channel_name
    #     )
    #     await self.accept()

    # async def disconnect(self, close_code):
    #     # 離開聊天室群組
    #     await self.channel_layer.group_discard(
    #         self.room_group_name,
    #         self.channel_name
    #     )

    # 處理來自 WebSocket 的訊息
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message')
        # sender = data.get('sender')
        # seller_id = data.get('seller_id')
        # product_id = data.get('product_id')

        # 保存訊息到資料庫
        await self.save_message(message)

        # 廣播訊息到聊天室群組
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',  # 將調用下面的 chat_message 方法
                'message': message,
                'sender': self.scope["user"].username,
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
    def save_message(self, message):
        # 根據 conversation_id 取得對話，並建立一筆新訊息
        conversation = Conversation.objects.get(pk=self.conversation_id)
        Message.objects.create(
            conversation=conversation,
            sender=self.scope["user"],
            content=message,
        )