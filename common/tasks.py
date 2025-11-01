"""
Common Background Tasks
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(name='send_email_task')
def send_email_task(subject, message, recipient_list, html_message=None):
    """
    Send email asynchronously
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Email sent successfully to {recipient_list}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


@shared_task(name='send_bulk_email_task')
def send_bulk_email_task(subject, message, recipient_list, html_message=None):
    """
    Send bulk emails in batches
    """
    batch_size = 50
    total_sent = 0
    
    for i in range(0, len(recipient_list), batch_size):
        batch = recipient_list[i:i + batch_size]
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=batch,
                html_message=html_message,
                fail_silently=False,
            )
            total_sent += len(batch)
            logger.info(f"Sent batch {i//batch_size + 1}: {len(batch)} emails")
        except Exception as e:
            logger.error(f"Failed to send batch {i//batch_size + 1}: {str(e)}")
    
    logger.info(f"Bulk email complete: {total_sent}/{len(recipient_list)} sent")
    return total_sent


@shared_task(name='generate_daily_reports')
def generate_daily_reports():
    """
    Generate daily reports for all churches
    """
    from denomination.models import ChurchBranch
    from django.db.models import Count
    
    logger.info("Starting daily report generation")
    
    try:
        branches = ChurchBranch.objects.filter(status='active')
        
        for branch in branches:
            # Generate report data
            yesterday = timezone.now() - timedelta(days=1)
            
            report_data = {
                'date': yesterday.date(),
                'branch': branch.name,
                'new_members': branch.users.filter(created_at__date=yesterday.date()).count(),
                'events': branch.events.filter(start_datetime__date=yesterday.date()).count(),
                # Add more metrics as needed
            }
            
            logger.info(f"Generated report for {branch.name}")
        
        return f"Reports generated for {branches.count()} branches"
    
    except Exception as e:
        logger.error(f"Failed to generate reports: {str(e)}")
        return f"Error: {str(e)}"


@shared_task(name='cleanup_expired_sessions')
def cleanup_expired_sessions():
    """
    Clean up expired sessions
    """
    from django.core.management import call_command
    
    try:
        call_command('clearsessions')
        logger.info("Expired sessions cleaned up")
        return "Success"
    except Exception as e:
        logger.error(f"Failed to cleanup sessions: {str(e)}")
        return f"Error: {str(e)}"


@shared_task(name='send_websocket_notification')
def send_websocket_notification(user_id, notification_data):
    """
    Send notification via WebSocket
    """
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{user_id}',
            {
                'type': 'notification_message',
                'notification': notification_data
            }
        )
        logger.info(f"WebSocket notification sent to user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send WebSocket notification: {str(e)}")
        return False