from .models import Category
from .models import Notification

def categories_processor(request):
    categories = Category.objects.all()
    return {'categories': categories}

def notification_context(request):
    if request.user.is_authenticated:
        # 先取得使用者所有通知（未切片）
        all_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        # 最新 3 筆通知
        recent_notifications = all_notifications[:3]
        # 未讀數量
        unread_count = all_notifications.filter(is_read=False).count()
    else:
        unread_count = 0
        recent_notifications = []

    return {
        'unread_count': unread_count,
        'recent_notifications': recent_notifications,
    }