# community/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Group, GroupMember, Post, Reaction, Comment, ChatMessage


class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 1
    autocomplete_fields = ['user']
    readonly_fields = ['joined_at']
    fields = ['user', 'role', 'joined_at']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'church_branch', 'visibility',
        'member_count', 'created_by', 'created_at'
    ]
    list_filter = ['visibility', 'church_branch__denomination', 'church_branch', 'created_at']
    search_fields = ['name', 'description', 'created_by__email', 'created_by__first_name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [GroupMemberInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'cover_image')
        }),
        (_('Organization'), {
            'fields': ('church_branch', 'created_by')
        }),
        (_('Settings'), {
            'fields': ('visibility',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Restrict to user's church/denomination"""
        qs = super().get_queryset(request)
        user = request.user

        if user.is_super_admin():
            return qs
        if user.is_denomination_admin() and user.denomination:
            return qs.filter(church_branch__denomination=user.denomination)
        if user.church_branch:
            return qs.filter(church_branch=user.church_branch)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit church_branch choices to user's scope"""
        if db_field.name == "church_branch":
            user = request.user
            if user.is_super_admin():
                pass  # show all
            elif user.is_denomination_admin() and user.denomination:
                kwargs["queryset"] = user.denomination.churches.all()
            elif user.church_branch:
                kwargs["queryset"] = type(user.church_branch).objects.filter(id=user.church_branch.id)
            else:
                kwargs["queryset"] = type(user.church_branch).objects.none()
        if db_field.name == "created_by":
            kwargs["initial"] = request.user
            kwargs["disabled"] = True
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'group', 'author', 'created_at']
    list_filter = [
        'group__church_branch__denomination',
        'group__church_branch',
        'group',
        'created_at'
    ]
    search_fields = ['content', 'author__email', 'author__first_name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['author', 'group']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_super_admin():
            return qs
        if user.is_denomination_admin() and user.denomination:
            return qs.filter(group__church_branch__denomination=user.denomination)
        if user.church_branch:
            return qs.filter(group__church_branch=user.church_branch)
        return qs.none()


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ['post', 'user', 'type', 'created_at']
    list_filter = ['type', 'post__group__church_branch']
    readonly_fields = ['created_at']
    raw_id_fields = ['post', 'user']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_super_admin():
            return qs
        if user.is_denomination_admin() and user.denomination:
            return qs.filter(post__group__church_branch__denomination=user.denomination)
        if user.church_branch:
            return qs.filter(post__group__church_branch=user.church_branch)
        return qs.none()


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'user', 'created_at']
    list_filter = ['post__group__church_branch']
    search_fields = ['content', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['post', 'user']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_super_admin():
            return qs
        if user.is_denomination_admin() and user.denomination:
            return qs.filter(post__group__church_branch__denomination=user.denomination)
        if user.church_branch:
            return qs.filter(post__group__church_branch=user.church_branch)
        return qs.none()


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['group', 'sender', 'message_preview', 'created_at']
    list_filter = ['group__church_branch']
    search_fields = ['message', 'sender__email']
    readonly_fields = ['created_at']
    raw_id_fields = ['group', 'sender']

    def message_preview(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = _("Message")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_super_admin():
            return qs
        if user.is_denomination_admin() and user.denomination:
            return qs.filter(group__church_branch__denomination=user.denomination)
        if user.church_branch:
            return qs.filter(group__church_branch=user.church_branch)
        return qs.none()