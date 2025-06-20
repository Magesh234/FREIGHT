from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only show conversations where the current user is a participant
        return Conversation.objects.filter(participants=self.request.user).prefetch_related('messages')

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        # Ensure the current user is a participant of this conversation
        if request.user not in conversation.participants.all():
            return Response({"detail": "Not authorized to view this conversation."}, status=status.HTTP_403_FORBIDDEN)

        messages = conversation.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='send-message')
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        if request.user not in conversation.participants.all():
            return Response({"detail": "Not authorized to send message in this conversation."}, status=status.HTTP_403_FORBIDDEN)

        content = request.data.get('content')
        if not content:
            return Response({"detail": "Message content cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='start-conversation')
    def start_conversation(self, request):
        # Requires 'user_id' or 'username' of the other participant
        other_user_id = request.data.get('user_id')
        other_username = request.data.get('username')

        if not other_user_id and not other_username:
            return Response({"detail": "Either 'user_id' or 'username' is required to start a conversation."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            if other_user_id:
                other_user = User.objects.get(id=other_user_id)
            else:
                other_user = User.objects.get(username=other_username)
        except User.DoesNotExist:
            return Response({"detail": "Other user not found."}, status=status.HTTP_404_NOT_FOUND)

        if other_user == request.user:
            return Response({"detail": "Cannot start a conversation with yourself."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if a conversation already exists between these two users
        existing_conversation = Conversation.objects.filter(
            Q(participants=request.user) & Q(participants=other_user)
        ).annotate(num_participants=models.Count('participants')).filter(num_participants=2).first() # Ensure it's exactly between these two

        if existing_conversation:
            serializer = self.get_serializer(existing_conversation)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Create new conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
        conversation.save()

        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)