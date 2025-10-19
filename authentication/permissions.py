"""
Custom Permission Classes for Role-Based Access Control
"""

from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission check for Super Admin role
    """
    message = "You must be a Super Admin to perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_super_admin()
        )


class IsDenominationAdmin(permissions.BasePermission):
    """
    Permission check for Denomination Admin role
    """
    message = "You must be a Denomination Admin to perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_denomination_admin()
        )


class IsChurchAdmin(permissions.BasePermission):
    """
    Permission check for Church Admin role
    """
    message = "You must be a Church Admin to perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_church_admin()
        )


class IsAnyAdmin(permissions.BasePermission):
    """
    Permission check for any admin role
    """
    message = "You must be an Admin to perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin()
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission check: Owner of object or Admin
    """
    message = "You must be the owner or an admin to access this resource."
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.is_admin():
            return True
        
        # Check if object has a 'user' attribute (for profiles, etc.)
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object itself is the user
        return obj == request.user


class IsVerified(permissions.BasePermission):
    """
    Permission check for verified users only
    """
    message = "Your account must be verified to perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_verified
        )


class IsSameDenomination(permissions.BasePermission):
    """
    Permission check: User must be in the same denomination as the object
    """
    message = "You can only access resources within your denomination."
    
    def has_object_permission(self, request, view, obj):
        # Super admin has access to everything
        if request.user.is_super_admin():
            return True
        
        # Check if object has denomination attribute
        if hasattr(obj, 'denomination'):
            return obj.denomination == request.user.denomination
        
        # Check if object itself is a denomination
        if obj.__class__.__name__ == 'Denomination':
            return obj == request.user.denomination
        
        return False


class IsSameChurchBranch(permissions.BasePermission):
    """
    Permission check: User must be in the same church branch as the object
    """
    message = "You can only access resources within your church branch."
    
    def has_object_permission(self, request, view, obj):
        # Super admin and denomination admin have broader access
        if request.user.is_super_admin():
            return True
        
        if request.user.is_denomination_admin():
            # Denomination admin can access all branches in their denomination
            if hasattr(obj, 'denomination'):
                return obj.denomination == request.user.denomination
            if hasattr(obj, 'church_branch') and obj.church_branch:
                return obj.church_branch.denomination == request.user.denomination
        
        # Church admin can only access their branch
        if request.user.is_church_admin():
            if hasattr(obj, 'church_branch'):
                return obj.church_branch == request.user.church_branch
            # If object is the church branch itself
            if obj.__class__.__name__ == 'ChurchBranch':
                return obj == request.user.church_branch
        
        return False