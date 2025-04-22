"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from mywebsite.views import homepage, get_db_result, api, register, login, profile, sell, product_detail, category_products
from mywebsite import views

urlpatterns = [
    path('', homepage, name='index'),
    path('get_db_result/', get_db_result, name='get_db_result'),
    path('api/', api, name='api'),
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('profile/', profile, name='profile'),
    path('sell/', sell, name='sell'), # sell 頁面的 URL
    path('product/<int:id>/', product_detail, name='product_detail'),
    path('admin/', admin.site.urls),
    path('category/<int:category_id>/', category_products, name='category_products'),
    path('search/', views.product_search, name='product_search'),
    path('toggle_favorite/<int:id>/', views.toggle_favorite, name='toggle_favorite'),
]
# 僅在開發環境中添加 media URL
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)