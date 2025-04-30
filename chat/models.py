from django.db import models
from django.conf import settings
from django.utils import timezone
# 假設 Post 模型在 shop 應用內，如果不同請修改 import 路徑
from mywebsite.models import Post

class Conversation(models.Model):
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='buyer_conversations',
        verbose_name="買家"
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='seller_conversations',
        verbose_name="賣家"
    )
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='conversations',
        verbose_name="商品"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    class Meta:
        verbose_name = "對話"
        verbose_name_plural = "對話紀錄"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.buyer.username} 與 {self.seller.username} - {self.post.title}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages',
        verbose_name="對話"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_messages',
        verbose_name="發送者"
    )
    content = models.TextField("訊息內容")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="發送時間")

    class Meta:
        verbose_name = "訊息"
        verbose_name_plural = "訊息紀錄"
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"