"""
WebSocket Consumers for Real-time Features
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumer for personal notifications
    Each user has their own notification channel
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'notifications_{self.user_id}'
        
        # Authenticate user
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return
        
        # Check if user is accessing their own notifications
        if str(user.id) != str(self.user_id):
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to notifications'
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'unknown')
            
            # Handle different message types
            if message_type == 'mark_read':
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def notification_message(self, event):
        """Receive notification from room group"""
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark notification as read"""
        from notification.models import Notification
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.read = True
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer for group/community chat
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f'chat_{self.group_id}'
        
        # Authenticate user
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return
        
        # Check if user is member of this group
        is_member = await self.check_group_membership(user.id, self.group_id)
        if not is_member:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify group that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': user.id,
                'username': user.get_full_name()
            }
        )
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        user = self.scope.get('user')
        
        # Notify group that user left
        if user and user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': user.id,
                    'username': user.get_full_name()
                }
            )
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            data = json.loads(text_data)
            message = data.get('message', '')
            user = self.scope.get('user')
            
            if not message.strip():
                return
            
            # Save message to database
            chat_message = await self.save_message(user.id, self.group_id, message)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': chat_message['id'],
                        'user_id': user.id,
                        'username': user.get_full_name(),
                        'message': message,
                        'timestamp': chat_message['timestamp']
                    }
                }
            )
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def chat_message(self, event):
        """Receive message from room group"""
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))
    
    async def user_joined(self, event):
        """User joined notification"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username']
        }))
    
    async def user_left(self, event):
        """User left notification"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username']
        }))
    
    @database_sync_to_async
    def check_group_membership(self, user_id, group_id):
        """Check if user is member of group"""
        from community.models import GroupMember
        try:
            return GroupMember.objects.filter(
                user_id=user_id,
                group_id=group_id,
                is_active=True
            ).exists()
        except:
            return False
    
    @database_sync_to_async
    def save_message(self, user_id, group_id, message):
        """Save chat message to database"""
        from community.models import ChatMessage
        from django.utils import timezone
        
        chat_message = ChatMessage.objects.create(
            group_id=group_id,
            sender_id=user_id,
            message=message
        )
        
        return {
            'id': chat_message.id,
            'timestamp': chat_message.created_at.isoformat()
        }


class EventUpdateConsumer(AsyncWebsocketConsumer):
    """
    Consumer for live event updates
    Real-time RSVP counts, attendance updates
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.event_id = self.scope['url_route']['kwargs']['event_id']
        self.room_group_name = f'event_{self.event_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current event stats
        stats = await self.get_event_stats(self.event_id)
        await self.send(text_data=json.dumps({
            'type': 'event_stats',
            'stats': stats
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def event_update(self, event):
        """Receive event update from room group"""
        # Send update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'update',
            'update': event['update']
        }))
    
    @database_sync_to_async
    def get_event_stats(self, event_id):
        """Get current event statistics"""
        from events.models import Event
        try:
            event = Event.objects.get(id=event_id)
            return {
                'total_rsvps': event.total_rsvps,
                'total_checked_in': event.total_checked_in,
                'spots_remaining': event.spots_remaining,
                'is_full': event.is_full
            }
        except Event.DoesNotExist:
            return {}