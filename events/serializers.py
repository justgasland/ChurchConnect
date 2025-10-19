"""
Serializers for Event Management
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from .models import (
    EventCategory,
    Event,
    RSVP,
    EventAttendance,
    EventReminder
)
from authentication.serializers import UserSerializer


class EventCategorySerializer(serializers.ModelSerializer):
    """Serializer for event categories"""
    
    event_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EventCategory
        fields = [
            'id', 'name', 'description', 'color', 'icon',
            'church_branch', 'is_active', 'event_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_event_count(self, obj):
        """Get total events in this category"""
        return obj.events.filter(status=Event.EventStatus.PUBLISHED).count()


class EventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing events"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    church_name = serializers.CharField(source='church_branch.name', read_only=True)
    organizer_name = serializers.CharField(source='organizer.get_full_name', read_only=True)
    
    is_past = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    is_ongoing = serializers.ReadOnlyField()
    total_rsvps = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    spots_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'category', 'category_name',
            'church_branch', 'church_name', 'event_type', 'status',
            'start_datetime', 'end_datetime', 'all_day', 'location',
            'is_online', 'require_rsvp', 'max_attendees', 'is_public',
            'is_featured', 'banner_image', 'organizer', 'organizer_name',
            'is_past', 'is_upcoming', 'is_ongoing', 'total_rsvps',
            'is_full', 'spots_remaining', 'created_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at']


class EventDetailSerializer(serializers.ModelSerializer):
    """Full serializer for event details"""
    
    category_detail = EventCategorySerializer(source='category', read_only=True)
    organizer_detail = UserSerializer(source='organizer', read_only=True)
    
    is_past = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    is_ongoing = serializers.ReadOnlyField()
    duration_hours = serializers.ReadOnlyField()
    total_rsvps = serializers.ReadOnlyField()
    total_checked_in = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    spots_remaining = serializers.ReadOnlyField()
    
    # User's RSVP status
    user_rsvp_status = serializers.SerializerMethodField()
    user_has_rsvpd = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_user_rsvp_status(self, obj):
        """Get current user's RSVP status"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            try:
                rsvp = obj.rsvps.get(user=request.user)
                return rsvp.status
            except RSVP.DoesNotExist:
                return None
        return None
    
    def get_user_has_rsvpd(self, obj):
        """Check if current user has RSVPd"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.rsvps.filter(user=request.user).exists()
        return False


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating events"""
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'category', 'church_branch',
            'department', 'event_type', 'status', 'start_datetime',
            'end_datetime', 'all_day', 'recurrence_pattern',
            'recurrence_end_date', 'location', 'venue', 'address',
            'latitude', 'longitude', 'is_online', 'meeting_link',
            'meeting_id', 'meeting_password', 'max_attendees',
            'require_rsvp', 'rsvp_deadline', 'allow_guests',
            'max_guests_per_person', 'is_public', 'is_featured',
            'banner_image', 'organizer', 'contact_person',
            'contact_email', 'contact_phone', 'dress_code',
            'special_instructions', 'tags', 'send_reminder',
            'reminder_hours_before'
        ]
    
    def validate(self, attrs):
        """Validate event data"""
        start = attrs.get('start_datetime')
        end = attrs.get('end_datetime')
        
        # Validate end datetime is after start datetime
        if start and end and end <= start:
            raise serializers.ValidationError({
                "end_datetime": "End time must be after start time."
            })
        
        # Validate RSVP deadline is before event start
        rsvp_deadline = attrs.get('rsvp_deadline')
        if rsvp_deadline and start and rsvp_deadline >= start:
            raise serializers.ValidationError({
                "rsvp_deadline": "RSVP deadline must be before event start time."
            })
        
        # Validate recurrence
        recurrence = attrs.get('recurrence_pattern')
        recurrence_end = attrs.get('recurrence_end_date')
        if recurrence and recurrence != Event.RecurrencePattern.NONE:
            if not recurrence_end:
                raise serializers.ValidationError({
                    "recurrence_end_date": "Recurrence end date is required for recurring events."
                })
        
        return attrs
    
    def create(self, validated_data):
        """Create event"""
        request = self.context.get('request')
        if request and request.user and not validated_data.get('organizer'):
            validated_data['organizer'] = request.user
        return super().create(validated_data)


class RSVPSerializer(serializers.ModelSerializer):
    """Serializer for RSVP"""
    
    user_detail = UserSerializer(source='user', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    total_attendees = serializers.ReadOnlyField()
    
    class Meta:
        model = RSVP
        fields = [
            'id', 'event', 'event_title', 'user', 'user_detail',
            'status', 'number_of_guests', 'guest_names',
            'dietary_requirements', 'special_needs', 'notes',
            'confirmation_code', 'confirmed', 'total_attendees',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'confirmation_code', 'created_at', 'updated_at']


class RSVPCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating RSVP"""
    
    class Meta:
        model = RSVP
        fields = [
            'event', 'status', 'number_of_guests', 'guest_names',
            'dietary_requirements', 'special_needs', 'notes'
        ]
    
    def validate(self, attrs):
        """Validate RSVP data"""
        event = attrs.get('event')
        number_of_guests = attrs.get('number_of_guests', 0)
        
        # Check if event allows guests
        if number_of_guests > 0 and event and not event.allow_guests:
            raise serializers.ValidationError({
                "number_of_guests": "This event does not allow guests."
            })
        
        # Check guest limit
        if event and number_of_guests > event.max_guests_per_person:
            raise serializers.ValidationError({
                "number_of_guests": f"Maximum {event.max_guests_per_person} guests allowed per person."
            })
        
        # Check if event is full
        if event and event.is_full and attrs.get('status') == RSVP.RSVPStatus.GOING:
            raise serializers.ValidationError({
                "event": "This event has reached maximum capacity."
            })
        
        # Check RSVP deadline
        if event and event.rsvp_deadline and timezone.now() > event.rsvp_deadline:
            raise serializers.ValidationError({
                "event": "RSVP deadline has passed."
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create RSVP"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['user'] = request.user
        return super().create(validated_data)


class EventAttendanceSerializer(serializers.ModelSerializer):
    """Serializer for event attendance"""
    
    user_detail = UserSerializer(source='user', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = EventAttendance
        fields = [
            'id', 'event', 'event_title', 'user', 'user_detail',
            'checked_in', 'check_in_time', 'check_out_time',
            'check_in_method', 'duration', 'notes', 'recorded_by',
            'recorded_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'recorded_by', 'created_at']
    
    def create(self, validated_data):
        """Create attendance record"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['recorded_by'] = request.user
        
        # Auto-set check_in_time if checked_in is True
        if validated_data.get('checked_in') and not validated_data.get('check_in_time'):
            validated_data['check_in_time'] = timezone.now()
        
        return super().create(validated_data)


class EventStatisticsSerializer(serializers.Serializer):
    """Serializer for event statistics"""
    
    total_events = serializers.IntegerField()
    upcoming_events = serializers.IntegerField()
    past_events = serializers.IntegerField()
    ongoing_events = serializers.IntegerField()
    total_rsvps = serializers.IntegerField()
    total_attendances = serializers.IntegerField()
    events_by_category = serializers.DictField()
    events_by_status = serializers.DictField()
    average_attendance_rate = serializers.FloatField()