"""
Event Management Models
Handles church events, RSVPs, and event attendance
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid


class EventCategory(models.Model):
    """
    Categories for events
    Example: Service, Conference, Meeting, Social, Outreach
    """
    
    name = models.CharField(_('category name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    color = models.CharField(
        _('color code'),
        max_length=7,
        default='#3498db',
        help_text=_('Hex color code for calendar display')
    )
    icon = models.CharField(
        _('icon'),
        max_length=50,
        blank=True,
        help_text=_('Icon name for display')
    )
    
    church_branch = models.ForeignKey(
        'denomination.ChurchBranch',
        on_delete=models.CASCADE,
        related_name='event_categories',
        verbose_name=_('church branch'),
        null=True,
        blank=True,
        help_text=_('Leave blank for denomination-wide categories')
    )
    
    # Status
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'event_categories'
        verbose_name = _('event category')
        verbose_name_plural = _('event categories')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Event(models.Model):
    """
    Main Event model
    """
    
    class EventType(models.TextChoices):
        REGULAR = 'regular', _('Regular Event')
        RECURRING = 'recurring', _('Recurring Event')
        SPECIAL = 'special', _('Special Event')
    
    class EventStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')
        CANCELLED = 'cancelled', _('Cancelled')
        COMPLETED = 'completed', _('Completed')
    
    class RecurrencePattern(models.TextChoices):
        NONE = 'none', _('Does not repeat')
        DAILY = 'daily', _('Daily')
        WEEKLY = 'weekly', _('Weekly')
        MONTHLY = 'monthly', _('Monthly')
        YEARLY = 'yearly', _('Yearly')
    
    # Basic Information
    title = models.CharField(_('event title'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=220, blank=True)
    description = models.TextField(_('description'))
    
    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
        verbose_name=_('category')
    )
    
    # Church & Organization
    church_branch = models.ForeignKey(
        'denomination.ChurchBranch',
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name=_('church branch')
    )
    
    department = models.ForeignKey(
        'denomination.BranchDepartment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
        verbose_name=_('department'),
        help_text=_('Department organizing this event')
    )
    
    # Event Details
    event_type = models.CharField(
        _('event type'),
        max_length=20,
        choices=EventType.choices,
        default=EventType.REGULAR
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=EventStatus.choices,
        default=EventStatus.DRAFT
    )
    
    # Date & Time
    start_datetime = models.DateTimeField(_('start date & time'))
    end_datetime = models.DateTimeField(_('end date & time'))
    
    all_day = models.BooleanField(_('all day event'), default=False)
    
    # Recurrence
    recurrence_pattern = models.CharField(
        _('recurrence pattern'),
        max_length=20,
        choices=RecurrencePattern.choices,
        default=RecurrencePattern.NONE
    )
    recurrence_end_date = models.DateField(
        _('recurrence end date'),
        null=True,
        blank=True
    )
    
    # Location
    location = models.CharField(_('location'), max_length=300)
    venue = models.CharField(_('venue name'), max_length=200, blank=True)
    address = models.TextField(_('full address'), blank=True)
    
    # Geolocation
    latitude = models.DecimalField(
        _('latitude'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    longitude = models.DecimalField(
        _('longitude'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    
    # Online Event
    is_online = models.BooleanField(_('online event'), default=False)
    meeting_link = models.URLField(_('meeting link'), blank=True)
    meeting_id = models.CharField(_('meeting ID'), max_length=100, blank=True)
    meeting_password = models.CharField(_('meeting password'), max_length=100, blank=True)
    
    # Capacity
    max_attendees = models.PositiveIntegerField(
        _('maximum attendees'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1)]
    )
    
    # Registration
    require_rsvp = models.BooleanField(_('require RSVP'), default=True)
    rsvp_deadline = models.DateTimeField(_('RSVP deadline'), null=True, blank=True)
    allow_guests = models.BooleanField(_('allow guests'), default=False)
    max_guests_per_person = models.PositiveIntegerField(
        _('max guests per person'),
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Visibility
    is_public = models.BooleanField(
        _('public event'),
        default=False,
        help_text=_('Visible to non-members')
    )
    is_featured = models.BooleanField(_('featured'), default=False)
    
    # Media
    banner_image = models.ImageField(
        _('banner image'),
        upload_to='events/banners/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Organizer
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organized_events',
        verbose_name=_('organizer')
    )
    
    # Contact
    contact_person = models.CharField(_('contact person'), max_length=200, blank=True)
    contact_email = models.EmailField(_('contact email'), blank=True)
    contact_phone = models.CharField(_('contact phone'), max_length=20, blank=True)
    
    # Additional Info
    dress_code = models.CharField(_('dress code'), max_length=100, blank=True)
    special_instructions = models.TextField(_('special instructions'), blank=True)
    tags = models.CharField(
        _('tags'),
        max_length=300,
        blank=True,
        help_text=_('Comma-separated tags')
    )
    
    # Reminders
    send_reminder = models.BooleanField(_('send reminder'), default=True)
    reminder_hours_before = models.PositiveIntegerField(
        _('reminder hours before'),
        default=24,
        help_text=_('Send reminder X hours before event')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'events'
        verbose_name = _('event')
        verbose_name_plural = _('events')
        ordering = ['-start_datetime']
    
    def __str__(self):
        return f"{self.title} - {self.start_datetime.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        """Auto-generate slug"""
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    @property
    def is_past(self):
        """Check if event is in the past"""
        return self.end_datetime < timezone.now()
    
    @property
    def is_upcoming(self):
        """Check if event is upcoming"""
        return self.start_datetime > timezone.now()
    
    @property
    def is_ongoing(self):
        """Check if event is currently ongoing"""
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime
    
    @property
    def duration_hours(self):
        """Calculate event duration in hours"""
        delta = self.end_datetime - self.start_datetime
        return round(delta.total_seconds() / 3600, 2)
    
    @property
    def total_rsvps(self):
        """Get total RSVP count"""
        return self.rsvps.filter(status=RSVP.RSVPStatus.GOING).count()
    
    @property
    def total_checked_in(self):
        """Get total checked-in attendees"""
        return self.event_attendances.filter(checked_in=True).count()
    
    @property
    def is_full(self):
        """Check if event has reached capacity"""
        if self.max_attendees:
            return self.total_rsvps >= self.max_attendees
        return False
    
    @property
    def spots_remaining(self):
        """Calculate remaining spots"""
        if self.max_attendees:
            return max(0, self.max_attendees - self.total_rsvps)
        return None


class RSVP(models.Model):
    """
    Event RSVP/Registration model
    """
    
    class RSVPStatus(models.TextChoices):
        GOING = 'going', _('Going')
        NOT_GOING = 'not_going', _('Not Going')
        MAYBE = 'maybe', _('Maybe')
        WAITLIST = 'waitlist', _('Waitlist')
    
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='rsvps',
        verbose_name=_('event')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='event_rsvps',
        verbose_name=_('user')
    )
    
    status = models.CharField(
        _('RSVP status'),
        max_length=20,
        choices=RSVPStatus.choices,
        default=RSVPStatus.GOING
    )
    
    # Guest Information
    number_of_guests = models.PositiveIntegerField(
        _('number of guests'),
        default=0,
        validators=[MinValueValidator(0)]
    )
    guest_names = models.TextField(
        _('guest names'),
        blank=True,
        help_text=_('Names of guests (one per line)')
    )
    
    # Additional Info
    dietary_requirements = models.TextField(_('dietary requirements'), blank=True)
    special_needs = models.TextField(_('special needs'), blank=True)
    notes = models.TextField(_('notes'), blank=True)
    
    # Confirmation
    confirmation_code = models.UUIDField(
        _('confirmation code'),
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    confirmed = models.BooleanField(_('confirmed'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'event_rsvps'
        verbose_name = _('RSVP')
        verbose_name_plural = _('RSVPs')
        ordering = ['-created_at']
        unique_together = ['event', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.event.title} ({self.status})"
    
    @property
    def total_attendees(self):
        """Total attendees including guests"""
        return 1 + self.number_of_guests


class EventAttendance(models.Model):
    """
    Track actual attendance at events (check-in/check-out)
    """
    
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='event_attendances',
        verbose_name=_('event')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='event_attendances',
        verbose_name=_('user')
    )
    
    # Check-in/out
    checked_in = models.BooleanField(_('checked in'), default=False)
    check_in_time = models.DateTimeField(_('check-in time'), null=True, blank=True)
    check_out_time = models.DateTimeField(_('check-out time'), null=True, blank=True)
    
    # Check-in method
    check_in_method = models.CharField(
        _('check-in method'),
        max_length=20,
        choices=[
            ('manual', _('Manual')),
            ('qr_code', _('QR Code')),
            ('nfc', _('NFC')),
            ('facial', _('Facial Recognition')),
        ],
        default='manual'
    )
    
    # Notes
    notes = models.TextField(_('notes'), blank=True)
    
    # Who recorded it
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_event_attendances',
        verbose_name=_('recorded by')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'event_attendances'
        verbose_name = _('event attendance')
        verbose_name_plural = _('event attendances')
        ordering = ['-check_in_time']
        unique_together = ['event', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.event.title}"
    
    @property
    def duration(self):
        """Calculate attendance duration"""
        if self.check_in_time and self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            return round(delta.total_seconds() / 3600, 2)
        return None


class EventReminder(models.Model):
    """
    Track reminders sent for events
    """
    
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='reminders',
        verbose_name=_('event')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='event_reminders',
        verbose_name=_('user')
    )
    
    # Reminder details
    reminder_type = models.CharField(
        _('reminder type'),
        max_length=20,
        choices=[
            ('email', _('Email')),
            ('sms', _('SMS')),
            ('push', _('Push Notification')),
            ('in_app', _('In-App')),
        ],
        default='email'
    )
    
    sent = models.BooleanField(_('sent'), default=False)
    sent_at = models.DateTimeField(_('sent at'), null=True, blank=True)
    
    # Status
    delivery_status = models.CharField(
        _('delivery status'),
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('sent', _('Sent')),
            ('delivered', _('Delivered')),
            ('failed', _('Failed')),
        ],
        default='pending'
    )
    
    error_message = models.TextField(_('error message'), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        db_table = 'event_reminders'
        verbose_name = _('event reminder')
        verbose_name_plural = _('event reminders')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reminder for {self.user.get_full_name()} - {self.event.title}"