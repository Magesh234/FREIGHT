from django.contrib import admin
from .models import FAQ, Article, Service

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order')
    list_editable = ('order',)
    list_filter = ('category',)
    search_fields = ('question', 'answer')

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'published_date', 'read_time_minutes')
    list_filter = ('category', 'author', 'published_date')
    search_fields = ('title', 'content')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon_class')
    search_fields = ('title', 'description')