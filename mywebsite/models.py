from django.db import models
from django.contrib.auth.models import User

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
    image = models.ImageField(upload_to='products/', blank=True, null=True)  # 新增圖片欄位
    pub_date = models.DateTimeField(auto_now_add=True)
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

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.title
    
