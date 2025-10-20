# notifications/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from authentication.models import User
from django.utils import timezone


class Notification(models.Model):
    """
    Unified notification system for ChurchConnect
    Supports in-app, email, and future push/SMS
    """

    class Type(models.TextChoices):
        EVENT = 'event', _('Event')
        DONATION = 'donation', _('Donation')
        ANNOUNCEMENT = 'announcement', _('Announcement')
        MESSAGE = 'message', _('Message')
        ATTENDANCE = 'attendance', _('Attendance')
        SYSTEM = 'system', _('System')

    class Channel(models.TextChoices):
        IN_APP = 'in_app', _('In-App')
        EMAIL = 'email', _('Email')
        SMS = 'sms', _('SMS')
        PUSH = 'push', _('Push Notification')

    # Recipient
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('recipient')
    )

    # Content
    title = models.CharField(_('title'), max_length=200)
    message = models.TextField(_('message'))
    type = models.CharField(_('type'), max_length=20, choices=Type.choices)
    link = models.URLField(_('link'), blank=True, null=True, help_text=_("URL to redirect when clicked"))

    # Delivery
    channel = models.CharField(_('channel'), max_length=10, choices=Channel.choices, default=Channel.IN_APP)
    is_sent = models.BooleanField(_('sent'), default=False)
    sent_at = models.DateTimeField(_('sent at'), null=True, blank=True)

    # Status
    is_read = models.BooleanField(_('read'), default=False)
    read_at = models.DateTimeField(_('read at'), null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} → {self.recipient.get_full_name()}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    @property
    def is_unread(self):
        return not self.is_read