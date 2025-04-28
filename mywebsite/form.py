# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(
        label="密碼",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text="密碼必須包含至少 8 個字符，不能全為數字。"
    )
    password2 = forms.CharField(
        label="確認密碼",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text="請再次輸入相同的密碼以確認。"
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email')  # 可以根據需要添加更多字段

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 可以添加更多的表單字段屬性
        self.fields['username'].help_text = "請輸入唯一的用戶名。"
        self.fields['email'].help_text = "請輸入有效的電子郵件地址。"