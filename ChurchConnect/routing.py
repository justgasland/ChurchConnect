"""
WebSocket URL Configuration
Routes WebSocket connections to appropriate consumers
"""

from django.urls import re_path
from common.consumers import (
    NotificationConsumer,
    ChatConsumer,
    EventUpdateConsumer,
)

websocket_urlpatterns = [
    # Notifications - Personal notifications for a user
    # ws://localhost:8000/ws/notifications/<user_id>/
    re_path(r'ws/notifications/(?P<user_id>\w+)/$', NotificationConsumer.as_asgi()),
    
    # Chat - Group/Community chat rooms
    # ws://localhost:8000/ws/chat/<group_id>/
    re_path(r'ws/chat/(?P<group_id>\w+)/$', ChatConsumer.as_asgi()),
    
    # Event Updates - Live event updates
    # ws://localhost:8000/ws/events/(?P<event_id>\w+)/
    re_path(r'ws/events/(?P<event_id>\w+)/$', EventUpdateConsumer.as_asgi()),
]