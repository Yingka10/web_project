from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

# 註冊
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, '密碼不一致！')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, '使用者名稱已存在！')
            return redirect('register')

        user = User.objects.create_user(username=username, password=password)
        user.save()
        messages.success(request, '註冊成功！請登入。')
        return redirect('login')

    return render(request, 'accounts/register.html')


# 登入
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # 登入成功後導向首頁（你可以改成任何頁面）
        else:
            messages.error(request, '帳號或密碼錯誤！')
            return redirect('login')

    return render(request, 'accounts/login.html')


# 登出
def logout_view(request):
    logout(request)
    return redirect('login')
