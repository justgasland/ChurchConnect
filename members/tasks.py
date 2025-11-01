"""
Background Tasks for Members
"""

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from datetime import date
import logging

logger = logging.getLogger(__name__)


@shared_task(name='send_birthday_wishes')
def send_birthday_wishes():
    """
    Send birthday wishes to members
    Runs daily at 8 AM via Celery Beat
    """
    from apps.accounts.models import UserProfile
    
    today = date.today()
    
    try:
        # Get all profiles with birthday today
        birthday_profiles = UserProfile.objects.filter(
            date_of_birth__month=today.month,
            date_of_birth__day=today.day
        ).select_related('user')
        
        total_sent = 0
        
        for profile in birthday_profiles:
            if profile.user.is_active:
                send_birthday_email.delay(profile.user.id)
                total_sent += 1
        
        logger.info(f"Birthday wishes: {total_sent} sent")
        return f"Sent {total_sent} birthday wishes"
        
    except Exception as e:
        logger.error(f"Failed to send birthday wishes: {str(e)}")
        return f"Error: {str(e)}"


@shared_task(name='send_birthday_email')
def send_birthday_email(user_id):
    """
    Send individual birthday email
    """
    from apps.accounts.models import User
    
    try:
        user = User.objects.get(id=user_id)
        
        # Render HTML email
        html_content = render_to_string('emails/birthday.html', {
            'user': user,
            'church_name': user.church_branch.name if user.church_branch else 'ChurchConnect',
            'site_name': 'ChurchConnect',
        })
        text_content = strip_tags(html_content)
        
        # Create email
        subject = f'🎉 Happy Birthday, {user.first_name}!'
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Birthday email sent to {user.email}")
        return True
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return False
    except Exception as e:
        logger.error(f"Failed to send birthday email: {str(e)}")
        return False


@shared_task(name='send_new_member_welcome')
def send_new_member_welcome(member_id):
    """
    Send welcome email to new members
    """
    from apps.members.models import Member
    
    try:
        member = Member.objects.select_related('user').get(id=member_id)
        user = member.user
        
        # Render HTML email
        html_content = render_to_string('emails/new_member_welcome.html', {
            'user': user,
            'member': member,
            'church_name': user.church_branch.name if user.church_branch else 'ChurchConnect',
            'site_name': 'ChurchConnect',
        })
        text_content = strip_tags(html_content)
        
        # Create email
        subject = f'Welcome to {user.church_branch.name if user.church_branch else "ChurchConnect"}!'
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"New member welcome sent to {user.email}")
        return True
        
    except Member.DoesNotExist:
        logger.error(f"Member {member_id} not found")
        return False
    except Exception as e:
        logger.error(f"Failed to send new member welcome: {str(e)}")
        return False