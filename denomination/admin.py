"""
Django Admin Configuration for Denomination Management
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Denomination, ChurchBranch, BranchDepartment


@admin.register(Denomination)
class DenominationAdmin(admin.ModelAdmin):
    """Admin for Denomination model"""
    
    list_display = [
        'name', 'logo_display', 'status', 'total_branches',
        'total_members', 'created_by', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'allow_public_registration']
    search_fields = ['name', 'description', 'headquarters', 'contact_email']
    readonly_fields = ['slug', 'total_branches', 'total_members', 'created_at', 'updated_at']
    prepopulated_fields = {}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'status')
        }),
        ('Branding', {
            'fields': ('logo', 'cover_image')
        }),
        ('Contact Information', {
            'fields': (
                'headquarters', 'contact_email', 'contact_phone', 'website'
            )
        }),
        ('Social Media', {
            'fields': (
                'facebook_url', 'twitter_url', 'instagram_url', 'youtube_url'
            ),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('allow_public_registration',)
        }),
        ('Management', {
            'fields': ('created_by',)
        }),
        ('Statistics', {
            'fields': ('total_branches', 'total_members')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def logo_display(self, obj):
        """Display logo thumbnail"""
        if obj.logo:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius: 5px;" />',
                obj.logo.url
            )
        return '-'
    logo_display.short_description = 'Logo'
    
    def save_model(self, request, obj, form, change):
        """Set created_by on creation"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class BranchDepartmentInline(admin.TabularInline):
    """Inline admin for departments"""
    model = BranchDepartment
    extra = 0
    fields = ['name', 'description', 'head', 'is_active']


@admin.register(ChurchBranch)
class ChurchBranchAdmin(admin.ModelAdmin):
    """Admin for ChurchBranch model"""
    
    list_display = [
        'name', 'denomination', 'city', 'state', 'country',
        'status', 'admin_user', 'total_members', 'created_at'
    ]
    list_filter = ['status', 'denomination', 'state', 'country', 'is_headquarters']
    search_fields = [
        'name', 'description', 'address', 'city',
        'contact_email', 'denomination__name'
    ]
    readonly_fields = ['slug', 'full_address', 'google_maps_url', 'total_members', 'created_at', 'updated_at']
    inlines = [BranchDepartmentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('denomination', 'name', 'slug', 'description', 'image', 'status')
        }),
        ('Location', {
            'fields': (
                'address', 'city', 'state', 'country', 'postal_code',
                'latitude', 'longitude', 'full_address', 'google_maps_url'
            )
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'alternative_phone')
        }),
        ('Management', {
            'fields': ('admin_user',)
        }),
        ('Church Details', {
            'fields': (
                'service_times', 'seating_capacity', 'is_headquarters',
                'established_date'
            )
        }),
        ('Settings', {
            'fields': ('allow_online_giving', 'allow_event_registration')
        }),
        ('Statistics', {
            'fields': ('total_members',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        """Optimize query with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('denomination', 'admin_user')


@admin.register(BranchDepartment)
class BranchDepartmentAdmin(admin.ModelAdmin):
    """Admin for BranchDepartment model"""
    
    list_display = [
        'name', 'branch', 'head', 'is_active', 'member_count', 'created_at'
    ]
    list_filter = ['is_active', 'branch__denomination', 'branch']
    search_fields = ['name', 'description', 'branch__name']
    readonly_fields = ['member_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('branch', 'name', 'description', 'is_active')
        }),
        ('Leadership', {
            'fields': ('head', 'contact_email', 'contact_phone')
        }),
        ('Statistics', {
            'fields': ('member_count',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        """Optimize query with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('branch', 'branch__denomination', 'head')