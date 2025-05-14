# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from chat.models import Message, Conversation
from channels.db import database_sync_to_async
from django.utils import timezone 

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
        message_content = data.get('message')
        # sender = data.get('sender')
        # seller_id = data.get('seller_id')
        # product_id = data.get('product_id')

        if not message_content: # 簡單驗證
            print("DEBUG receive: Received empty message content.")
            return
        print(f"DEBUG receive: Received message content: '{message_content[:50]}...' from user: {self.scope['user'].username}")

        # 保存訊息到資料庫
        await self.save_message(message_content)

        # 廣播訊息到聊天室群組
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',  # 將調用下面的 chat_message 方法
                'message': message_content,
                'sender': self.scope["user"].username,
            }
        )
        print(f"DEBUG receive: Message sent to group {self.room_group_name}")

    # 接收群組訊息，並發送回 WebSocket
    async def chat_message(self, event):
        message_to_send = event['message']
        sender_username = event['sender']
        
        # 非常重要的日誌：記錄是哪個用戶的 Consumer 實例在處理哪個事件
        print(f"DEBUG chat_message: 消費者實例 (用戶 '{self.scope['user'].username}', 群組 '{self.room_group_name}') "
          f"正在處理來自發送者 '{sender_username}' 的訊息: '{message_to_send[:50]}...'")
    
        print(f"DEBUG chat_message: Sending message to WebSocket client: '{message_to_send[:50]}...' from sender: {sender_username}")

        await self.send(text_data=json.dumps({
            'message': message_to_send,
            'sender': sender_username,
        }))
        print(f"DEBUG chat_message: 訊息已通過 WebSocket 由消費者實例 (用戶 '{self.scope['user'].username}') 發送")

    # 藉由同步函式保存訊息
    @database_sync_to_async
    def save_message(self, message_content_param):
        try:
            current_user = self.scope["user"]
            print(f"DEBUG save_message: Attempting to save message for conversation_id: {self.conversation_id}, user: {current_user.username}")
            
            conversation_obj = Conversation.objects.get(pk=self.conversation_id)
            
            new_msg = Message.objects.create(
                conversation=conversation_obj,
                sender=current_user,
                content=message_content_param, # 使用傳入的參數
            )
            print(f"DEBUG save_message: Message saved with ID: {new_msg.id}, content: '{new_msg.content[:30]}...'")

            # 更新對話的 updated_at 時間戳
            conversation_obj.updated_at = timezone.now()
            conversation_obj.save(update_fields=['updated_at']) # 只更新 updated_at 字段
            print(f"DEBUG save_message: Conversation {conversation_obj.id} updated_at timestamp to {conversation_obj.updated_at}.")

        except Conversation.DoesNotExist:
            print(f"ERROR save_message: Conversation with ID {self.conversation_id} does not exist.")
        except Exception as e:
            print(f"ERROR save_message: Failed to save message. Error: {e}, User: {current_user.username if 'current_user' in locals() else 'Unknown'}")
