# chat/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from chat.models import Conversation, Message
from django.db.models import Q, OuterRef, Subquery, Max, Value, CharField
from django.db.models.functions import Coalesce # 用於處理可能為 None 的情況
#from mywebsite.models import Post
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

import logging # 引入 logging 模組
logger = logging.getLogger(__name__)# 獲取一個 logger 實例
User = get_user_model()

@login_required
def chat_with_seller(request, seller_id, product_id):
    other_user = get_object_or_404(User, id=seller_id)
    if request.user == other_user:
        messages.error(request, "您不能與自己開始聊天。")
        return redirect('index')

    # 確保 user1 和 user2 的順序
    user1_obj, user2_obj = sorted([request.user, other_user], key=lambda user: user.id)

    # 嘗試取得或建立對話
    conversation, created = Conversation.objects.get_or_create(
        user1=user1_obj,
        user2=user2_obj
    )

    return redirect('chat:chat_detail', conversation_id=conversation.id)

@login_required
def chat_with_buyer(request, buyer_id, product_id):

    print(f"--- 進入 chat_with_buyer: buyer_id={buyer_id} ---")
    current_user = request.user # 假設當前用戶是賣家 (或有權限與買家聊天的用戶)
    try:
        other_user = get_object_or_404(User, id=buyer_id) # 買家
        print(f"--- chat_with_buyer: 找到對方用戶 (買家): {other_user} ---")
    except User.DoesNotExist:
        print(f"--- chat_with_buyer: 找不到 ID 為 {buyer_id} 的用戶 ---")
        messages.error(request, "指定的用戶不存在。")
        return redirect('index')
    except Exception as e:
        print(f"--- chat_with_buyer: 一般錯誤: {e} ---")
        messages.error(request, "發生未知錯誤，請稍後再試。")
        return redirect('index')


    if current_user == other_user:
        messages.error(request, "您不能與自己開始聊天。")
        return redirect('index')

    user1_obj, user2_obj = (current_user, other_user) if current_user.id < other_user.id else (other_user, current_user)

    print(f"--- chat_with_buyer: 嘗試取得或建立對話，用戶1={user1_obj.id}, 用戶2={user2_obj.id} ---")
    try:
        conversation, created = Conversation.objects.get_or_create(
            user1=user1_obj,
            user2=user2_obj
            # 移除了 product
        )
        if created:
            conversation.updated_at = timezone.now()
            conversation.save(update_fields=['updated_at'])
        print(f"--- chat_with_buyer: 對話 {'已建立' if created else '已找到'}: ID={conversation.id} ---")
    except Exception as e:
        print(f"--- chat_with_buyer: 取得或建立對話時發生錯誤: {e} ---")
        messages.error(request, "建立或取得對話失敗。")
        return redirect('index')

    print(f"--- chat_with_buyer: 嘗試重定向至 'chat:chat_detail'，對話 ID: {conversation.id} ---")
    try:
        response = redirect('chat:chat_detail', conversation_id=conversation.id)
        print(f"--- chat_with_buyer: 重定向回應已建立。 ---")
        return response
    except Exception as e:
        print(f"--- chat_with_buyer: 重定向至 'chat:chat_detail' 時發生錯誤: {e} ---")
        messages.error(request, "無法開啟聊天室。")
        return redirect('index')

@login_required
@login_required
def chat_detail(request, conversation_id):
    current_user = request.user
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if current_user not in [conversation.user1, conversation.user2]:
        messages.error(request, "您無權存取此對話。")
        return redirect('index')
    other_user = conversation.user2 if conversation.user1 == current_user else conversation.user1

    # 標記對方訊息為已讀
    Message.objects.filter(
        conversation=conversation,
        sender=other_user,
        is_read=False
    ).update(is_read=True)

    if request.method == "POST":
        content = request.POST.get('message')
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=current_user,
                content=content,
            )
            conversation.updated_at = timezone.now()
            conversation.save(update_fields=['updated_at'])
            return redirect('chat:chat_detail', conversation_id=conversation.id)
        else:
            messages.warning(request, "訊息內容不能為空。")

    messages_qs = conversation.messages.all().order_by('timestamp')
    context = {
        'conversation': conversation,
        'messages_list': messages_qs,
        'other_user': other_user,
    }
    return render(request, 'chat.html', context)



@login_required
def send_message_ajax(request, conversation_id): # AJAX 視圖範例
    if request.method == 'POST':
        try:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        except Conversation.DoesNotExist:
             return JsonResponse({'status': 'error', 'message': '找不到對話'}, status=404)

        current_user = request.user

        if current_user != conversation.user1 and current_user != conversation.user2:
            return JsonResponse({'status': 'error', 'message': '未授權'}, status=403)

        content = request.POST.get('content')
        if content:
            message = Message.objects.create(
                conversation=conversation,
                sender=current_user,
                content=content
            )
            conversation.updated_at = timezone.now()
            conversation.save(update_fields=['updated_at'])

            # 觸發通知的邏輯 (如果需要)
            # from mywebsite.models import Notification # 假設 Notification 模型存在
            # recipient = conversation.user1 if current_user == conversation.user2 else conversation.user2
            # try:
            #     Notification.objects.create(
            #         recipient=recipient,
            #         message_text=f"{current_user.username} 給您發了一條新訊息: \"{content[:30]}...\"",
            #         link=reverse('chat:chat_detail', kwargs={'conversation_id': conversation.id})
            #     )
            # except Exception as e:
            #     print(f"創建通知時發生錯誤: {e}")


            return JsonResponse({
                'status': 'success',
                'message_content': message.content,
                'sender_username': message.sender.username,
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        return JsonResponse({'status': 'error', 'message': '訊息內容為必填'}, status=400)
    return JsonResponse({'status': 'error', 'message': '無效的請求方法'}, status=405)
