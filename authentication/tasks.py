"""
Email Tasks for Account Management
"""

from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import logging

logger = logging.getLogger(__name__)


@shared_task(name='send_verification_email')
def send_verification_email(user_id, verification_token, frontend_url):
    """
    Send email verification link
    """
    from authentication.models import User
    
    try:
        user = User.objects.get(id=user_id)
        
        # Create verification URL
        verification_url = f"{frontend_url}/verify-email/{verification_token}/"
        
        # Render HTML email
        html_content = render_to_string('emails/verify_email.html', {
            'user': user,
            'verification_url': verification_url,
            'site_name': 'ChurchConnect',
        })
        text_content = strip_tags(html_content)
        
        # Create email
        subject = 'Verify your ChurchConnect account'
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return False
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return False


@shared_task(name='send_password_reset_email')
def send_password_reset_email(user_id, reset_token, frontend_url):
    """
    Send password reset link
    """
    from authentication.models import User
    
    try:
        user = User.objects.get(id=user_id)
        
        # Create reset URL
        reset_url = f"{frontend_url}/reset-password/{reset_token}/"
        
        # Render HTML email
        html_content = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_url': reset_url,
            'site_name': 'ChurchConnect',
        })
        text_content = strip_tags(html_content)
        
        # Create email
        subject = 'Reset your ChurchConnect password'
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Password reset email sent to {user.email}")
        return True
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return False
    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        return False


@shared_task(name='send_welcome_email')
def send_welcome_email(user_id):
    """
    Send welcome email to new users
    """
    from authentication.models import User
    
    try:
        user = User.objects.get(id=user_id)
        
        # Render HTML email
        html_content = render_to_string('emails/welcome.html', {
            'user': user,
            'site_name': 'ChurchConnect',
            'church_name': user.church_branch.name if user.church_branch else 'ChurchConnect',
        })
        text_content = strip_tags(html_content)
        
        # Create email
        subject = f'Welcome to ChurchConnect!'
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return False
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return False


@shared_task(name='send_password_changed_email')
def send_password_changed_email(user_id):
    """
    Notify user that their password was changed
    """
    from authentication.models import User
    
    try:
        user = User.objects.get(id=user_id)
        
        # Render HTML email
        html_content = render_to_string('emails/password_changed.html', {
            'user': user,
            'site_name': 'ChurchConnect',
        })
        text_content = strip_tags(html_content)
        
        # Create email
        subject = 'Your password has been changed'
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Password changed notification sent to {user.email}")
        return True
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return False
    except Exception as e:
        logger.error(f"Failed to send password changed email: {str(e)}")
        return False