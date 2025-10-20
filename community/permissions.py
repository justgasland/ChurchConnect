# community/permissions.py
from rest_framework import permissions

def is_group_admin(user, group):
    """Check if user is admin/mod in the group"""
    try:
        membership = group.members.get(user=user)
        return membership.role in ['admin', 'moderator']
    except:
        return False

def can_view_group(user, group):
    """Check if user can view the group based on visibility"""
    if group.visibility == 'public':
        return True
    if not user.is_authenticated:
        return False
    if user.church_branch != group.church_branch:
        return False
    if group.visibility == 'secret':
        return group.members.filter(user=user).exists()
    return True