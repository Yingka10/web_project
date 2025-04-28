from django.contrib import admin
from mywebsite.models import Post, Category, CustomUser, Notification, Reservation, Rating, ProductImage

admin.site.register(Post)
admin.site.register(Category)
admin.site.register(CustomUser)
admin.site.register(Notification)
admin.site.register(Reservation)
admin.site.register(Rating)
admin.site.register(ProductImage)