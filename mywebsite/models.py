from django.db import models
from django.contrib.auth.models import User, AbstractUser
from cloudinary.models import CloudinaryField
from django.utils import timezone
from django.db.models import Avg
from django.conf import settings

class ChatMessage(models.Model):
    sender = models.CharField(max_length=150)
    content = models.TextField()
    seller_id = models.IntegerField()
    product_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.content[:20]}"
    
class Category(models.Model):
    name = models.CharField("分類名稱", max_length=100, unique=True)
    description = models.TextField("描述", blank=True, null=True)

    class Meta:
        verbose_name = "分類"
        verbose_name_plural = "分類"

    def __str__(self):
        return self.name
    
class CustomUser(AbstractUser):
    @property
    def average_rating(self):
        try:
            ratings = self.received_ratings.all()
            if ratings.exists():
                avg_score = ratings.aggregate(Avg('score'))['score__avg']
                return round(avg_score, 1)
            return None
        except Exception as e:
            print(f"Error calculating average rating: {e}")
            return None
    favorite_posts = models.ManyToManyField('Post', related_name='favorited_by_users')
    # 明确指定 related_name 参数，避免反向访问器冲突
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )


class Post(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    pub_date = models.DateTimeField(auto_now_add=True)
    buyer = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='purchased_posts')
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name="分類",
        null=True,
        blank=True
    )
    favorites = models.ManyToManyField(
        CustomUser,
        blank=True,
        related_name='favorited_posts',
        verbose_name="收藏的使用者"
    )
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name="賣家",
        null=True,
        blank=True
    )
    is_reserved = models.BooleanField("已被預約", default=False)
    is_sold = models.BooleanField("已售出", default=False)
    is_selected = models.BooleanField(default=False)
    purchase_time = models.DateTimeField("購買時間", null=True, blank=True)

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.title

    def get_first_image(self):
        first_image = self.images.first()
        return first_image.image if first_image else None


class Rating(models.Model):
    rater = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='given_ratings')
    rated = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_ratings')
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    score = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('rater', 'rated', 'post')

    def __str__(self):
        return f"{self.rater.username} 給 {self.rated.username} 的評分：{self.score}"
    
class ProductImage(models.Model):
    post = models.ForeignKey(Post, related_name='images', on_delete=models.CASCADE, verbose_name="商品")
    image = CloudinaryField(verbose_name="圖片")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="上傳時間")
    is_primary = models.BooleanField(default=False, verbose_name="主要圖片") # 可選：標記主要圖片

    class Meta:
        verbose_name = "商品圖片"
        verbose_name_plural = "商品圖片"
        ordering = ['-is_primary', 'uploaded_at'] # 主要圖片優先，其次按上傳時間

    def __str__(self):
        return f"{self.post.title} 的圖片"
        
# +++ 新增 Reservation 模型 +++
class Reservation(models.Model):
    product = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reservations', verbose_name="預約商品")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reservations', verbose_name="預約者")
    reserved_at = models.DateTimeField("預約時間", default=timezone.now)
    is_selected = models.BooleanField(default=False)
    # 可以考慮加入其他欄位，例如：預約狀態 (pending, confirmed, cancelled)


    class Meta:
        verbose_name = "預約紀錄"
        verbose_name_plural = "預約紀錄"
        unique_together = ('product', 'user') # 同一個使用者對同一個商品只能預約一次

    def __str__(self):
        return f"{self.user.username} 預約了 {self.product.title}"
    
class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"通知給 {self.user.username}: {self.message}"

