# chat/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from chat.models import Conversation, Message
from mywebsite.models import Post
from django.contrib.auth import get_user_model

@login_required
def chat_with_seller(request, seller_id, product_id):
    # 取得指定的賣家與商品
    User = get_user_model()
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
def chat_with_buyer(request, buyer_id, product_id):
    """
    讓賣家與特定買家進行聊天：
    - buyer_id: 買家的 ID（從 template 中傳遞）
    - product_id: 商品編號
    """
    User = get_user_model()
    buyer = get_object_or_404(User, id=buyer_id)
    product = get_object_or_404(Post, id=product_id)
    
    # 確認目前登入者是產品的賣家
    if request.user != product.owner:
        # 非賣家不能使用此功能，可依需求返回 403 或導向其他頁面
        return redirect('home')
    
    # 嘗試取得現有對話；若無則建立一筆 
    conversation, created = Conversation.objects.get_or_create(
        buyer=buyer,
        seller=request.user,
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

    if request.method == "POST":
        content = request.POST.get('message')
        if content:
            # 假設 Message 模型至少需要 conversation, sender, content 等欄位
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content,
            )
            # 送出訊息後使用 Post-Redirect-Get 模式，重新導向同一頁以防止重複提交
            return redirect('chat_detail', conversation_id=conversation.id)
    
    messages_qs = conversation.messages.all().order_by('timestamp')
    return render(request, 'chat/chat_detail.html', {
        'conversation': conversation,
        'messages': messages_qs,
    })

@login_required
def conversation_list(request):
    # 列出該使用者參與的所有對話
    conversations = Conversation.objects.filter(buyer=request.user) | Conversation.objects.filter(seller=request.user)
    conversations = conversations.order_by('-created_at')
    return render(request, 'chat/conversation_list.html', {'conversations': conversations})