"""
Class-Based Views for Denomination and Church Branch Management
"""

from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import Denomination, ChurchBranch, BranchDepartment
from .serializers import (
    DenominationSerializer,
    DenominationListSerializer,
    DenominationCreateUpdateSerializer,
    ChurchBranchSerializer,
    ChurchBranchListSerializer,
    ChurchBranchCreateUpdateSerializer,
    BranchDepartmentSerializer
)

from authentication.permissions import IsSuperAdmin, IsAnyAdmin


# ==================== DENOMINATION VIEWS ====================

class DenominationListCreateView(generics.ListCreateAPIView):
    """
    List all denominations or create a new one
    GET /api/denominations/
    POST /api/denominations/
    """
    queryset = Denomination.objects.filter(status=Denomination.Status.ACTIVE)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'headquarters']
    ordering_fields = ['name', 'created_at', 'total_branches']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'POST':
            return DenominationCreateUpdateSerializer
        return DenominationListSerializer
    
    def get_permissions(self):
        """Anyone can view, only super admin can create"""
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsSuperAdmin()]
        return [AllowAny()]
    
    def create(self, request, *args, **kwargs):
        """Create a new denomination"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        denomination = serializer.save(created_by=request.user)
        
        # Return full details
        response_serializer = DenominationSerializer(denomination)
        
        return Response({
            'success': True,
            'message': 'Denomination created successfully!',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        """List all denominations"""
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
        }, status=status.HTTP_200_OK)


class DenominationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a denomination
    GET /api/denominations/<id>/
    PUT/PATCH /api/denominations/<id>/
    DELETE /api/denominations/<id>/
    """
    queryset = Denomination.objects.all()
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Use different serializers for different methods"""
        if self.request.method in ['PUT', 'PATCH']:
            return DenominationCreateUpdateSerializer
        return DenominationSerializer
    
    def get_permissions(self):
        """Anyone can view, only super admin can modify"""
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsSuperAdmin()]
    
    def retrieve(self, request, *args, **kwargs):
        """Get denomination details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """Update denomination"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return full details
        response_serializer = DenominationSerializer(instance)
        
        return Response({
            'success': True,
            'message': 'Denomination updated successfully!',
            'data': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        """Delete/deactivate denomination"""
        instance = self.get_object()
        
        # Soft delete - just deactivate
        instance.status = Denomination.Status.INACTIVE
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Denomination deactivated successfully!'
        }, status=status.HTTP_200_OK)


# ==================== CHURCH BRANCH VIEWS ====================

class ChurchBranchListCreateView(generics.ListCreateAPIView):
    """
    List all church branches or create a new one
    GET /api/churches/
    POST /api/churches/
    """
    queryset = ChurchBranch.objects.filter(status=ChurchBranch.Status.ACTIVE)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['denomination', 'city', 'state', 'country', 'status']
    search_fields = ['name', 'description', 'address', 'city']
    ordering_fields = ['name', 'created_at', 'city']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'POST':
            return ChurchBranchCreateUpdateSerializer
        return ChurchBranchListSerializer
    
    def get_permissions(self):
        """Anyone can view, authenticated users can create"""
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAnyAdmin()]
        return [AllowAny()]
    
    def get_queryset(self):
        """Filter branches based on user role"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # If not authenticated, return all active branches
        if not user.is_authenticated:
            return queryset
        
        # Super admin sees everything
        if user.is_super_admin():
            return ChurchBranch.objects.all()
        
        # Denomination admin sees their denomination's branches
        if user.is_denomination_admin() and user.denomination:
            return queryset.filter(denomination=user.denomination)
        
        # Church admin sees their branch
        if user.is_church_admin() and user.church_branch:
            return queryset.filter(id=user.church_branch.id)
        
        # Regular users see all active branches
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new church branch"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        branch = serializer.save()
        
        # Return full details
        response_serializer = ChurchBranchSerializer(branch)
        
        return Response({
            'success': True,
            'message': 'Church branch created successfully!',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        """List all church branches"""
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
        }, status=status.HTTP_200_OK)


class ChurchBranchDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a church branch
    GET /api/churches/<id>/
    PUT/PATCH /api/churches/<id>/
    DELETE /api/churches/<id>/
    """
    queryset = ChurchBranch.objects.all()
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Use different serializers for different methods"""
        if self.request.method in ['PUT', 'PATCH']:
            return ChurchBranchCreateUpdateSerializer
        return ChurchBranchSerializer
    
    def get_permissions(self):
        """Anyone can view, admins can modify"""
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsAnyAdmin()]
    
    def retrieve(self, request, *args, **kwargs):
        """Get church branch details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """Update church branch"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return full details
        response_serializer = ChurchBranchSerializer(instance)
        
        return Response({
            'success': True,
            'message': 'Church branch updated successfully!',
            'data': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        """Delete/deactivate church branch"""
        instance = self.get_object()
        
        # Soft delete - just deactivate
        instance.status = ChurchBranch.Status.INACTIVE
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Church branch deactivated successfully!'
        }, status=status.HTTP_200_OK)


class ChurchBranchMembersView(generics.ListAPIView):
    """
    List all members of a specific church branch
    GET /api/churches/<id>/members/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id):
        """Get members of a church branch"""
        try:
            branch = ChurchBranch.objects.get(id=id)
        except ChurchBranch.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Church branch not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all users in this branch
        from  authentication.serializers import UserSerializer
        members = branch.users.filter(is_active=True)
        serializer = UserSerializer(members, many=True)
        
        return Response({
            'success': True,
            'count': members.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


# ==================== DEPARTMENT VIEWS ====================

class DepartmentListCreateView(generics.ListCreateAPIView):
    """
    List departments in a branch or create a new one
    GET /api/churches/<branch_id>/departments/
    POST /api/churches/<branch_id>/departments/
    """
    serializer_class = BranchDepartmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get departments for specific branch"""
        branch_id = self.kwargs.get('branch_id')
        return BranchDepartment.objects.filter(
            branch_id=branch_id,
            is_active=True
        )
    
    def create(self, request, branch_id):
        """Create a new department"""
        try:
            branch = ChurchBranch.objects.get(id=branch_id)
        except ChurchBranch.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Church branch not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check permission - must be admin of this branch or higher
        user = request.user
        if not (user.is_super_admin() or 
                (user.is_denomination_admin() and user.denomination == branch.denomination) or
                (user.is_church_admin() and user.church_branch == branch)):
            return Response({
                'success': False,
                'message': 'You do not have permission to create departments in this branch'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        department = serializer.save(branch=branch)
        
        return Response({
            'success': True,
            'message': 'Department created successfully!',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, branch_id):
        """List all departments"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a department
    GET /api/churches/<branch_id>/departments/<id>/
    PUT/PATCH /api/churches/<branch_id>/departments/<id>/
    DELETE /api/churches/<branch_id>/departments/<id>/
    """
    serializer_class = BranchDepartmentSerializer
    permission_classes = [IsAuthenticated, IsAnyAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Get departments for specific branch"""
        branch_id = self.kwargs.get('branch_id')
        return BranchDepartment.objects.filter(branch_id=branch_id)
    
    def retrieve(self, request, *args, **kwargs):
        """Get department details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """Update department"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Department updated successfully!',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        """Delete department"""
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Department deactivated successfully!'
        }, status=status.HTTP_200_OK)


# ==================== STATISTICS VIEWS ====================

class DenominationStatsView(APIView):
    """
    Get statistics for a denomination
    GET /api/denominations/<id>/stats/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id):
        """Get denomination statistics"""
        try:
            denomination = Denomination.objects.get(id=id)
        except Denomination.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Denomination not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate statistics
        branches = denomination.branches.filter(status=ChurchBranch.Status.ACTIVE)
        total_members = denomination.users.filter(is_active=True).count()
        
        # Branch statistics by location
        branches_by_state = {}
        for branch in branches:
            state = branch.state
            if state not in branches_by_state:
                branches_by_state[state] = 0
            branches_by_state[state] += 1
        
        stats = {
            'total_branches': branches.count(),
            'total_members': total_members,
            'active_branches': branches.filter(status=ChurchBranch.Status.ACTIVE).count(),
            'branches_by_state': branches_by_state,
            'total_admins': denomination.users.filter(
                role__in=['denomination_admin', 'church_admin']
            ).count(),
        }
        
        return Response({
            'success': True,
            'data': stats
        }, status=status.HTTP_200_OK)


class ChurchBranchStatsView(APIView):
    """
    Get statistics for a church branch
    GET /api/churches/<id>/stats/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id):
        """Get church branch statistics"""
        try:
            branch = ChurchBranch.objects.get(id=id)
        except ChurchBranch.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Church branch not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate statistics
        total_members = branch.users.filter(is_active=True).count()
        departments = branch.departments.filter(is_active=True)
        
        stats = {
            'total_members': total_members,
            'total_departments': departments.count(),
            'seating_capacity': branch.seating_capacity,
            'capacity_utilization': round(
                (total_members / branch.seating_capacity * 100) if branch.seating_capacity else 0,
                2
            ),
            'has_coordinates': bool(branch.latitude and branch.longitude),
        }
        
        return Response({
            'success': True,
            'data': stats
        }, status=status.HTTP_200_OK)