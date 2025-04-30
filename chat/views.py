# chat/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from chat.models import Conversation, Message
from mywebsite.models import Post
from django.contrib.auth.models import User

@login_required
def chat_with_seller(request, seller_id, product_id):
    # 取得指定的賣家與商品
    seller = get_object_or_404(User, id=seller_id)
    product = get_object_or_404(Post, id=product_id)
    
    # 嘗試取得現有對話；若無則建立一筆
    conversation, created = Conversation.objects.get_or_create(
        buyer=request.user,
        seller=seller,
        product=product,
    )
    # 導向聊天詳情頁面
    return redirect('chat_detail', conversation_id=conversation.id)

@login_required
def chat_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # 確認只有對話雙方可以進入
    if request.user != conversation.buyer and request.user != conversation.seller:
        return redirect('home')  # 或返回 403
    
    messages = conversation.messages.all().order_by('timestamp')
    return render(request, 'chat/chat_detail.html', {
        'conversation': conversation,
        'messages': messages,
    })

@login_required
def conversation_list(request):
    # 列出該使用者參與的所有對話
    conversations = Conversation.objects.filter(buyer=request.user) | Conversation.objects.filter(seller=request.user)
    conversations = conversations.order_by('-created_at')
    return render(request, 'chat/conversation_list.html', {'conversations': conversations})