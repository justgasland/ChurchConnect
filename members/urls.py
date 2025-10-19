"""
URL Configuration for Members App
"""

from django.urls import path
from .views import (
    MembershipTypeListCreateView,
    MembershipTypeDetailView,
    MemberListCreateView,
    MemberDetailView,
    AttendanceListCreateView,
    AttendanceDetailView,
    AttendanceBulkCreateView,
    MemberAttendanceHistoryView,
    MemberNoteListCreateView,
    MemberNoteDetailView,
    MemberDepartmentListView,
    MemberStatisticsView,
)

app_name = 'members'

urlpatterns = [
    # Membership Types
    path('membership-types/', MembershipTypeListCreateView.as_view(), name='membership_type_list_create'),
    path('membership-types/<int:id>/', MembershipTypeDetailView.as_view(), name='membership_type_detail'),
    
    # Members
    path('', MemberListCreateView.as_view(), name='member_list_create'),
    path('<int:id>/', MemberDetailView.as_view(), name='member_detail'),
    path('statistics/', MemberStatisticsView.as_view(), name='member_statistics'),
    
    # Attendance
    path('attendance/', AttendanceListCreateView.as_view(), name='attendance_list_create'),
    path('attendance/<int:id>/', AttendanceDetailView.as_view(), name='attendance_detail'),
    path('attendance/bulk/', AttendanceBulkCreateView.as_view(), name='attendance_bulk_create'),
    path('<int:member_id>/attendance/', MemberAttendanceHistoryView.as_view(), name='member_attendance_history'),
    
    # Member Notes
    path('<int:member_id>/notes/', MemberNoteListCreateView.as_view(), name='member_note_list_create'),
    path('<int:member_id>/notes/<int:id>/', MemberNoteDetailView.as_view(), name='member_note_detail'),
    
    # Member Departments
    path('<int:member_id>/departments/', MemberDepartmentListView.as_view(), name='member_department_list'),
]