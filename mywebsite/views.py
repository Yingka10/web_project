from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from mywebsite.models import Post,Category

from django.http import JsonResponse
import json

def homepage(request):
    products = Post.objects.all()  # 獲取所有商品
    categories = Category.objects.all()  # 獲取所有分類
    return render(request, "index.html", {'products': products, 'categories': categories})

def get_db_result(request):
    posts = Post.objects.all()
    return render(request, "index_get_db_result.html", locals())

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
    product = get_object_or_404(Post, id=id)
    return render(request, "product_detail.html", {'product': product})

def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    # 透過 models.ForeignKey 的 related_name 反查該分類下的所有商品
    products = category.posts.all()
    return render(request, "category_products.html", {'category': category, 'products': products})

def register(request):
    return render(request, "register.html")

def login(request):
    return render(request, "login.html")

def profile(request):
    return render(request, "profile.html")

def sell(request):
    if request.method == 'POST':
        # 處理表單提交
        # 從 request.POST 獲取文字資料
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        # 從 request.FILES 獲取檔案資料
        image = request.FILES.get('image')

        # 簡單的驗證 (確保必要欄位存在)
        if name and description and price and image:
            # 創建 Post 物件並儲存到資料庫
            # 注意：表單中的 'name' 對應模型的 'title'
            Post.objects.create(
                title=name,
                body=description,
                price=price,
                image=image
            )
            # 新增成功後，重定向到首頁，使用者就能看到新上架的商品
            return redirect('index')
        else:
            # 如果資料不完整，可以選擇顯示錯誤訊息或重新渲染表單
            # 這裡我們先簡單地重新渲染空表單
            # 更完善的做法是使用 Django Forms 來處理驗證和錯誤顯示
            return render(request, "sell.html", {'error': '請填寫所有欄位並上傳圖片'})

    # 如果是 GET 請求，像之前一樣顯示空表單
    return render(request, "sell.html")

def product_search(request):
    # 從 GET 請求中取得關鍵字，參數名稱 "q" 可以依需求修改
    query = request.GET.get('q', '')
    
    # 如果有輸入關鍵字，則進行搜尋
    if query:
        # 使用 Q 可在多個欄位中進行搜尋，例如商品標題和內文
        results = Post.objects.filter(
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
