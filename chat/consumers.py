# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from chat.models import Message, Conversation
from channels.db import database_sync_to_async
from django.utils import timezone 
from django.urls import reverse # 確保導入
from mywebsite.models import Notification as SiteNotification # 如果您還想用之前的 Notification 模型記錄
from mywebsite.models import CustomUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("DEBUG: Attempting to connect WebSocket...") # 新增
        conversation_id_str = self.scope['url_route']['kwargs'].get('conversation_id')
        print(f"DEBUG: conversation_id_str from URL: '{conversation_id_str}'") # 新增

        if not conversation_id_str:
            print("DEBUG: Closing connection - conversation_id_str is missing.") # 新增
            await self.close()
            return

        try:
            self.conversation_id = int(conversation_id_str)
            print(f"DEBUG: Parsed conversation_id: {self.conversation_id}") # 新增
        except ValueError:
            print(f"DEBUG: Closing connection - ValueError converting conversation_id_str: '{conversation_id_str}'") # 新增
            await self.close()
            return
        
        self.user = self.scope["user"]
        # 檢查使用者是否已通過身份驗證
        if not self.scope["user"].is_authenticated:
            print(f"DEBUG: Closing connection - User '{self.scope['user']}' is not authenticated.") # 新增
            await self.close()
            return
        else: # 新增
            print(f"DEBUG: User '{self.scope['user']}' is authenticated.") # 新增


        self.room_group_name = f"chat_{self.conversation_id}"
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

        new_message_obj, recipient_user = await self.save_message_and_get_recipient(message_content)

        if not new_message_obj:
            print("DEBUG: ChatConsumer: Message saving failed or no recipient, not proceeding with broadcast.")
            return
        
        # 廣播訊息到聊天室群組
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',  # 將調用下面的 chat_message 方法
                'message': message_content,
                'sender_username': new_message_obj.sender.username, 
                'timestamp': new_message_obj.timestamp.strftime('%H:%M'),
            }
        )
        print(f"DEBUG receive: Message sent to group {self.room_group_name}")

        if recipient_user and recipient_user != self.user:
            await self.send_popup_notification_to_recipient(recipient_user, new_message_obj)

    # 接收群組訊息，並發送回 WebSocket
    async def chat_message(self, event):
        message_to_send = event['message']
        sender_username = event['sender_username'] 
        timestamp = event['timestamp'] 

        
        # 非常重要的日誌：記錄是哪個用戶的 Consumer 實例在處理哪個事件
        print(f"DEBUG chat_message: 消費者實例 (用戶 '{self.scope['user'].username}', 群組 '{self.room_group_name}') "
          f"正在處理來自發送者 '{sender_username}' 的訊息: '{message_to_send[:50]}...'")
    
        print(f"DEBUG chat_message: Sending message to WebSocket client: '{message_to_send[:50]}...' from sender: {sender_username}")

        await self.send(text_data=json.dumps({
            'message': message_to_send,
            'sender': sender_username,
            'timestamp': timestamp,
        }))
        print(f"DEBUG chat_message: 訊息已通過 WebSocket 由消費者實例 (用戶 '{self.scope['user'].username}') 發送")

    # 藉由同步函式保存訊息
    @database_sync_to_async
    def save_message_and_get_recipient(self, message_content_param):
        try:
            current_user = self.user
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

            recipient = None
            if conversation_obj.user1 == current_user:
                recipient = conversation_obj.user2
            elif conversation_obj.user2 == current_user:
                recipient = conversation_obj.user1
            
            if recipient:
                 print(f"DEBUG: ChatConsumer: Determined recipient: {recipient.username}")
            else:
                print(f"WARNING: ChatConsumer: Could not determine recipient for conversation {conversation_obj.id}")


            return new_msg, recipient 
            
        except Conversation.DoesNotExist:
            print(f"ERROR: ChatConsumer: Conversation with ID {self.conversation_id} does not exist.")
            return None, None
        except Exception as e:
            print(f"ERROR: ChatConsumer: Failed to save message. Error: {e}, User: {current_user.username if hasattr(self, 'user') else 'Unknown'}")
            return None, None
        
        # --- 新增：獲取聊天室 URL 的輔助方法 ---
    @database_sync_to_async
    def get_chat_url(self, conversation_id):
        try:
            # 假設您的 chat app 的 app_name 是 'chat'，並且 URL name 是 'chat_detail'
            return reverse('chat:chat_detail', kwargs={'conversation_id': conversation_id})
        except Exception as e:
            print(f"ERROR: ChatConsumer: Error reversing chat_detail URL: {e}")
            return "#" # Fallback URL
    # --- 新增結束 ---

    # --- 新增：發送彈出通知到 NotificationConsumer 的邏輯 ---
    async def send_popup_notification_to_recipient(self, recipient, chat_message_obj):
        sender_name = chat_message_obj.sender.username
        message_preview = chat_message_obj.content[:50]
        conversation_id = chat_message_obj.conversation.id
        chat_link = await self.get_chat_url(conversation_id) # 使用輔助方法

        popup_title = f"來自 {sender_name} 的新訊息"
        popup_body = f"{message_preview}{'...' if len(chat_message_obj.content) > 50 else ''}"
        recipient_notification_group = f"notifications_user_{recipient.id}" # 確保與 NotificationConsumer 的組名一致

        await self.channel_layer.group_send(
            recipient_notification_group,
            {
                'type': 'display_chat_popup', # NotificationConsumer 將處理這個類型
                'popup_title': popup_title,
                'popup_body': popup_body,
                'popup_link': chat_link,
                'conversation_id': str(conversation_id),
                'sender_username': sender_name,
            }
        )
        print(f"DEBUG: ChatConsumer: Popup event sent to group {recipient_notification_group} for user {recipient.username}")
  
# --- 新增/修改 NotificationConsumer ---
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            print("DEBUG: NotificationConsumer: Closing connection - User not authenticated.")
            await self.close()
            return

        self.user_notification_group = f"notifications_user_{self.user.id}"
        print(f"DEBUG: NotificationConsumer: User '{self.user.username}' connecting to group '{self.user_notification_group}'")

        await self.channel_layer.group_add(
            self.user_notification_group,
            self.channel_name
        )
        await self.accept()
        print(f"DEBUG: NotificationConsumer: WebSocket connected for user {self.user.username}, group {self.user_notification_group}")

        #(可選) 連接時發送一次未讀鈴鐺通知計數
        unread_count = await self.get_initial_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count_update', # 與前端 JS 處理鈴鐺的類型一致
            'unread_count': unread_count
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'user_notification_group'):
            print(f"DEBUG: NotificationConsumer: User '{self.user.username}' disconnecting from group '{self.user_notification_group}'")
            await self.channel_layer.group_discard(
                self.user_notification_group,
                self.channel_name
            )
        else:
            print(f"DEBUG: NotificationConsumer: User '{self.user.username if hasattr(self, 'user') and self.user.is_authenticated else 'Unauthenticated user'}' disconnected without a group.")


    # (可選) 如果您還需要處理鈴鐺通知的更新
    async def send_notification_update(self, event):
        print(f"DEBUG: NotificationConsumer: User {self.user.username} received 'send_notification_update' event: {event}")
        await self.send(text_data=json.dumps({
            'type': 'new_notification', # 與前端 JS 處理鈴鐺旁的瀏覽器通知類型一致
            'notification_text': event.get('notification_text'),
            'notification_link': event.get('notification_link'),
            'unread_count': event.get('unread_count'),
            'sender_username': event.get('sender_username'),
            'conversation_id': event.get('conversation_id') # 傳遞 conversation_id 給鈴鐺通知
        }))

    # --- 新增：處理來自 ChatConsumer 的 display_chat_popup 事件 ---
    async def display_chat_popup(self, event):
        print(f"DEBUG: NotificationConsumer: User {self.user.username} received 'display_chat_popup' event: {event}")

        popup_title = event.get('popup_title')
        popup_body = event.get('popup_body')
        popup_link = event.get('popup_link')
        conversation_id = event.get('conversation_id')
        sender_username = event.get('sender_username')

        await self.send(text_data=json.dumps({
            'type': 'show_chat_popup_notification', # 前端 JS 將監聽這個 type
            'title': popup_title,
            'body': popup_body,
            'link': popup_link,
            'conversation_id': conversation_id,
            'sender': sender_username, # 與前端 JS 期望的 key 'sender' 保持一致
        }))
        print(f"DEBUG: NotificationConsumer: Sent 'show_chat_popup_notification' data to user {self.user.username} via WebSocket.")

    # (可選) 獲取初始未讀計數的方法
    @database_sync_to_async
    def get_initial_unread_count(self):
        if self.user and self.user.is_authenticated:
            return SiteNotification.objects.filter(user=self.user, is_read=False).count()
        return 0
