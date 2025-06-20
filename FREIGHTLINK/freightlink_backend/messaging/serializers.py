from rest_framework import serializers
from .models import Conversation, Message
from accounts.serializers import UserProfileSerializer, UserSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['conversation', 'sender', 'timestamp']

class ConversationSerializer(serializers.ModelSerializer):
    # participants = UserSerializer(many=True, read_only=True)
    # To avoid recursion and simplify, you might just want participant usernames
    participant_usernames = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_messages_count = serializers.SerializerMethodField()


    class Meta:
        model = Conversation
        fields = '__all__'
        read_only_fields = ['participants', 'created_at', 'updated_at']

    def get_participant_usernames(self, obj):
        # Exclude the current user from the list if available in context
        request_user = self.context.get('request').user if 'request' in self.context else None
        return [p.username for p in obj.participants.all() if p != request_user]

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None

    def get_unread_messages_count(self, obj):
        request_user = self.context.get('request').user
        if request_user:
            return obj.messages.filter(is_read=False).exclude(sender=request_user).count()
        return 0