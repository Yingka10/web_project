#chat/routing.py
from django.urls import re_path
#from .consumers import ChatConsumer
from chat import consumers

websocket_urlpatterns = [
     re_path(r'ws/chat/(?P<conversation_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
     re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]