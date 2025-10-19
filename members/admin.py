"""
Django Admin Configuration for Member Management
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    MembershipType,
    Member,
    Attendance,
    MemberNote,
    MemberDepartment
)


@admin.register(MembershipType)
class MembershipTypeAdmin(admin.ModelAdmin):
    """Admin for MembershipType model"""
    
    list_display = [
        'name', 'church_branch', 'can_vote', 'can_hold_office',
        'is_active', 'member_count', 'created_at'
    ]
    list_filter = ['is_active', 'can_vote', 'can_hold_office', 'church_branch']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('church_branch', 'name', 'description')
        }),
        ('Privileges', {
            'fields': ('can_vote', 'can_hold_office')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def member_count(self, obj):
        """Get member count"""
        from django.db.models import Count
        count = obj.members.filter(status=Member.MemberStatus.ACTIVE).count()
        return count
    member_count.short_description = 'Members'


class MemberDepartmentInline(admin.TabularInline):
    """Inline admin for member departments"""
    model = MemberDepartment
    extra = 0
    fields = ['department', 'role', 'is_active', 'joined_date']
    raw_id_fields = ['department']


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """Admin for Member model"""
    
    list_display = [
        'membership_number', 'user_full_name', 'status',
        'membership_type', 'joined_date', 'age', 'years_of_membership'
    ]
    list_filter = [
        'status', 'membership_type', 'marital_status',
        'joined_date', 'created_at'
    ]
    search_fields = [
        'user__first_name', 'user__last_name', 'user__email',
        'membership_number', 'occupation'
    ]
    readonly_fields = [
        'membership_number', 'age', 'years_of_membership',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['user', 'membership_approved_by']
    date_hierarchy = 'joined_date'
    inlines = [MemberDepartmentInline]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Membership Information', {
            'fields': (
                'membership_number', 'membership_type', 'status',
                'joined_date', 'membership_approved_date',
                'membership_approved_by', 'years_of_membership'
            )
        }),
        ('Personal Details', {
            'fields': (
                'marital_status', 'occupation', 'employer',
                'spouse_name', 'anniversary_date', 'number_of_children',
                'age'
            )
        }),
        ('Church Information', {
            'fields': (
                'baptism_date', 'baptism_location', 'confirmation_date',
                'previous_church', 'transfer_letter'
            )
        }),
        ('Skills & Interests', {
            'fields': ('skills', 'interests')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def user_full_name(self, obj):
        """Display user's full name"""
        return obj.user.get_full_name()
    user_full_name.short_description = 'Full Name'
    user_full_name.admin_order_field = 'user__first_name'
    
    def get_queryset(self, request):
        """Optimize query"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'membership_type', 'membership_approved_by')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Admin for Attendance model"""
    
    list_display = [
        'member_name', 'event_name', 'date', 'status',
        'check_in_time', 'duration_display', 'recorded_by_name'
    ]
    list_filter = [
        'status', 'date', 'event_name', 'church_branch'
    ]
    search_fields = [
        'member__user__first_name', 'member__user__last_name',
        'event_name'
    ]
    date_hierarchy = 'date'
    readonly_fields = ['duration', 'created_at', 'updated_at']
    raw_id_fields = ['member', 'recorded_by']
    
    fieldsets = (
        ('Attendance Information', {
            'fields': ('member', 'church_branch', 'event_name', 'date', 'status')
        }),
        ('Time Tracking', {
            'fields': ('check_in_time', 'check_out_time', 'duration')
        }),
        ('Additional Information', {
            'fields': ('notes', 'recorded_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def member_name(self, obj):
        """Display member name"""
        return obj.member.user.get_full_name()
    member_name.short_description = 'Member'
    member_name.admin_order_field = 'member__user__first_name'
    
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
        return qs.select_related('member__user', 'church_branch', 'recorded_by')


@admin.register(MemberNote)
class MemberNoteAdmin(admin.ModelAdmin):
    """Admin for MemberNote model"""
    
    list_display = [
        'title', 'member_name', 'is_confidential',
        'created_by_name', 'created_at'
    ]
    list_filter = ['is_confidential', 'created_at']
    search_fields = [
        'title', 'content', 'member__user__first_name',
        'member__user__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['member', 'created_by']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Note Information', {
            'fields': ('member', 'title', 'content', 'is_confidential')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    
    def member_name(self, obj):
        """Display member name"""
        return obj.member.user.get_full_name()
    member_name.short_description = 'Member'
    
    def created_by_name(self, obj):
        """Display creator name"""
        return obj.created_by.get_full_name() if obj.created_by else '-'
    created_by_name.short_description = 'Created By'
    
    def get_queryset(self, request):
        """Optimize query"""
        qs = super().get_queryset(request)
        return qs.select_related('member__user', 'created_by')


@admin.register(MemberDepartment)
class MemberDepartmentAdmin(admin.ModelAdmin):
    """Admin for MemberDepartment model"""
    
    list_display = [
        'member_name', 'department_name', 'role',
        'is_active', 'joined_date'
    ]
    list_filter = ['is_active', 'department', 'joined_date']
    search_fields = [
        'member__user__first_name', 'member__user__last_name',
        'department__name', 'role'
    ]
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['member', 'department']
    date_hierarchy = 'joined_date'
    
    fieldsets = (
        ('Assignment Information', {
            'fields': ('member', 'department', 'role', 'is_active')
        }),
        ('Dates', {
            'fields': ('joined_date', 'left_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def member_name(self, obj):
        """Display member name"""
        return obj.member.user.get_full_name()
    member_name.short_description = 'Member'
    
    def department_name(self, obj):
        """Display department name"""
        return obj.department.name
    department_name.short_description = 'Department'
    
    def get_queryset(self, request):
        """Optimize query"""
        qs = super().get_queryset(request)
        return qs.select_related('member__user', 'department')