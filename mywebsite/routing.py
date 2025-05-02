from django.urls import re_path
from ..chat import consumers

websocket_urlpatterns = [
    # 這裡我們使用 room_name 來代表每組聊天室，例如 "5_72" 表示 Seller ID 與 Product ID 組合
    re_path(r'^ws/chat/(?P<room_name>[\w-]+)/$', consumers.ChatConsumer.as_asgi()),
]