# community/serializers.py
from rest_framework import serializers
from .models import Group, GroupMember, Post, Reaction, Comment, ChatMessage
from authentication.serializers import UserSerializer


class GroupMemberSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = GroupMember
        fields = ['id', 'user', 'user_detail', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class GroupSerializer(serializers.ModelSerializer):
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    members = GroupMemberSerializer(many=True, read_only=True)
    member_count = serializers.ReadOnlyField()

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'description', 'cover_image', 'visibility',
            'created_by', 'created_by_detail', 'church_branch',
            'member_count', 'members', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']


class GroupCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name', 'description', 'cover_image', 'visibility', 'church_branch']

    def validate_church_branch(self, value):
        """Ensure user belongs to this church branch"""
        user = self.context['request'].user
        if user.church_branch != value:
            raise serializers.ValidationError("You can only create groups in your church branch.")
        return value


class PostSerializer(serializers.ModelSerializer):
    author_detail = UserSerializer(source='author', read_only=True)
    reaction_count = serializers.SerializerMethodField()
    comment_count = serializers.ReadOnlyField()

    class Meta:
        model = Post
        fields = [
            'id', 'group', 'author', 'author_detail', 'content',
            'media', 'reaction_count', 'comment_count', 'created_at'
        ]
        read_only_fields = ['id', 'author', 'created_at']

    def get_reaction_count(self, obj):
        return obj.reactions.count()


class ReactionSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Reaction
        fields = ['id', 'post', 'user', 'user_detail', 'type', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'user', 'user_detail', 'content', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_detail = UserSerializer(source='sender', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'group', 'sender', 'sender_detail', 'message', 'attachment', 'created_at']
        read_only_fields = ['id', 'sender', 'created_at']