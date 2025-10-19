"""
Class-Based Views for Member Management
"""

from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Avg
from datetime import date, timedelta

from .models import (
    MembershipType,
    Member,
    Attendance,
    MemberNote,
    MemberDepartment
)
from .serializers import (
    MembershipTypeSerializer,
    MemberListSerializer,
    MemberDetailSerializer,
    MemberCreateUpdateSerializer,
    AttendanceSerializer,
    AttendanceCreateBulkSerializer,
    MemberNoteSerializer,
    MemberDepartmentSerializer,
    MemberStatisticsSerializer
)
from authentication.permissions import IsAnyAdmin, IsOwnerOrAdmin


# ==================== MEMBERSHIP TYPE VIEWS ====================

class MembershipTypeListCreateView(generics.ListCreateAPIView):
    """
    List membership types or create a new one
    GET/POST /api/members/membership-types/
    """
    queryset = MembershipType.objects.filter(is_active=True)
    serializer_class = MembershipTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['church_branch']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        """Filter by user's church or show all for admins"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_super_admin():
            return queryset
        
        if user.church_branch:
            return queryset.filter(church_branch=user.church_branch)
        
        return queryset.none()
    
    def create(self, request, *args, **kwargs):
        """Create membership type"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Membership type created successfully!',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class MembershipTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update or delete a membership type
    GET/PUT/PATCH/DELETE /api/members/membership-types/<id>/
    """
    queryset = MembershipType.objects.all()
    serializer_class = MembershipTypeSerializer
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
            'message': 'Membership type updated successfully!',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Membership type deactivated successfully!'
        })


# ==================== MEMBER VIEWS ====================

class MemberListCreateView(generics.ListCreateAPIView):
    """
    List all members or create a new member
    GET/POST /api/members/
    """
    queryset = Member.objects.select_related('user', 'membership_type').filter(
        status=Member.MemberStatus.ACTIVE
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'membership_type', 'marital_status']
    search_fields = [
        'user__first_name', 'user__last_name', 'user__email',
        'membership_number', 'occupation'
    ]
    ordering_fields = ['joined_date', 'created_at', 'membership_number']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'POST':
            return MemberCreateUpdateSerializer
        return MemberListSerializer
    
    def get_queryset(self):
        """Filter members based on user role"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Super admin sees all
        if user.is_super_admin():
            return Member.objects.select_related('user', 'membership_type').all()
        
        # Denomination admin sees their denomination's members
        if user.is_denomination_admin() and user.denomination:
            return queryset.filter(user__denomination=user.denomination)
        
        # Church admin sees their branch members
        if user.is_church_admin() and user.church_branch:
            return queryset.filter(user__church_branch=user.church_branch)
        
        # Regular members see only active members in their branch
        if user.church_branch:
            return queryset.filter(user__church_branch=user.church_branch)
        
        return queryset.none()
    
    def create(self, request, *args, **kwargs):
        """Create new member"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = serializer.save()
        
        # Set approval info if user is admin
        if request.user.is_admin():
            member.membership_approved_by = request.user
            member.membership_approved_date = date.today()
            member.save()
        
        # Return full details
        response_serializer = MemberDetailSerializer(member)
        
        return Response({
            'success': True,
            'message': 'Member created successfully!',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        """List members"""
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


class MemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update or delete a member
    GET/PUT/PATCH/DELETE /api/members/<id>/
    """
    queryset = Member.objects.select_related('user', 'membership_type')
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Use different serializers for different methods"""
        if self.request.method in ['PUT', 'PATCH']:
            return MemberCreateUpdateSerializer
        return MemberDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Get member details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """Update member"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Remove user_id from update data
        data = request.data.copy()
        data.pop('user_id', None)
        
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return full details
        response_serializer = MemberDetailSerializer(instance)
        
        return Response({
            'success': True,
            'message': 'Member updated successfully!',
            'data': response_serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Deactivate member"""
        instance = self.get_object()
        instance.status = Member.MemberStatus.INACTIVE
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Member deactivated successfully!'
        })


# ==================== ATTENDANCE VIEWS ====================

class AttendanceListCreateView(generics.ListCreateAPIView):
    """
    List attendance records or create new one
    GET/POST /api/members/attendance/
    """
    queryset = Attendance.objects.select_related('member__user', 'church_branch')
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['member', 'church_branch', 'status', 'date', 'event_name']
    search_fields = ['member__user__first_name', 'member__user__last_name', 'event_name']
    ordering_fields = ['date', 'check_in_time']
    ordering = ['-date', '-check_in_time']
    
    def get_queryset(self):
        """Filter attendance based on user role"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Super admin sees all
        if user.is_super_admin():
            return queryset
        
        # Denomination admin sees their denomination
        if user.is_denomination_admin() and user.denomination:
            return queryset.filter(church_branch__denomination=user.denomination)
        
        # Church admin sees their branch
        if user.is_church_admin() and user.church_branch:
            return queryset.filter(church_branch=user.church_branch)
        
        # Regular members see only their own attendance
        if hasattr(user, 'member_profile'):
            return queryset.filter(member=user.member_profile)
        
        return queryset.none()
    
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


class AttendanceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update or delete attendance record
    GET/PUT/PATCH/DELETE /api/members/attendance/<id>/
    """
    queryset = Attendance.objects.select_related('member__user', 'church_branch')
    serializer_class = AttendanceSerializer
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


class AttendanceBulkCreateView(APIView):
    """
    Create multiple attendance records at once
    POST /api/members/attendance/bulk/
    """
    permission_classes = [IsAuthenticated, IsAnyAdmin]
    
    def post(self, request):
        """Bulk create attendance"""
        serializer = AttendanceCreateBulkSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        created = serializer.save()
        
        return Response({
            'success': True,
            'message': f'{len(created)} attendance records created successfully!',
            'count': len(created)
        }, status=status.HTTP_201_CREATED)


class MemberAttendanceHistoryView(generics.ListAPIView):
    """
    Get attendance history for a specific member
    GET /api/members/<member_id>/attendance/
    """
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        member_id = self.kwargs.get('member_id')
        return Attendance.objects.filter(member_id=member_id).order_by('-date')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Calculate statistics
        total = queryset.count()
        present = queryset.filter(status=Attendance.AttendanceStatus.PRESENT).count()
        rate = round((present / total * 100), 2) if total > 0 else 0
        
        return Response({
            'success': True,
            'statistics': {
                'total_records': total,
                'present': present,
                'attendance_rate': rate
            },
            'data': serializer.data
        })


# ==================== MEMBER NOTES VIEWS ====================

class MemberNoteListCreateView(generics.ListCreateAPIView):
    """
    List or create member notes
    GET/POST /api/members/<member_id>/notes/
    """
    serializer_class = MemberNoteSerializer
    permission_classes = [IsAuthenticated, IsAnyAdmin]
    
    def get_queryset(self):
        member_id = self.kwargs.get('member_id')
        return MemberNote.objects.filter(member_id=member_id).order_by('-created_at')
    
    def create(self, request, member_id):
        """Create member note"""
        data = request.data.copy()
        data['member'] = member_id
        
        serializer = self.get_serializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Note created successfully!',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, member_id):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })


class MemberNoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update or delete a member note
    GET/PUT/PATCH/DELETE /api/members/<member_id>/notes/<id>/
    """
    serializer_class = MemberNoteSerializer
    permission_classes = [IsAuthenticated, IsAnyAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        member_id = self.kwargs.get('member_id')
        return MemberNote.objects.filter(member_id=member_id)
    
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
            'message': 'Note updated successfully!',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        
        return Response({
            'success': True,
            'message': 'Note deleted successfully!'
        })


# ==================== MEMBER DEPARTMENTS VIEWS ====================

class MemberDepartmentListView(generics.ListAPIView):
    """
    List departments for a member
    GET /api/members/<member_id>/departments/
    """
    serializer_class = MemberDepartmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        member_id = self.kwargs.get('member_id')
        return MemberDepartment.objects.filter(
            member_id=member_id,
            is_active=True
        ).select_related('department')
    
    def list(self, request, member_id):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })


# ==================== STATISTICS VIEWS ====================

class MemberStatisticsView(APIView):
    """
    Get member statistics
    GET /api/members/statistics/
    """
    permission_classes = [IsAuthenticated, IsAnyAdmin]
    
    def get(self, request):
        """Calculate member statistics"""
        user = request.user
        
        # Filter based on user role
        if user.is_super_admin():
            members = Member.objects.all()
        elif user.is_denomination_admin() and user.denomination:
            members = Member.objects.filter(user__denomination=user.denomination)
        elif user.church_branch:
            members = Member.objects.filter(user__church_branch=user.church_branch)
        else:
            members = Member.objects.none()
        
        # Calculate statistics
        today = date.today()
        first_day_month = today.replace(day=1)
        first_day_year = today.replace(month=1, day=1)
        
        stats = {
            'total_members': members.count(),
            'active_members': members.filter(status=Member.MemberStatus.ACTIVE).count(),
            'inactive_members': members.filter(status=Member.MemberStatus.INACTIVE).count(),
            'new_members_this_month': members.filter(created_at__gte=first_day_month).count(),
            'new_members_this_year': members.filter(created_at__gte=first_day_year).count(),
            'members_by_status': dict(
                members.values('status').annotate(count=Count('id')).values_list('status', 'count')
            ),
            'members_by_gender': dict(
                members.values('user__profile__gender').annotate(count=Count('id')).values_list('user__profile__gender', 'count')
            ),
            'members_by_marital_status': dict(
                members.values('marital_status').annotate(count=Count('id')).values_list('marital_status', 'count')
            ),
            'average_age': 0.0,  # Calculate if date_of_birth available
            'attendance_rate': 0.0,  # Calculate from recent attendance
        }
        
        serializer = MemberStatisticsSerializer(stats)
        
        return Response({
            'success': True,
            'data': serializer.data
        })