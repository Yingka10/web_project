from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from django.utils import timezone

class Category(models.Model):
    name = models.CharField("分類名稱", max_length=100, unique=True)
    description = models.TextField("描述", blank=True, null=True)

    class Meta:
        verbose_name = "分類"
        verbose_name_plural = "分類"

    def __str__(self):
        return self.name
    
class Post(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # 新增價格欄位
    pub_date = models.DateTimeField(auto_now_add=True)
    buyer = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='purchased_posts')
    # 新增與 Category 的關聯，若你希望此欄位為必填就省略 null 與 blank 參數
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name="分類",
        null=True,
        blank=True  # 若商品不一定要分類，可以設置 blank=True
    )
    # 新增「收藏」欄位，儲存哪些使用者收藏此商品
    favorites = models.ManyToManyField(
        User,
        blank=True,
        related_name='favorite_posts',
        verbose_name="收藏的使用者"
    )
    # 上架者欄位：記錄誰發佈了這個商品
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name="賣家",
        null=True,
        blank=True
    )
    # 新增：標記商品是否已被預約或售出 (可選，但建議)
    is_reserved = models.BooleanField("已被預約", default=False)
    is_sold = models.BooleanField("已售出", default=False)


    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.title
    
    def get_first_image(self):
        first_image = self.images.first()
        return first_image.image if first_image else None
    
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations', verbose_name="預約者")
    reserved_at = models.DateTimeField("預約時間", default=timezone.now)
    # 可以考慮加入其他欄位，例如：預約狀態 (pending, confirmed, cancelled)

    class Meta:
        verbose_name = "預約紀錄"
        verbose_name_plural = "預約紀錄"
        unique_together = ('product', 'user') # 同一個使用者對同一個商品只能預約一次

    def __str__(self):
        return f"{self.user.username} 預約了 {self.product.title}"

