"""
Class-Based Views for Event Management
"""

from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    EventCategory,
    Event,
    RSVP,
    EventAttendance,
    EventReminder
)
from .serializers import (
    EventCategorySerializer,
    EventListSerializer,
    EventDetailSerializer,
    EventCreateUpdateSerializer,
    RSVPSerializer,
    RSVPCreateUpdateSerializer,
    EventAttendanceSerializer,
    EventStatisticsSerializer
)
from authentication.permissions import IsAnyAdmin


# ==================== EVENT CATEGORY VIEWS ====================

class EventCategoryListCreateView(generics.ListCreateAPIView):
    """
    List event categories or create a new one
    GET/POST /api/events/categories/
    """
    queryset = EventCategory.objects.filter(is_active=True)
    serializer_class = EventCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        """Filter by user's church or denomination"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_super_admin():
            return queryset
        
        if user.church_branch:
            return queryset.filter(
                Q(church_branch=user.church_branch) | Q(church_branch__isnull=True)
            )
        
        return queryset.filter(church_branch__isnull=True)
    
    def get_permissions(self):
        """Anyone can view, admins can create"""
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAnyAdmin()]
        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        """Create event category"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Event category created successfully!',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        """List event categories"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })


class EventCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update or delete an event category
    GET/PUT/PATCH/DELETE /api/events/categories/<id>/
    """
    queryset = EventCategory.objects.all()
    serializer_class = EventCategorySerializer
    permission_classes = [IsAuthenticated, IsAnyAdmin]
    lookup_field = 'id'
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Event category updated successfully!',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Event category deactivated successfully!'
        })


# ==================== EVENT VIEWS ====================

class EventListCreateView(generics.ListCreateAPIView):
    """
    List all events or create a new one
    GET/POST /api/events/
    """
    queryset = Event.objects.select_related('category', 'church_branch', 'organizer')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'category', 'church_branch', 'department', 'event_type',
        'status', 'is_public', 'is_featured', 'is_online'
    ]
    search_fields = ['title', 'description', 'location', 'tags']
    ordering_fields = ['start_datetime', 'created_at', 'title']
    ordering = ['start_datetime']
    
    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'POST':
            return EventCreateUpdateSerializer
        return EventListSerializer
    
    def get_permissions(self):
        """Public can view published events, admins can create"""
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAnyAdmin()]
        if self.request.GET.get('status') == 'published':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filter events based on user and query params"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(start_datetime__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_datetime__lte=end_date)
        
        # Filter upcoming/past events
        time_filter = self.request.query_params.get('time_filter')
        now = timezone.now()
        
        if time_filter == 'upcoming':
            queryset = queryset.filter(start_datetime__gt=now)
        elif time_filter == 'past':
            queryset = queryset.filter(end_datetime__lt=now)
        elif time_filter == 'ongoing':
            queryset = queryset.filter(start_datetime__lte=now, end_datetime__gte=now)
        
        # Public users see only published public events
        if not user.is_authenticated:
            return queryset.filter(status=Event.EventStatus.PUBLISHED, is_public=True)
        
        # Super admin sees all
        if user.is_super_admin():
            return queryset
        
        # Denomination admin sees their denomination's events
        if user.is_denomination_admin() and user.denomination:
            return queryset.filter(church_branch__denomination=user.denomination)
        
        # Church admin sees their branch events
        if user.is_church_admin() and user.church_branch:
            return queryset.filter(church_branch=user.church_branch)
        
        # Regular members see published events in their branch + public events
        if user.church_branch:
            return queryset.filter(
                Q(church_branch=user.church_branch, status=Event.EventStatus.PUBLISHED) |
                Q(is_public=True, status=Event.EventStatus.PUBLISHED)
            )
        
        # Default: published public events
        return queryset.filter(status=Event.EventStatus.PUBLISHED, is_public=True)
    
    def create(self, request, *args, **kwargs):
        """Create new event"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        
        # Return full details
        response_serializer = EventDetailSerializer(event, context={'request': request})
        
        return Response({
            'success': True,
            'message': 'Event created successfully!',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        """List events"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })


class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update or delete an event
    GET/PUT/PATCH/DELETE /api/events/<id>/
    """
    queryset = Event.objects.select_related('category', 'church_branch', 'organizer')
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Use different serializers for different methods"""
        if self.request.method in ['PUT', 'PATCH']:
            return EventCreateUpdateSerializer
        return EventDetailSerializer
    
    def get_permissions(self):
        """Public can view, admins can modify"""
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsAnyAdmin()]
    
    def retrieve(self, request, *args, **kwargs):
        """Get event details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'request': request})
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """Update event"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return full details
        response_serializer = EventDetailSerializer(instance, context={'request': request})
        
        return Response({
            'success': True,
            'message': 'Event updated successfully!',
            'data': response_serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Cancel/delete event"""
        instance = self.get_object()
        
        # Soft delete - mark as cancelled
        instance.status = Event.EventStatus.CANCELLED
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Event cancelled successfully!'
        })


# ==================== RSVP VIEWS ====================

class RSVPListCreateView(generics.ListCreateAPIView):
    """
    List RSVPs or create a new one
    GET/POST /api/events/rsvps/
    """
    queryset = RSVP.objects.select_related('user', 'event')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['event', 'status']
    search_fields = ['user__first_name', 'user__last_name']
    
    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'POST':
            return RSVPCreateUpdateSerializer
        return RSVPSerializer
    
    def get_queryset(self):
        """Filter RSVPs based on user"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Admins see all RSVPs
        if user.is_admin():
            if user.church_branch:
                return queryset.filter(event__church_branch=user.church_branch)
            return queryset
        
        # Regular users see only their own RSVPs
        return queryset.filter(user=user)
    
    def create(self, request, *args, **kwargs):
        """Create RSVP"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        rsvp = serializer.save()
        
        # Return full details
        response_serializer = RSVPSerializer(rsvp)
        
        return Response({
            'success': True,
            'message': 'RSVP created successfully!',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        """List RSVPs"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })


class RSVPDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update or delete an RSVP
    GET/PUT/PATCH/DELETE /api/events/rsvps/<id>/
    """
    queryset = RSVP.objects.select_related('user', 'event')
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Use different serializers for different methods"""
        if self.request.method in ['PUT', 'PATCH']:
            return RSVPCreateUpdateSerializer
        return RSVPSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Remove event from update data (can't change event)
        data = request.data.copy()
        data.pop('event', None)
        
        serializer = self.get_serializer(instance, data=data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return full details
        response_serializer = RSVPSerializer(instance)
        
        return Response({
            'success': True,
            'message': 'RSVP updated successfully!',
            'data': response_serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        
        return Response({
            'success': True,
            'message': 'RSVP deleted successfully!'
        })


class EventRSVPListView(generics.ListAPIView):
    """
    List all RSVPs for a specific event
    GET /api/events/<event_id>/rsvps/
    """
    serializer_class = RSVPSerializer
    permission_classes = [IsAuthenticated, IsAnyAdmin]
    
    def get_queryset(self):
        event_id = self.kwargs.get('event_id')
        return RSVP.objects.filter(event_id=event_id).select_related('user', 'event')
    
    def list(self, request, event_id):
        """List RSVPs for event"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Calculate statistics
        total = queryset.count()
        going = queryset.filter(status=RSVP.RSVPStatus.GOING).count()
        not_going = queryset.filter(status=RSVP.RSVPStatus.NOT_GOING).count()
        maybe = queryset.filter(status=RSVP.RSVPStatus.MAYBE).count()
        
        return Response({
            'success': True,
            'statistics': {
                'total': total,
                'going': going,
                'not_going': not_going,
                'maybe': maybe
            },
            'data': serializer.data
        })


# ==================== ATTENDANCE VIEWS ====================

class EventAttendanceListCreateView(generics.ListCreateAPIView):
    """
    List event attendance or create new record
    GET/POST /api/events/attendance/
    """
    queryset = EventAttendance.objects.select_related('user', 'event', 'recorded_by')
    serializer_class = EventAttendanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['event', 'checked_in', 'check_in_method']
    search_fields = ['user__first_name', 'user__last_name']
    
    def get_queryset(self):
        """Filter attendance based on user"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Admins see all attendance
        if user.is_admin():
            if user.church_branch:
                return queryset.filter(event__church_branch=user.church_branch)
            return queryset
        
        # Regular users see only their own attendance
        return queryset.filter(user=user)
    
    def get_permissions(self):
        """Anyone can view, admins can create"""
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAnyAdmin()]
        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        """Create attendance record"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Attendance recorded successfully!',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        """List attendance records"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })


class EventAttendanceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update or delete attendance record
    GET/PUT/PATCH/DELETE /api/events/attendance/<id>/
    """
    queryset = EventAttendance.objects.select_related('user', 'event')
    serializer_class = EventAttendanceSerializer
    permission_classes = [IsAuthenticated, IsAnyAdmin]
    lookup_field = 'id'
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Attendance updated successfully!',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        
        return Response({
            'success': True,
            'message': 'Attendance record deleted successfully!'
        })


class CheckInView(APIView):
    """
    Quick check-in endpoint
    POST /api/events/<event_id>/check-in/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, event_id):
        """Check in to an event"""
        user = request.user
        
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Event not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create or update attendance
        attendance, created = EventAttendance.objects.update_or_create(
            event=event,
            user=user,
            defaults={
                'checked_in': True,
                'check_in_time': timezone.now(),
                'check_in_method': request.data.get('method', 'manual'),
                'recorded_by': request.user
            }
        )
        
        serializer = EventAttendanceSerializer(attendance)
        
        message = 'Checked in successfully!' if created else 'Check-in updated!'
        
        return Response({
            'success': True,
            'message': message,
            'data': serializer.data
        })


# ==================== STATISTICS VIEWS ====================

class EventStatisticsView(APIView):
    """
    Get event statistics
    GET /api/events/statistics/
    """
    permission_classes = [IsAuthenticated, IsAnyAdmin]
    
    def get(self, request):
        """Calculate event statistics"""
        user = request.user
        
        # Filter based on user role
        if user.is_super_admin():
            events = Event.objects.all()
        elif user.is_denomination_admin() and user.denomination:
            events = Event.objects.filter(church_branch__denomination=user.denomination)
        elif user.church_branch:
            events = Event.objects.filter(church_branch=user.church_branch)
        else:
            events = Event.objects.none()
        
        now = timezone.now()
        
        stats = {
            'total_events': events.count(),
            'upcoming_events': events.filter(start_datetime__gt=now).count(),
            'past_events': events.filter(end_datetime__lt=now).count(),
            'ongoing_events': events.filter(start_datetime__lte=now, end_datetime__gte=now).count(),
            'total_rsvps': RSVP.objects.filter(event__in=events).count(),
            'total_attendances': EventAttendance.objects.filter(event__in=events, checked_in=True).count(),
            'events_by_category': dict(
                events.values('category__name').annotate(count=Count('id')).values_list('category__name', 'count')
            ),
            'events_by_status': dict(
                events.values('status').annotate(count=Count('id')).values_list('status', 'count')
            ),
            'average_attendance_rate': 0.0,  # Calculate based on RSVPs vs actual attendance
        }
        
        serializer = EventStatisticsSerializer(stats)
        
        return Response({
            'success': True,
            'data': serializer.data
        })