from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone # 引入 timezone
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from mywebsite.models import Post, Category, Reservation , ProductImage, Rating, Notification, CustomUser
from django.contrib import messages 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import  AuthenticationForm
from django.contrib.auth import login as auth_login, authenticate
from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import cloudinary
from django.conf import settings
from django.contrib.auth.models import User
from .form import CustomUserCreationForm
from .models import ChatMessage 
from django.db.models import Q, OuterRef, Subquery, Value, CharField, IntegerField, DateTimeField, F
from django.db.models.functions import Coalesce
from .models import Post, Rating 
from chat.models import Conversation as ChatConversation, Message as ChatMessage
from django.db.models import Avg

@login_required
def chat(request, role, chat_with_id, product_id):
    chat_with = get_object_or_404(User, id=chat_with_id)
    
    # 根據角色決定對話中賣家的 id
    if role == 'seller':
        # 當前使用者為賣家，對話對象為買家，但訊息記錄只以 seller_id 標識
        actual_seller_id = request.user.id
    elif role == 'buyer':
        # 當前使用者為買家，對話對象為賣家
        actual_seller_id = chat_with.id
    else:
        #messages.error(request, "不合法的聊天室參數。")
        return redirect('homepage')
    
    if request.method == "POST":
        message_content = request.POST.get("message")
        if message_content:
            ChatMessage.objects.create(
                sender=request.user.username if request.user.is_authenticated else "Guest",
                content=message_content,
                product_id=product_id,
                seller_id=actual_seller_id,
            )
        # 重導回相同聊天室，同時傳回 role 參數
        return redirect('chat', role=role, chat_with_id=chat_with_id, product_id=product_id)
    
    # 使用 product_id 與 seller_id 來過濾聊天記錄
    messages_qs = ChatMessage.objects.filter(
        product_id=product_id,
        seller_id=actual_seller_id
    ).order_by('id')

    context = {
        'user_role': role,
        'chat_with': chat_with,
        'seller_id': actual_seller_id,
        'product_id': product_id,
        'messages': messages_qs,
    }
    return render(request, 'chat.html', context)

cloudinary.config(
    cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
    api_secret=settings.CLOUDINARY_STORAGE['API_SECRET']
)

def homepage(request):
    categories = Category.objects.all()
    sort = request.GET.get('sort')  # 取得排序參數

    # 先定義一個基礎的查詢集
    base_products_query = Post.objects.filter(is_sold=False).prefetch_related('images')

    if sort == 'price_asc':
        products_query = base_products_query.order_by('price')
    elif sort == 'price_desc':
        products_query = base_products_query.order_by('-price')
    elif sort == 'date_desc':
        products_query = base_products_query.order_by('-pub_date')
    elif sort == 'date_asc':
        products_query = base_products_query.order_by('pub_date')   # 由舊到新
    # 如果沒有 sort 參數，則 products_query 保持其初始狀態 (可能按模型 Meta.ordering 排序)
    else:
        # 如果 sort 參數不存在或不是預期的值，則 products_query 等於基礎查詢集
        products_query = base_products_query
        
    # 將查詢集轉換為列表，以便我們可以為每個商品對象添加自定義屬性
    # 這一步會執行數據庫查詢
    product_list_for_template = list(products_query)

    if request.user.is_authenticated:
        # 獲取當前用戶收藏的所有商品的 ID 集合，方便快速查找
        favorite_post_ids = set(request.user.favorite_posts.values_list('id', flat=True))
        
        for product_item in product_list_for_template:
            # 為每個商品對象添加一個名為 is_favorited_by_user 的屬性
            product_item.is_favorited_by_user = product_item.id in favorite_post_ids
    else:
        # 如果用戶未登入，所有商品都標記為未收藏
        for product_item in product_list_for_template:
            product_item.is_favorited_by_user = False

    # 加這一段（計算未讀通知數量 + 撈通知）
    unread_count = 0
    notifications = []
    if request.user.is_authenticated:
        unread_count = request.user.notifications.filter(is_read=False).count()
        notifications = request.user.notifications.all()[:5]  # 只撈最新5筆通知
        
    return render(request, "index.html", {
        'products': product_list_for_template,
        'categories': categories,
        'sort': sort,  # 把目前的排序傳給模板，方便下拉選單顯示狀態
        'unread_count': unread_count,  # 加進 context
        'notifications': notifications,
    })


@login_required
def toggle_favorite(request, id):
    product = get_object_or_404(Post, id=id)
    user = request.user
    # 如果目前使用者已收藏此商品，就移除；否則加入收藏
    if product in user.favorite_posts.all():
        user.favorite_posts.remove(product)
        #messages.success(request, f"已將「{product.title}」從收藏移除。")
    else:
        user.favorite_posts.add(product)
        #messages.success(request, f"已將「{product.title}」加入收藏！")
    # 重導回前一個頁面
    return redirect(request.META.get('HTTP_REFERER', 'index'))

@login_required
def profile(request): # 您的 profile 視圖
    current_user = request.user

    # --- 您現有的獲取其他個人頁面數據的邏輯 ---
    favorites = current_user.favorite_posts.prefetch_related('images').all()
    user_reservations = current_user.reservations.select_related('product').prefetch_related('product__images').order_by('-reserved_at')
    all_my_posts = current_user.posts.prefetch_related('images').all()
    active_posts = all_my_posts.filter(is_sold=False)
    sold_posts = all_my_posts.filter(is_sold=True)
    purchased_posts = Post.objects.filter(buyer=current_user, is_sold=True).prefetch_related('images')

    for post in sold_posts:
        if post.buyer:
            post.can_rate_buyer = not Rating.objects.filter(rater=current_user, rated=post.buyer, post=post).exists()

    for post in purchased_posts:
        post.can_rate_seller = not Rating.objects.filter(rater=current_user, rated=post.owner, post=post).exists()
    # --- 現有邏輯結束 ---

    # --- 獲取用戶的對話列表 (基於方案2，直接在 profile 視圖中) ---
    # 子查詢，用於獲取每個對話的最後一條訊息的內容
    last_message_content_subquery = ChatMessage.objects.filter(
        conversation=OuterRef('pk')
    ).order_by('-timestamp').values('content')[:1]

    # 子查詢，用於獲取每個對話的最後一條訊息的時間戳
    last_message_timestamp_subquery = ChatMessage.objects.filter(
        conversation=OuterRef('pk')
    ).order_by('-timestamp').values('timestamp')[:1]
    
    # 子查詢，用於獲取每個對話的最後一條訊息的發送者 ID
    last_message_sender_id_subquery = ChatMessage.objects.filter(
        conversation=OuterRef('pk')
    ).order_by('-timestamp').values('sender_id')[:1]

    user_conversations_qs = ChatConversation.objects.filter(
        Q(user1=current_user) | Q(user2=current_user)
    ).annotate(
        # 使用 Coalesce 提供一個預設值，以防某些對話沒有任何訊息
        annotated_last_message_content=Coalesce(
            Subquery(last_message_content_subquery, output_field=CharField(null=True)),
            Value(''), # 如果子查詢結果為 None，則預設為空字串
            output_field=CharField() # Coalesce 本身的 output_field
        ),
        annotated_last_message_timestamp=Coalesce(
            Subquery(last_message_timestamp_subquery, output_field=DateTimeField(null=True)),
            F('created_at'), # *** 修正點：使用 F() 引用外部查詢的欄位 ***
            output_field=DateTimeField() # *** 為 Coalesce 明確指定 output_field ***
        ),
        annotated_last_message_sender_id=Subquery(
            last_message_sender_id_subquery,
            output_field=IntegerField(null=True)
        )
    ).order_by('-annotated_last_message_timestamp')

    # 處理對方用戶和組裝最終數據
    conversations_for_profile_tab = []
    
    user_ratings = Rating.objects.filter(rated=current_user).select_related('rater')
    average_rating = user_ratings.aggregate(Avg('score'))['score__avg'] or 0
    received_ratings = current_user.received_ratings.select_related('rater').order_by('-created_at')

    for conv_obj in user_conversations_qs: # conv_obj 是 Conversation 物件，帶有 annotate 的欄位
        other_user_in_conv = conv_obj.user2 if conv_obj.user1 == current_user else conv_obj.user1
        is_last_msg_from_current_user = (conv_obj.annotated_last_message_sender_id == current_user.id)
        
        # 判斷是否有實際的訊息
        has_actual_message = conv_obj.annotated_last_message_sender_id is not None

        unread_message_count = ChatMessage.objects.filter(
            conversation=conv_obj,      # 屬於當前這個對話
            sender=other_user_in_conv,  # 訊息是由對方發送的
            is_read=False               # 且訊息是未讀的
        ).count()

        conversations_for_profile_tab.append({
            'conversation_id': conv_obj.id, # 直接傳遞 ID
            'other_user_username': other_user_in_conv.username, # 直接傳遞用戶名
            'other_user_id': other_user_in_conv.id, # 如果需要對方用戶ID
            'last_message_content': conv_obj.annotated_last_message_content,
            'last_message_timestamp': conv_obj.annotated_last_message_timestamp,
            'is_last_message_from_current_user': is_last_msg_from_current_user,
            'has_actual_message': has_actual_message,
            'conversation_created_at': conv_obj.created_at, # 用於沒有訊息時的排序或顯示
            'unread_count': unread_message_count,
            
        })
    # --- 獲取對話列表結束 ---

    context = {
        'favorites': favorites,
        'user_reservations': user_reservations,
        'active_posts': active_posts,
        'sold_posts': sold_posts,
        'purchased_posts': purchased_posts,
        'conversations_for_profile_tab': conversations_for_profile_tab, # 將對話列表數據傳遞給模板
        'user_ratings': user_ratings,
        'average_rating': round(average_rating, 1),
        'received_ratings': received_ratings,
        # 'user': current_user, # request.user 在模板中默認可用
    }
    return render(request, "profile.html", context)

@csrf_exempt
def api(request):
    if request.method == 'GET':
        keyword = request.GET.get('keyword')
        limit = request.GET.get('limit') 
        
        # Check the values before using them
        if keyword and limit:
            print(keyword + ' ' + limit)

        # Retrieve the latest posts from the database
        posts = Post.objects.all()
        post_list = []

        for post in posts:
            post_list.append({
                'title': post.title,
                'body': post.body,
                'pub_date': post.pub_date.strftime('%Y-%m-%d %H:%M:%S')
            })
        # Return the list of posts as JSON
        return JsonResponse({'posts': post_list})

    elif request.method == 'POST':
        try:
            if not request.body:
                return JsonResponse({'error': 'Empty body'}, status=400)
            
            # Parse the JSON data from the request body
            data = json.loads(request.body.decode('utf-8'))
            title = data.get('title')
            body = data.get('body')

            if title and body:
                # Create a new Post object and save it to the database
                post = Post.objects.create(title=title, body=body)

                # Return the created post's information
                return JsonResponse({
                    'message': 'Post created successfully',
                    'post': {
                        'id': post.id,
                        'title': post.title,
                        'body': post.body,
                        'pub_date': post.pub_date.strftime('%Y-%m-%d %H:%M:%S')
                    }
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    else:
        # Method not allowed
        return JsonResponse({'error': 'Only GET and POST methods are supported'}, status=405)
    
def product_detail(request, id):
    product = get_object_or_404(Post.objects.prefetch_related('images'), id=id)
    reservations = None # 初始化為 None
    is_owner = False # 標記當前使用者是否為擁有者

    # 檢查當前登入使用者是否為商品擁有者
    if request.user.is_authenticated and product.owner == request.user:
        is_owner = True
        # 如果是擁有者，則獲取該商品的所有預約紀錄
        reservations = Reservation.objects.filter(product=product).order_by('-reserved_at')

    context = {
        'product': product,
        'is_owner': is_owner,
        'reservations': reservations, # 將預約列表傳遞給模板
        # 可以加入判斷是否已預約的邏輯
        'user_has_reserved': False # 預設使用者未預約
    }

    # 檢查當前登入使用者是否已預約此商品
    if request.user.is_authenticated:
        context['user_has_reserved'] = Reservation.objects.filter(product=product, user=request.user).exists()


    return render(request, "product_detail.html", context) 

def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    sort = request.GET.get('sort')
    products_query = category.posts.filter(is_sold=False).prefetch_related('images').all()
    categories = Category.objects.all()  
    # 排序刊登中的商品
    if sort == 'price_asc':
        products = products_query.order_by('price')
    elif sort == 'price_desc':
        products = products_query.order_by('-price')
    elif sort == 'date_desc':
        products = products_query.order_by('-pub_date')
    elif sort == 'date_asc':
        products = products_query.order_by('pub_date')
    else:
        products = products_query.order_by('-pub_date')  # 預設排序
    return render(request, 'category_products.html', {
        'category': category,
        'products': products,
        'categories': categories,  # 傳給 base.html 的下拉選單用
        'sort': sort,
    })

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # 建立新使用者
            auth_login(request, user) # 註冊後自動登入 (可選)
            messages.success(request, "註冊成功！歡迎加入我們！")
            return redirect('index')  # 註冊成功後導向首頁
        else:
            # 表單無效時，顯示具體的錯誤訊息
            for field in form:
                for error in field.errors:
                    messages.error(request, f"{field.label}: {error}")
    else:
        form = CustomUserCreationForm()
    return render(request, "register.html", {'form': form}) # 將 form 傳遞給模板

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                # 可以加上 ?next=/some/path 來導向登入前的頁面
                return redirect('index') # 登入成功後導向首頁
            else:
                # 可以加入無效登入的錯誤訊息
                pass
        else:
            # 可以加入表單無效的錯誤訊息
            pass
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {'form': form}) # 將 form 傳遞給模板


def sell(request):
    if request.method == 'POST':
        # 處理表單提交
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        category_id = request.POST.get('category')  # 獲取選擇的分類 ID
        images = request.FILES.getlist('images')
        
        # 基本驗證
        if name and description and price and category_id and images: # 確保至少有一張圖片
            try:
                category = Category.objects.get(id=category_id)
                # 先建立 Post 物件
                new_post = Post.objects.create(
                    title=name,
                    body=description,
                    price=price,
                    category=category,
                    owner=request.user
                )
                is_first_image = True # 標記第一張圖片
                for img in images:
                    ProductImage.objects.create(
                        post=new_post,
                        image=img,
                        # 可以設定第一張為主圖
                        is_primary=is_first_image
                    )
                    is_first_image = False 

                messages.success(request, "商品已成功上架！")
                return redirect('index')
            except Category.DoesNotExist:
                 messages.error(request, "選擇的分類無效。")
            except Exception as e:
                 messages.error(request, f"上架時發生錯誤：{e}")
             

        else:
            # 提供更明確的錯誤訊息
            error_message = "請填寫所有欄位並上傳至少一張圖片。"
            if not images:
                error_message = "請至少上傳一張商品圖片。"
            messages.error(request, error_message)

            return render(request, "sell.html", {
                'error': '請填寫所有欄位並上傳圖片',
                'categories': Category.objects.all()  # 傳遞分類資料
            })

    # 如果是 GET 請求，顯示空表單
    return render(request, "sell.html", {
        'categories': Category.objects.all()  # 傳遞分類資料
    })

def combined_search(request):
    query = request.GET.get('q', '')
    product_results = Post.objects.none() 
    seller_results = CustomUser.objects.none()

    if query:

        product_results = Post.objects.prefetch_related('images', 'owner').filter(
            (Q(title__icontains=query) | Q(body__icontains=query)) & Q(is_sold=False)
        ).distinct() 
 
        seller_results = CustomUser.objects.filter(username__icontains=query)

    context = {
        'query': query,
        'product_results': product_results,
        'seller_results': seller_results,
    }

    return render(request, "combined_search.html", context) #

def seller_profile(request, seller_id):
    seller = get_object_or_404(CustomUser, id=seller_id)

    sort = request.GET.get('sort') 

    # 獲取賣家的所有商品
    seller_posts = seller.posts.all()

    # 分開刊登中和已售出的商品
    active_posts = seller_posts.filter(is_sold=False)
    sold_posts = seller_posts.filter(is_sold=True)

    # 排序刊登中的商品
    if sort == 'price_asc':
        active_posts = active_posts.order_by('price')
    elif sort == 'price_desc':
        active_posts = active_posts.order_by('-price')
    elif sort == 'date_desc':
        active_posts = active_posts.order_by('-pub_date')
    elif sort == 'date_asc':
        active_posts = active_posts.order_by('pub_date')
    else:
        active_posts = active_posts.order_by('-pub_date')  # 預設排序

    # 排序已售出的商品
    if sort == 'price_asc':
        sold_posts = sold_posts.order_by('price')
    elif sort == 'price_desc':
        sold_posts = sold_posts.order_by('-price')
    elif sort == 'date_desc':
        sold_posts = sold_posts.order_by('-pub_date')
    elif sort == 'date_asc':
        sold_posts = sold_posts.order_by('pub_date')
    else:
        sold_posts = sold_posts.order_by('-pub_date')  # 預設排序

    reviews = Rating.objects.filter(rated=seller).order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('score'))['score__avg']
    
    return render(request, "seller_profile.html", {
        'seller': seller,
        'active_posts': active_posts,
        'sold_posts': sold_posts,
        'sort': sort,
        'reviews': reviews,
        'avg_rating': avg_rating,
    })


def add_to_favorites(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user

    # 檢查是否已經收藏，避免重複添加
    if post not in user.favorite_posts.all():
        user.favorite_posts.add(post) # 通過 user 的 favorite_posts 欄位添加
        messages.success(request, "收藏成功")
    else:
        messages.info(request, "您已經收藏過此商品。")
    return redirect('product_detail', post_id=post.id)

# +++ 新增 reserve_product View +++
@login_required
def reserve_product(request, id):
    product = get_object_or_404(Post, id=id)
    user = request.user
    try:
        reservation, created = Reservation.objects.get_or_create(
            product=product,
            user=user,
            defaults={'reserved_at': timezone.now()} # 使用 timezone.now()
        )
        if created:
            messages.success(request, f"成功預約商品：{product.title}")
        else:
            messages.info(request, "您已經預約過此商品。")
    except Exception as e:
        messages.error(request, f"預約時發生錯誤: {e}")

    return redirect('product_detail', id=id) # 重導回商品頁面

# +++ (可選) 新增取消預約 View +++
@login_required
def cancel_reservation(request, id):
    product = get_object_or_404(Post, id=id)
    user = request.user

    try:
        reservation = Reservation.objects.get(product=product, user=user)
        reservation.delete()
      
        messages.success(request, f"已取消預約商品：{product.title}")
    except Reservation.DoesNotExist:
        messages.warning(request, "您並未預約此商品。")
    except Exception as e:
        messages.error(request, f"取消預約時發生錯誤: {e}")

    return redirect('product_detail', id=id)



@login_required
def mark_as_sold(request, id):
    # 使用 get_object_or_404 確保商品存在，同時只允許擁有者操作
    product = get_object_or_404(Post, id=id, owner=request.user)

    if request.method == 'POST': 
        # 將商品標示為已售出
        product.is_sold = True
        product.save()
        # ✅ 嘗試找到有預約的買家
        reservation = Reservation.objects.filter(product=product).first()
        if reservation:
            buyer = reservation.user
            # ✅ 建立通知
            Notification.objects.create(
                user=buyer,
                message=f"你預約的商品『{product.title}』已成功購買！"
            )
        messages.success(request, f"商品 '{product.title}' 已成功標示為已售出。")
        return redirect('profile')
     
    else:
        messages.warning(request, "無效的操作請求。")
        return redirect('profile')
    
@login_required
def choose_buyer(request, product_id):
    product = get_object_or_404(Post, id=product_id, owner=request.user)

    if product.is_sold:
        messages.warning(request, "這個商品已經售出，不能再選買家了！")
        return redirect('product_detail', id=product_id)
    
    if request.method == 'POST':
        buyer_id = request.POST.get('buyer_id')
        if buyer_id:
            try:
                # 使用 CustomUser 模型來獲取買家對象
                buyer = CustomUser.objects.get(id=buyer_id)
                
                # 標記商品為已售出
                product.is_sold = True
                product.buyer = buyer
                product.purchase_time = timezone.now()
                product.save()

                # 刪除該商品的所有預約紀錄
                Reservation.objects.filter(product=product).delete()

                # 建立通知給買家
                Notification.objects.create(
                    user=buyer,
                    message=f"你預約的商品『{product.title}』已成功購買！"
                )
                # 建立通知給賣家
                Notification.objects.create(
                    user=product.owner,
                    message=f"你的商品『{product.title}』已成功售出給 {buyer.username}！"
                )
                messages.success(request, f"商品 '{product.title}' 已成功售出給 {buyer.username}！")
                return redirect('profile')
            except CustomUser.DoesNotExist:
                messages.error(request, "所選的買家不存在。")
        else:
            messages.error(request, "請選擇一位買家。")

    return redirect('product_detail', id=product_id)

@login_required
def notification_list(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    notifications = request.user.notifications.order_by('-created_at')
    return render(request, 'notification_list.html', {  # 這裡改成 'notification_list.html'
        'notifications': notifications,
    })
@login_required
def rate_seller(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    seller = post.owner

    if request.method == 'POST':
        score = request.POST.get('score')
        comment = request.POST.get('comment')
        if score:
            try:
                score = int(score)
                Rating.objects.create(rater=request.user, rated=seller, post=post, score=score, comment=comment)
                messages.success(request, "評分成功！")
                return redirect('profile')
            except ValueError:
                messages.error(request, "請選擇有效的評分。")
        else:
            messages.error(request, "請選擇評分。")

    return render(request, "rate_seller.html", {'post': post, 'seller': seller})




def some_view(request):
    # 假設獲得了一個 buyer_id
    buyer_id = request.POST.get('buyer_id')
    try:
        buyer = get_object_or_404(CustomUser, id=buyer_id)
        # 創建或更新 Post 記錄
        post = Post.objects.create("Some Title", buyer=buyer)
    except CustomUser.DoesNotExist:
        # 處理用戶不存在的情況
        pass