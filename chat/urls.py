from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # 點擊聊天按鈕後開啟與賣家的對話，利用 seller_id 與 product_id 判斷
    path('with-seller/<int:seller_id>/<int:product_id>/', views.chat_with_seller, name='chat_with_seller'),
    # 新增：點擊聊天按鈕後開啟與買家的對話，利用 buyer_id 與 product_id 判斷
    path('with-buyer/<int:buyer_id>/<int:product_id>/', views.chat_with_buyer, name='chat_with_buyer'),
    # 聊天詳情頁面，帶 conversation_id
    path('<int:conversation_id>/', views.chat_detail, name='chat_detail'),
]