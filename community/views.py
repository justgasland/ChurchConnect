# community/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction

from denomination import serializers
from .models import Group, GroupMember, Post, Reaction, Comment, ChatMessage
from .serializers import (
    GroupSerializer, GroupCreateUpdateSerializer,
    PostSerializer, ReactionSerializer, CommentSerializer, ChatMessageSerializer
)
from .permissions import can_view_group, is_group_admin


class GroupListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return GroupCreateUpdateSerializer
        return GroupSerializer

    def get_queryset(self):
        user = self.request.user
        # Only show groups in user's church branch
        groups = Group.objects.filter(church_branch=user.church_branch)
        # Filter by visibility
        visible_groups = [g for g in groups if can_view_group(user, g)]
        return visible_groups

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Auto-add creator as admin
        group = serializer.instance
        GroupMember.objects.create(group=group, user=request.user, role='admin')
        response_serializer = GroupSerializer(group)
        return Response({
            'success': True,
            'message': 'Group created successfully!',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'count': len(queryset),
            'data': serializer.data
        })


class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return GroupCreateUpdateSerializer
        return GroupSerializer

    def get_queryset(self):
        return Group.objects.all()

    def get_object(self):
        obj = get_object_or_404(Group, id=self.kwargs['id'])
        if not can_view_group(self.request.user, obj):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to view this group.")
        return obj

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not is_group_admin(request.user, instance):
            return Response({
                'success': False,
                'message': 'Only group admins can update this group.'
            }, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not is_group_admin(request.user, instance):
            return Response({
                'success': False,
                'message': 'Only group admins can delete this group.'
            }, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class GroupPostListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return PostSerializer

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        group = get_object_or_404(Group, id=group_id)
        if not can_view_group(self.request.user, group):
            return Post.objects.none()
        return Post.objects.filter(group=group)

    def perform_create(self, serializer):
        group_id = self.kwargs['group_id']
        group = get_object_or_404(Group, id=group_id)
        if not can_view_group(self.request.user, group):
            raise serializers.ValidationError("You cannot post in this group.")
        serializer.save(author=self.request.user, group=group)

    def create(self, request, group_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'success': True,
            'message': 'Post created successfully!',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    def list(self, request, group_id):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })

