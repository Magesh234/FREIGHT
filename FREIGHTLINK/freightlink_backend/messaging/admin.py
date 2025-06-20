from django.contrib import admin
from .models import Conversation, Message

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    filter_horizontal = ('participants',)
    list_display = ('id', 'created_at', 'updated_at')
    search_fields = ('participants__username',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'timestamp', 'is_read', 'content')
    list_filter = ('is_read', 'timestamp', 'sender')
    search_fields = ('content', 'sender__username')
    raw_id_fields = ('conversation', 'sender')