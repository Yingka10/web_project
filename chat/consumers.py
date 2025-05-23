# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from chat.models import Message, Conversation
from channels.db import database_sync_to_async
from django.utils import timezone
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from mywebsite.models import Notification as SiteNotification
from mywebsite.models import CustomUser

# 全域字典：user_id -> 連線數
ONLINE_USERS = {}

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("DEBUG: Attempting to connect WebSocket...")
        conversation_id_str = self.scope['url_route']['kwargs'].get('conversation_id')
        print(f"DEBUG: conversation_id_str from URL: '{conversation_id_str}'")
        if not conversation_id_str:
            print("DEBUG: Closing connection - conversation_id_str is missing.")
            await self.close()
            return
        try:
            self.conversation_id = int(conversation_id_str)
            print(f"DEBUG: Parsed conversation_id: {self.conversation_id}")
        except ValueError:
            print(f"DEBUG: Closing connection - ValueError converting conversation_id_str: '{conversation_id_str}'")
            await self.close()
            return

        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            print(f"DEBUG: Closing connection - User '{self.scope['user']}' is not authenticated.")
            await self.close()
            return
        else:
            print(f"DEBUG: User '{self.scope['user']}' is authenticated.")

        # 追蹤用戶在線狀態
        uid = self.user.id
        ONLINE_USERS[uid] = ONLINE_USERS.get(uid, 0) + 1

        self.room_group_name = f"chat_{self.conversation_id}"
        print(f"DEBUG: room_group_name set to: '{self.room_group_name}'")
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        print(f"DEBUG: Added to group '{self.room_group_name}'.")
        await self.accept()
        print(f"WebSocket connected: user {self.scope['user'].username}, group {self.room_group_name}")

    async def disconnect(self, close_code):
        print(f"DEBUG: WebSocket disconnecting with code: {close_code}")
        # 移除用戶在線狀態
        if hasattr(self, "user") and self.user.is_authenticated:
            uid = self.user.id
            if uid in ONLINE_USERS:
                ONLINE_USERS[uid] -= 1
                if ONLINE_USERS[uid] <= 0:
                    del ONLINE_USERS[uid]
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            print(f"WebSocket disconnected: user {self.scope['user'].username}, group {self.room_group_name}")
        else:
            user_display = str(self.scope.get("user", "Unknown user"))
            if hasattr(self.scope.get("user"), "username"):
                user_display = self.scope["user"].username
            print(f"WebSocket disconnected (no room_group_name set): user {user_display}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data.get('message')
        if not message_content:
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
                'type': 'chat_message',
                'message': message_content,
                'sender_username': new_message_obj.sender.username,
                'timestamp': new_message_obj.timestamp.strftime('%H:%M'),
            }
        )
        print(f"DEBUG receive: Message sent to group {self.room_group_name}")

        # 判斷收件人是否在線，不在線才寄 email
        if recipient_user and recipient_user != self.user:
            recipient_id = recipient_user.id
            if recipient_id not in ONLINE_USERS and recipient_user.email:
                await send_new_message_email(
                    to_user=recipient_user,
                    from_user=self.user,
                    message=message_content,
                    conversation_id=self.conversation_id
                )
                print(f"DEBUG: Email notification sent to {recipient_user.email} (user offline)")
            await self.send_popup_notification_to_recipient(recipient_user, new_message_obj)

    async def chat_message(self, event):
        message_to_send = event['message']
        sender_username = event['sender_username']
        timestamp = event['timestamp']
        print(f"DEBUG chat_message: 消費者實例 (用戶 '{self.scope['user'].username}', 群組 '{self.room_group_name}') "
              f"正在處理來自發送者 '{sender_username}' 的訊息: '{message_to_send[:50]}...'")
        print(f"DEBUG chat_message: Sending message to WebSocket client: '{message_to_send[:50]}...' from sender: {sender_username}")
        await self.send(text_data=json.dumps({
            'message': message_to_send,
            'sender': sender_username,
            'timestamp': timestamp,
        }))
        print(f"DEBUG chat_message: 訊息已通過 WebSocket 由消費者實例 (用戶 '{self.scope['user'].username}') 發送")

    @database_sync_to_async
    def save_message_and_get_recipient(self, message_content_param):
        try:
            current_user = self.user
            print(f"DEBUG save_message: Attempting to save message for conversation_id: {self.conversation_id}, user: {current_user.username}")
            conversation_obj = Conversation.objects.get(pk=self.conversation_id)
            new_msg = Message.objects.create(
                conversation=conversation_obj,
                sender=current_user,
                content=message_content_param,
            )
            print(f"DEBUG save_message: Message saved with ID: {new_msg.id}, content: '{new_msg.content[:30]}...'")
            conversation_obj.updated_at = timezone.now()
            conversation_obj.save(update_fields=['updated_at'])
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

    @database_sync_to_async
    def get_chat_url(self, conversation_id):
        try:
            return reverse('chat:chat_detail', kwargs={'conversation_id': conversation_id})
        except Exception as e:
            print(f"ERROR: ChatConsumer: Error reversing chat_detail URL: {e}")
            return "#"

    async def send_popup_notification_to_recipient(self, recipient, chat_message_obj):
        sender_name = chat_message_obj.sender.username
        message_preview = chat_message_obj.content[:50]
        conversation_id = chat_message_obj.conversation.id
        chat_link = await self.get_chat_url(conversation_id)
        popup_title = f"來自 {sender_name} 的新訊息"
        popup_body = f"{message_preview}{'...' if len(chat_message_obj.content) > 50 else ''}"
        recipient_notification_group = f"notifications_user_{recipient.id}"
        await self.channel_layer.group_send(
            recipient_notification_group,
            {
                'type': 'display_chat_popup',
                'popup_title': popup_title,
                'popup_body': popup_body,
                'popup_link': chat_link,
                'conversation_id': str(conversation_id),
                'sender_username': sender_name,
            }
        )
        print(f"DEBUG: ChatConsumer: Popup event sent to group {recipient_notification_group} for user {recipient.username}")

@database_sync_to_async
def send_new_message_email(to_user, from_user, message, conversation_id):
    subject = f"你收到來自 {from_user.username} 的新私訊"
    message_body = (
        f"Hi {to_user.username},\n\n"
        f"你收到來自 {from_user.username} 的新訊息：\n\n"
        f"{message[:50]}...\n\n"
        f"請登入網站查看完整訊息。\n"
        f"聊天室連結: https://webproject-ncu.up.railway.app//chat/{conversation_id}/"
    )
    send_mail(
        subject,
        message_body,
        settings.DEFAULT_FROM_EMAIL,
        [to_user.email],
        fail_silently=False,
    )

# --- NotificationConsumer ---

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

        # (可選) 連接時發送一次未讀鈴鐺通知計數
        unread_count = await self.get_initial_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count_update',
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

    async def send_notification_update(self, event):
        print(f"DEBUG: NotificationConsumer: User {self.user.username} received 'send_notification_update' event: {event}")
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification_text': event.get('notification_text'),
            'notification_link': event.get('notification_link'),
            'unread_count': event.get('unread_count'),
            'sender_username': event.get('sender_username'),
            'conversation_id': event.get('conversation_id')
        }))

    async def display_chat_popup(self, event):
        print(f"DEBUG: NotificationConsumer: User {self.user.username} received 'display_chat_popup' event: {event}")
        popup_title = event.get('popup_title')
        popup_body = event.get('popup_body')
        popup_link = event.get('popup_link')
        conversation_id = event.get('conversation_id')
        sender_username = event.get('sender_username')
        await self.send(text_data=json.dumps({
            'type': 'show_chat_popup_notification',
            'title': popup_title,
            'body': popup_body,
            'link': popup_link,
            'conversation_id': conversation_id,
            'sender': sender_username,
        }))
        print(f"DEBUG: NotificationConsumer: Sent 'show_chat_popup_notification' data to user {self.user.username} via WebSocket.")

    @database_sync_to_async
    def get_initial_unread_count(self):
        if self.user and self.user.is_authenticated:
            return SiteNotification.objects.filter(user=self.user, is_read=False).count()
        return 0
