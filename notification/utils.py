# notifications/utils.py
from .models import Notification
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def create_notification(recipient, title, message, notif_type, link=None, send_email=False):
    """
    Create an in-app notification and optionally send email
    Usage:
        create_notification(
            recipient=user,
            title="New Event",
            message="You're invited to Sunday service",
            notif_type=Notification.Type.EVENT,
            link="/events/123"
        )
    """
    # Create in-app notification
    notif = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        type=notif_type,
        link=link,
        channel=Notification.Channel.IN_APP
    )

    # Optional: send email
    if send_email and recipient.email:
        try:
            send_mail(
                subject=title,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=True
            )
            notif.is_sent = True
            notif.sent_at = timezone.now()
            notif.channel = Notification.Channel.EMAIL
            notif.save(update_fields=['is_sent', 'sent_at', 'channel'])
        except Exception:
            # Log error in production (use logging)
            pass

    return notif