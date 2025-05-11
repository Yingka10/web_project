from .models import Category

def categories_processor(request):
    categories = Category.objects.all()
    return {'categories': categories}

def notification_context(request):
    if request.user.is_authenticated:
        unread_count = request.user.notifications.filter(is_read=False).count()
        notifications = request.user.notifications.all()[:5]
    else:
        unread_count = 0
        notifications = []

    return {
        'unread_count': unread_count,
        'notifications': notifications,
    }