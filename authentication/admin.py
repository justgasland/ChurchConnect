"""
Django Admin Configuration for User and Profile Management
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin for custom User model"""

    list_display = [
        'email', 'full_name_display', 'role', 'is_verified',
        'is_active', 'date_joined_display', 'profile_preview'
    ]
    list_filter = ['role', 'is_active', 'is_verified', 'created_at']
    search_fields = ['email', 'first_name', 'last_name', 'username', 'phone_number']
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    ordering = ['-created_at']

    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_image')
        }),
        ('Account Details', {
            'fields': ('username', 'role', 'is_active', 'is_verified')
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )

    def full_name_display(self, obj):
        """Display full name"""
        return obj.get_full_name()
    full_name_display.short_description = 'Full Name'

    def profile_preview(self, obj):
        """Display small profile image preview"""
        if obj.profile_image:
            return format_html('<img src="{}" width="35" height="35" style="border-radius:50%;" />', obj.profile_image.url)
        return '-'
    profile_preview.short_description = 'Profile'

    def date_joined_display(self, obj):
        """Display created date in readable format"""
        return obj.created_at.strftime("%b %d, %Y")
    date_joined_display.short_description = 'Joined'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model"""

    list_display = [
        'user_display', 'gender', 'city', 'state', 'department',
        'age', 'created_at_display'
    ]
    list_filter = ['gender', 'state', 'department', 'country']
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'city', 'state', 'department'
    ]
    readonly_fields = ['age', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'gender', 'date_of_birth', 'age', 'bio')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'country')
        }),
        ('Church Info', {
            'fields': ('department', 'joined_date')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def user_display(self, obj):
        """Display user’s full name or email"""
        return obj.user.get_full_name() or obj.user.email
    user_display.short_description = 'User'

    def created_at_display(self, obj):
        """Readable created date"""
        return obj.created_at.strftime("%b %d, %Y")
    created_at_display.short_description = 'Created'



