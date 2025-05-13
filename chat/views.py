# chat/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from chat.models import Conversation, Message
#from mywebsite.models import Post
from django.contrib.auth import get_user_model
import logging # 引入 logging 模組

# 獲取一個 logger 實例
logger = logging.getLogger(__name__)

@login_required
def chat_with_seller(request, seller_id, product_id):
    # # 取得指定的賣家與商品
    # User = get_user_model()
    # other_user = get_object_or_404(User, id=seller_id)
    
    # # 嘗試取得現有對話；若無則建立一筆
    # user1, user2 = sorted([request.user, other_user], key=lambda user: user.id)
    # conversation, created = Conversation.objects.get_or_create(
    #     user1=user1,
    #     user2=user2
    # )
    # # 導向聊天詳情頁面
    # return redirect('chat_detail', conversation_id=conversation.id)
    print(f"--- Entering chat_with_seller: seller_id={seller_id}, product_id={product_id} ---") # 新增
    User = get_user_model()
    try:
        other_user = get_object_or_404(User, id=seller_id)
        print(f"--- chat_with_seller: Found other_user (seller): {other_user} ---") # 新增
    except Exception as e:
        print(f"--- chat_with_seller: Error finding other_user with id {seller_id}: {e} ---") # 新增
        return redirect('home')

    # product = get_object_or_404(Post, id=product_id)
    # print(f"--- chat_with_seller: Product (if used): {product_id} ---") # 如果將來使用 product_id

    user1, user2 = sorted([request.user, other_user], key=lambda user: user.id)
    print(f"--- chat_with_seller: Trying to get_or_create Conversation for user1={user1.id}, user2={user2.id} ---") # 新增
    try:
        conversation, created = Conversation.objects.get_or_create(
            user1=user1,
            user2=user2
            # post=product,
        )
        print(f"--- chat_with_seller: Conversation {'created' if created else 'found'}: ID={conversation.id} ---") # 新增
    except Exception as e:
        print(f"--- chat_with_seller: Error get_or_create Conversation: {e} ---") # 新增
        return redirect('home')

    print(f"--- chat_with_seller: Attempting to redirect to 'chat_detail' with conversation_id: {conversation.id} ---") # 新增
    try:
        response = redirect('chat_detail', conversation_id=conversation.id)
        print(f"--- chat_with_seller: Redirect response created. Status code should be 302. ---") # 新增
        return response
    except Exception as e:
        print(f"--- chat_with_seller: Error during redirect to 'chat_detail': {e} ---") # 新增
        return redirect('home')

@login_required
def chat_with_buyer(request, buyer_id, product_id):
    # """
    # 賣家對特定買家發起對話：
    # - buyer_id 為買家 ID
    # - product_id 為商品編號
    # 只有該商品賣家才有權限發起此對話。
    # """
    # User = get_user_model()
    # other_user = get_object_or_404(User, id=buyer_id)
    
    # # 排序兩位使用者，確保順序一致
    # user1, user2 = sorted([request.user, other_user], key=lambda user: user.id)
    # conversation, created = Conversation.objects.get_or_create(
    #     user1=user1,
    #     user2=user2
    # )
    # # 導向聊天詳情頁面
    # return redirect('chat_detail', conversation_id=conversation.id)
    print(f"--- Entering chat_with_buyer: buyer_id={buyer_id}, product_id={product_id} ---")
    User = get_user_model()
    try:
        other_user = get_object_or_404(User, id=buyer_id)
        print(f"--- chat_with_buyer: Found other_user: {other_user} ---")
    except Exception as e:
        print(f"--- chat_with_buyer: Error finding other_user with id {buyer_id}: {e} ---")
        return redirect('home') # 或者其他錯誤處理

    # product = get_object_or_404(Post, id=product_id) # 假設 Post 模型相關邏輯暫時不需要

    user1, user2 = sorted([request.user, other_user], key=lambda user: user.id)
    print(f"--- chat_with_buyer: Trying to get_or_create Conversation for user1={user1.id}, user2={user2.id} ---")
    try:
        conversation, created = Conversation.objects.get_or_create(
            user1=user1,
            user2=user2
            # post=product, # 如果 post 欄位在 Conversation 模型中是必須的，需要取消註解並確保 product 有效
        )
        print(f"--- chat_with_buyer: Conversation {'created' if created else 'found'}: ID={conversation.id} ---")
    except Exception as e:
        print(f"--- chat_with_buyer: Error get_or_create Conversation: {e} ---")
        # 考慮錯誤處理，例如重定向到錯誤頁面或首頁
        return redirect('home') 

    print(f"--- chat_with_buyer: Attempting to redirect to 'chat_detail' with conversation_id: {conversation.id} ---")
    try:
        response = redirect('chat_detail', conversation_id=conversation.id)
        print(f"--- chat_with_buyer: Redirect response created. Status code should be 302. ---")
        return response
    except Exception as e: # 例如 NoReverseMatch
        print(f"--- chat_with_buyer: Error during redirect to 'chat_detail': {e} ---")
        # 這裡也需要錯誤處理
        return redirect('home')

@login_required
def chat_detail(request, conversation_id):
    # conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # # 檢查只有對話成員可以查看聊天室
    # if request.user not in [conversation.user1, conversation.user2]:
    #     return redirect('home')

    # if request.method == "POST":
    #     content = request.POST.get('message')
    #     if content:
    #         # 假設 Message 模型至少需要 conversation, sender, content 等欄位
    #         Message.objects.create(
    #             conversation=conversation,
    #             # sender=request.user.username,
    #             sender=request.user,
    #             content=content,
    #         )
    #         # 送出訊息後使用 Post-Redirect-Get 模式，重新導向同一頁以防止重複提交
    #         return redirect('chat_detail', conversation_id=conversation.id)
    
    # messages_qs = conversation.messages.all().order_by('timestamp')
    # return render(request, 'chat.html', {
    #     'conversation': conversation,
    #     'messages': messages_qs,
    # })

    print(f"--- Entering chat_detail view with conversation_id (from URL): {conversation_id} ---") # 新增日誌

    try:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        print(f"--- Successfully fetched conversation object: {conversation} (ID: {conversation.id}) ---") # 新增日誌
    except Exception as e:
        print(f"--- Error fetching conversation with ID {conversation_id}: {e} ---") # 新增日誌
        # 根據您的應用邏輯，這裡可能需要返回一個錯誤頁面或重定向
        return redirect('home') # 或其他適當的錯誤處理

    # 檢查只有對話成員可以查看聊天室
    if request.user not in [conversation.user1, conversation.user2]:
        print(f"--- User {request.user} is not part of conversation {conversation.id}. Redirecting. ---") # 新增日誌
        return redirect('home')

    if request.method == "POST":
        content = request.POST.get('message')
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content,
            )
            print(f"--- POST request: Message saved for conversation {conversation.id}. Redirecting. ---") # 新增日誌
            return redirect('chat_detail', conversation_id=conversation.id)
    
    messages_qs = conversation.messages.all().order_by('timestamp')

    # --- 添加更詳細的 context 除錯日誌 ---
    context_to_pass = {
        'conversation': conversation,
        'messages': messages_qs,
    }
    print(f"--- Context being passed to template for conversation ID {conversation.id}: ---")
    print(f"Conversation object in context: {context_to_pass.get('conversation')}")
    if context_to_pass.get('conversation'):
        print(f"Conversation ID in context: {context_to_pass.get('conversation').id}")
        print(f"Conversation user1 in context: {context_to_pass.get('conversation').user1}")
        print(f"Conversation user2 in context: {context_to_pass.get('conversation').user2}")
    print(f"Request user in context (available via 'request'): {request.user}")
    # --- 結束除錯日誌 ---

    return render(request, 'chat.html', context_to_pass)

@login_required
def conversation_list(request):
    # 找出目前使用者參與的所有對話（無論存在哪個欄位中）
    from django.db.models import Q
    conversations = Conversation.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).order_by('-created_at')
    return render(request, 'conversation_list.html', {'conversations': conversations})