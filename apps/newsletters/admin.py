from django.contrib import admin
from .models import News, Newsletter, UserCredit

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'type', 'localisation', 'postal_code')
    search_fields = ('title', 'summary', 'localisation')
    list_filter = ('type', 'news_type', 'date')

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at',)

@admin.register(UserCredit)
class UserCreditAdmin(admin.ModelAdmin):
    list_display = ('user', 'credits')
    search_fields = ('user__username',)
