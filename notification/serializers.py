# notifications/serializers.py
from rest_framework import serializers
from .models import Notification
from authentication.serializers import UserSerializer


class NotificationSerializer(serializers.ModelSerializer):
    recipient_detail = UserSerializer(source='recipient', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'recipient_detail', 'title', 'message',
            'type', 'link', 'channel', 'is_sent', 'sent_at',
            'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'recipient_detail', 'is_sent', 'sent_at',
            'read_at', 'created_at'
        ]