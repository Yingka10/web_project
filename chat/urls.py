from django.urls import path
from . import views

urlpatterns = [
    # 點擊聊天按鈕後開啟與賣家的對話，利用 seller_id 與 product_id 判斷
    path('with-seller/<int:seller_id>/<int:product_id>/', views.chat_with_seller, name='chat_with_seller'),
    # 聊天詳情頁面，帶 conversation_id
    path('chat/<int:conversation_id>/', views.chat_detail, name='chat_detail'),
    # 對話列表，顯示所有曾聊過天的對話記錄
    path('conversations/', views.conversation_list, name='conversation_list'),
]