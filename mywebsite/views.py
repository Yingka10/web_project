from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone # 引入 timezone
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from mywebsite.models import Post, Category, Reservation , ProductImage
from django.contrib import messages 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, authenticate
from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import cloudinary
from django.conf import settings
from django.contrib.auth.models import User
from .models import Post



cloudinary.config(
    cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
    api_secret=settings.CLOUDINARY_STORAGE['API_SECRET']
)

def homepage(request):
    products = Post.objects.filter(is_sold=False).prefetch_related('images').all()
    categories = Category.objects.all()
    return render(request, "index.html", {'products': products, 'categories': categories})

@login_required
def toggle_favorite(request, id):
    product = get_object_or_404(Post, id=id)
    # 如果目前使用者已收藏此商品，就移除；否則加入收藏
    if request.user in product.favorites.all():
        product.favorites.remove(request.user)
        messages.success(request, "✅ 已從收藏移除。")
    else:
        product.favorites.add(request.user)
        messages.success(request, "✅ 已加入收藏！")
    # 重導回前一個頁面
    return redirect(request.META.get('HTTP_REFERER', 'index'))

@login_required
def profile(request):
    favorites = request.user.favorite_posts.prefetch_related('images').all()
    all_my_posts = request.user.posts.prefetch_related('images').all() # 先獲取所有商品
    active_posts = all_my_posts.filter(is_sold=False) # 篩選出未售出的
    sold_posts = all_my_posts.filter(is_sold=True)   # 篩選出已售出的
    return render(request, "profile.html", {
        'favorites': favorites,
        'active_posts': active_posts,
        'sold_posts': sold_posts     
    })

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
    # 透過 models.ForeignKey 的 related_name 反查該分類下的所有商品
    products = category.posts.prefetch_related('images').all()
    categories = Category.objects.all()  # 加這行
    return render(request, 'category_products.html', {
        'category': category,
        'products': products,
        'categories': categories,  # 傳給 base.html 的下拉選單用
    })

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # 建立新使用者
            auth_login(request, user) # 註冊後自動登入 (可選)
            return redirect('index')  # 註冊成功後導向首頁
    else:
        form = UserCreationForm()
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

def product_search(request):
    # 從 GET 請求中取得關鍵字，參數名稱 "q" 可以依需求修改
    query = request.GET.get('q', '')
    
    # 如果有輸入關鍵字，則進行搜尋
    if query:
        # 使用 Q 可在多個欄位中進行搜尋，例如商品標題和內文
        results = Post.objects.prefetch_related('images').filter(
            Q(title__icontains=query) | Q(body__icontains=query)
        )
    else:
        # 如果沒有輸入關鍵字，可以傳回空的 QuerySet 或全部商品，視需求而定
        results = Post.objects.none()
    
    context = {
        'query': query,
        'results': results,
    }
    return render(request, "product_search.html", context)

def seller_profile(request, user_id):
    seller = get_object_or_404(User, id=user_id)
    seller_posts = seller.posts.all()
    return render(request, "seller_profile.html", {
        'seller': seller,
        'seller_posts': seller_posts
    })


def add_to_favorites(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    print("登入者：", request.user)
    print("賣家是：", post.owner)

    post.favorites.add(request.user)
    messages.success(request, "收藏成功")
    return redirect('post_detail', post_id=post.id)
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
        messages.success(request, f"商品 '{product.title}' 已成功標示為已售出。")
        return redirect('profile')
     
    else:
        messages.warning(request, "無效的操作請求。")
        return redirect('profile')
