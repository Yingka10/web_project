from django.urls import re_path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    # 房間名稱格式為 chat_seller_<id> 或 chat_buyer_<id>
    re_path(r'ws/chat/(?P<room_name>\w+)/$', ChatConsumer.as_asgi()),
]