"""
Django Admin Configuration for Event Management
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    EventCategory,
    Event,
    RSVP,
    EventAttendance,
    EventReminder
)


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    """Admin for EventCategory model"""
    
    list_display = ['name', 'color_display', 'church_branch', 'is_active', 'event_count', 'created_at']
    list_filter = ['is_active', 'church_branch']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'church_branch')
        }),
        ('Display', {
            'fields': ('color', 'icon')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def color_display(self, obj):
        """Display color"""
        return format_html(
            '<span style="background-color: {}; padding: 5px 15px; border-radius: 3px; color: white;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'
    
    def event_count(self, obj):
        """Get event count"""
        return obj.events.filter(status=Event.EventStatus.PUBLISHED).count()
    event_count.short_description = 'Events'


class RSVPInline(admin.TabularInline):
    """Inline admin for RSVPs"""
    model = RSVP
    extra = 0
    fields = ['user', 'status', 'number_of_guests', 'confirmed']
    raw_id_fields = ['user']
    readonly_fields = ['confirmation_code']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin for Event model"""
    
    list_display = [
        'title', 'category', 'church_branch', 'event_type',
        'status', 'start_datetime', 'is_online', 'total_rsvps',
        'is_full', 'is_featured'
    ]
    list_filter = [
        'status', 'event_type', 'category', 'church_branch',
        'is_online', 'is_public', 'is_featured', 'start_datetime'
    ]
    search_fields = ['title', 'description', 'location', 'tags']
    readonly_fields = [
        'slug', 'is_past', 'is_upcoming', 'is_ongoing',
        'duration_hours', 'total_rsvps', 'total_checked_in',
        'is_full', 'spots_remaining', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['organizer']
    date_hierarchy = 'start_datetime'
    inlines = [RSVPInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'category', 'church_branch', 'department')
        }),
        ('Event Details', {
            'fields': ('event_type', 'status', 'start_datetime', 'end_datetime', 'all_day', 'duration_hours')
        }),
        ('Recurrence', {
            'fields': ('recurrence_pattern', 'recurrence_end_date'),
            'classes': ('collapse',)
        }),
        ('Location', {
            'fields': ('location', 'venue', 'address', 'latitude', 'longitude')
        }),
        ('Online Event', {
            'fields': ('is_online', 'meeting_link', 'meeting_id', 'meeting_password'),
            'classes': ('collapse',)
        }),
        ('Registration & Capacity', {
            'fields': (
                'require_rsvp', 'rsvp_deadline', 'max_attendees',
                'allow_guests', 'max_guests_per_person',
                'total_rsvps', 'total_checked_in', 'is_full', 'spots_remaining'
            )
        }),
        ('Visibility', {
            'fields': ('is_public', 'is_featured')
        }),
        ('Media', {
            'fields': ('banner_image',)
        }),
        ('Organizer & Contact', {
            'fields': ('organizer', 'contact_person', 'contact_email', 'contact_phone')
        }),
        ('Additional Info', {
            'fields': ('dress_code', 'special_instructions', 'tags'),
            'classes': ('collapse',)
        }),
        ('Reminders', {
            'fields': ('send_reminder', 'reminder_hours_before')
        }),
        ('Status Indicators', {
            'fields': ('is_past', 'is_upcoming', 'is_ongoing')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        """Optimize query"""
        qs = super().get_queryset(request)
        return qs.select_related('category', 'church_branch', 'organizer', 'department')


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    """Admin for RSVP model"""
    
    list_display = [
        'user_name', 'event_title', 'status', 'number_of_guests',
        'total_attendees', 'confirmed', 'created_at'
    ]
    list_filter = ['status', 'confirmed', 'created_at', 'event__church_branch']
    search_fields = [
        'user__first_name', 'user__last_name', 'user__email',
        'event__title'
    ]
    readonly_fields = ['confirmation_code', 'total_attendees', 'created_at', 'updated_at']
    raw_id_fields = ['user', 'event']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('RSVP Information', {
            'fields': ('event', 'user', 'status', 'confirmed', 'confirmation_code')
        }),
        ('Guest Information', {
            'fields': ('number_of_guests', 'guest_names', 'total_attendees')
        }),
        ('Additional Information', {
            'fields': ('dietary_requirements', 'special_needs', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def user_name(self, obj):
        """Display user name"""
        return obj.user.get_full_name()
    user_name.short_description = 'User'
    user_name.admin_order_field = 'user__first_name'
    
    def event_title(self, obj):
        """Display event title"""
        return obj.event.title
    event_title.short_description = 'Event'
    event_title.admin_order_field = 'event__title'
    
    def get_queryset(self, request):
        """Optimize query"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'event', 'event__church_branch')


@admin.register(EventAttendance)
class EventAttendanceAdmin(admin.ModelAdmin):
    """Admin for EventAttendance model"""
    
    list_display = [
        'user_name', 'event_title', 'checked_in', 'check_in_time',
        'check_in_method', 'duration_display', 'recorded_by_name'
    ]
    list_filter = [
        'checked_in', 'check_in_method', 'check_in_time',
        'event__church_branch'
    ]
    search_fields = [
        'user__first_name', 'user__last_name',
        'event__title'
    ]
    readonly_fields = ['duration', 'created_at', 'updated_at']
    raw_id_fields = ['user', 'event', 'recorded_by']
    date_hierarchy = 'check_in_time'
    
    fieldsets = (
        ('Attendance Information', {
            'fields': ('event', 'user', 'checked_in')
        }),
        ('Check-in Details', {
            'fields': ('check_in_time', 'check_out_time', 'check_in_method', 'duration')
        }),
        ('Additional Information', {
            'fields': ('notes', 'recorded_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def user_name(self, obj):
        """Display user name"""
        return obj.user.get_full_name()
    user_name.short_description = 'User'
    user_name.admin_order_field = 'user__first_name'
    
    def event_title(self, obj):
        """Display event title"""
        return obj.event.title
    event_title.short_description = 'Event'
    event_title.admin_order_field = 'event__title'
    
    def recorded_by_name(self, obj):
        """Display who recorded"""
        return obj.recorded_by.get_full_name() if obj.recorded_by else '-'
    recorded_by_name.short_description = 'Recorded By'
    
    def duration_display(self, obj):
        """Display duration"""
        duration = obj.duration
        if duration:
            return f"{duration} hrs"
        return '-'
    duration_display.short_description = 'Duration'
    
    def get_queryset(self, request):
        """Optimize query"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'event', 'recorded_by', 'event__church_branch')


@admin.register(EventReminder)
class EventReminderAdmin(admin.ModelAdmin):
    """Admin for EventReminder model"""
    
    list_display = [
        'user_name', 'event_title', 'reminder_type',
        'sent', 'sent_at', 'delivery_status'
    ]
    list_filter = ['sent', 'reminder_type', 'delivery_status', 'sent_at']
    search_fields = [
        'user__first_name', 'user__last_name',
        'event__title'
    ]
    readonly_fields = ['created_at']
    raw_id_fields = ['user', 'event']
    date_hierarchy = 'sent_at'
    
    fieldsets = (
        ('Reminder Information', {
            'fields': ('event', 'user', 'reminder_type')
        }),
        ('Delivery Status', {
            'fields': ('sent', 'sent_at', 'delivery_status', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def user_name(self, obj):
        """Display user name"""
        return obj.user.get_full_name()
    user_name.short_description = 'User'
    
    def event_title(self, obj):
        """Display event title"""
        return obj.event.title
    event_title.short_description = 'Event'
    
    def get_queryset(self, request):
        """Optimize query"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'event')