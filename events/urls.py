"""
URL Configuration for Events App
"""

from django.urls import path
from .views import (
    EventCategoryListCreateView,
    EventCategoryDetailView,
    EventListCreateView,
    EventDetailView,
    RSVPListCreateView,
    RSVPDetailView,
    EventRSVPListView,
    EventAttendanceListCreateView,
    EventAttendanceDetailView,
    CheckInView,
    EventStatisticsView,
)

app_name = 'events'

urlpatterns = [
    # Event Categories
    path('categories/', EventCategoryListCreateView.as_view(), name='category_list_create'),
    path('categories/<int:id>/', EventCategoryDetailView.as_view(), name='category_detail'),
    
    # Events
    path('', EventListCreateView.as_view(), name='event_list_create'),
    path('<int:id>/', EventDetailView.as_view(), name='event_detail'),
    path('statistics/', EventStatisticsView.as_view(), name='event_statistics'),
    
    # RSVPs
    path('rsvps/', RSVPListCreateView.as_view(), name='rsvp_list_create'),
    path('rsvps/<int:id>/', RSVPDetailView.as_view(), name='rsvp_detail'),
    path('<int:event_id>/rsvps/', EventRSVPListView.as_view(), name='event_rsvp_list'),
    
    # Attendance
    path('attendance/', EventAttendanceListCreateView.as_view(), name='attendance_list_create'),
    path('attendance/<int:id>/', EventAttendanceDetailView.as_view(), name='attendance_detail'),
    path('<int:event_id>/check-in/', CheckInView.as_view(), name='event_checkin'),
]