# chat/models.py
from django.db import models
from django.conf import settings
#from mywebsite.models import Post
from django.utils import timezone

class Conversation(models.Model):
   
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='conversation_user1',
        db_column='buyer_id'
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='conversation_user2',
        db_column='seller_id'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最後更新")

    def save(self, *args, **kwargs):
        # 自動依使用者 ID 排序，較小的放在 user1
        if self.user1.id > self.user2.id:
            self.user1, self.user2 = self.user2, self.user1
        # 確保每次保存時都更新 updated_at
        if 'update_fields' not in kwargs or 'updated_at' in kwargs.get('update_fields', []):
             self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "對話"
        verbose_name_plural = "對話紀錄"
        ordering = ['-updated_at']
        unique_together = (("user1", "user2"),)

    def __str__(self):
        return f"{self.user1.username} 與 {self.user2.username}"


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
    is_read = models.BooleanField(default=False, verbose_name="是否已讀")

    class Meta:
        verbose_name = "訊息"
        verbose_name_plural = "訊息紀錄"
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"