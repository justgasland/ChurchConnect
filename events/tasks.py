"""
Background Tasks for Events
"""

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(name='send_event_reminders')
def send_event_reminders():
    """
    Send reminders for upcoming events
    Runs every hour via Celery Beat
    """
    from apps.events.models import Event, RSVP
    
    now = timezone.now()
    
    try:
        # Get events that are 24 hours away (with some buffer)
        upcoming_events = Event.objects.filter(
            status=Event.EventStatus.PUBLISHED,
            send_reminder=True,
            start_datetime__gte=now,
            start_datetime__lte=now + timedelta(hours=25)
        )
        
        total_sent = 0
        
        for event in upcoming_events:
            hours_until = (event.start_datetime - now).total_seconds() / 3600
            
            # Check if reminder should be sent
            if abs(hours_until - event.reminder_hours_before) <= 1:  # Within 1 hour window
                # Get all RSVPs who said they're going
                rsvps = RSVP.objects.filter(
                    event=event,
                    status=RSVP.RSVPStatus.GOING
                ).select_related('user')
                
                for rsvp in rsvps:
                    send_event_reminder_email.delay(event.id, rsvp.user.id)
                    total_sent += 1
        
        logger.info(f"Event reminders: {total_sent} sent")
        return f"Sent {total_sent} reminders"
        
    except Exception as e:
        logger.error(f"Failed to send event reminders: {str(e)}")
        return f"Error: {str(e)}"


@shared_task(name='send_event_reminder_email')
def send_event_reminder_email(event_id, user_id):
    """
    Send individual event reminder email
    """
    from apps.events.models import Event
    from apps.accounts.models import User
    
    try:
        event = Event.objects.get(id=event_id)
        user = User.objects.get(id=user_id)
        
        # Render HTML email
        html_content = render_to_string('emails/event_reminder.html', {
            'user': user,
            'event': event,
            'site_name': 'ChurchConnect',
        })
        text_content = strip_tags(html_content)
        
        # Create email
        subject = f'Reminder: {event.title}'
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Event reminder sent to {user.email} for {event.title}")
        return True
        
    except (Event.DoesNotExist, User.DoesNotExist):
        logger.error(f"Event {event_id} or User {user_id} not found")
        return False
    except Exception as e:
        logger.error(f"Failed to send event reminder: {str(e)}")
        return False


@shared_task(name='send_rsvp_confirmation_email')
def send_rsvp_confirmation_email(rsvp_id):
    """
    Send RSVP confirmation email
    """
    from apps.events.models import RSVP
    
    try:
        rsvp = RSVP.objects.select_related('event', 'user').get(id=rsvp_id)
        
        # Render HTML email
        html_content = render_to_string('emails/rsvp_confirmation.html', {
            'user': rsvp.user,
            'event': rsvp.event,
            'rsvp': rsvp,
            'site_name': 'ChurchConnect',
        })
        text_content = strip_tags(html_content)
        
        # Create email
        subject = f'RSVP Confirmed: {rsvp.event.title}'
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[rsvp.user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"RSVP confirmation sent to {rsvp.user.email}")
        return True
        
    except RSVP.DoesNotExist:
        logger.error(f"RSVP {rsvp_id} not found")
        return False
    except Exception as e:
        logger.error(f"Failed to send RSVP confirmation: {str(e)}")
        return False


@shared_task(name='send_event_cancelled_email')
def send_event_cancelled_email(event_id):
    """
    Notify attendees when event is cancelled
    """
    from apps.events.models import Event, RSVP
    
    try:
        event = Event.objects.get(id=event_id)
        
        # Get all RSVPs
        rsvps = RSVP.objects.filter(event=event).select_related('user')
        
        for rsvp in rsvps:
            # Render HTML email
            html_content = render_to_string('emails/event_cancelled.html', {
                'user': rsvp.user,
                'event': event,
                'site_name': 'ChurchConnect',
            })
            text_content = strip_tags(html_content)
            
            # Create email
            subject = f'Event Cancelled: {event.title}'
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[rsvp.user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
        
        logger.info(f"Event cancellation sent to {rsvps.count()} attendees")
        return True
        
    except Event.DoesNotExist:
        logger.error(f"Event {event_id} not found")
        return False
    except Exception as e:
        logger.error(f"Failed to send event cancellation: {str(e)}")
        return False