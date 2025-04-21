from django.contrib import admin
from mywebsite.models import Post, Category

# Register your models here.
admin.site.register(Post)
admin.site.register(Category)