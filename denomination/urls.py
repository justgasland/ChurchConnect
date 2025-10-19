"""
URL Configuration for Denomination App
"""

from django.urls import path
from .views import (
    DenominationListCreateView,
    DenominationDetailView,
    DenominationStatsView,
    ChurchBranchListCreateView,
    ChurchBranchDetailView,
    ChurchBranchMembersView,
    ChurchBranchStatsView,
    DepartmentListCreateView,
    DepartmentDetailView,
)

app_name = 'denomination'

urlpatterns = [
    # Denomination endpoints
    path('', DenominationListCreateView.as_view(), name='denomination_list_create'),
    path('<int:id>/', DenominationDetailView.as_view(), name='denomination_detail'),
    path('<int:id>/stats/', DenominationStatsView.as_view(), name='denomination_stats'),
    
    # Church Branch endpoints
    path('churches/', ChurchBranchListCreateView.as_view(), name='church_list_create'),
    path('churches/<int:id>/', ChurchBranchDetailView.as_view(), name='church_detail'),
    path('churches/<int:id>/members/', ChurchBranchMembersView.as_view(), name='church_members'),
    path('churches/<int:id>/stats/', ChurchBranchStatsView.as_view(), name='church_stats'),
    
    # Department endpoints
    path('churches/<int:branch_id>/departments/', DepartmentListCreateView.as_view(), name='department_list_create'),
    path('churches/<int:branch_id>/departments/<int:id>/', DepartmentDetailView.as_view(), name='department_detail'),
]