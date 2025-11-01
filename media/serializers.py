"""
Serializers for MediaHub Management
"""

from rest_framework import serializers
from django.db.models import Avg, Count

from .models import (
    MediaCategory,
    MediaTag,
    MediaItem,
    MediaPlaylist,
    PlaylistItem,
    MediaFavorite,
    MediaComment,
    MediaRating
)
from authentication.serializers import UserSerializer


class MediaTagSerializer(serializers.ModelSerializer):
    """Serializer for media tags"""
    
    class Meta:
        model = MediaTag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['id', 'slug']


class MediaCategorySerializer(serializers.ModelSerializer):
    """Serializer for media categories"""
    
    subcategories = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaCategory
        fields = [
            'id', 'name', 'description', 'slug', 'parent',
            'is_active', 'order', 'subcategories', 'item_count',
            'created_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at']
    
    def get_subcategories(self, obj):
        """Get subcategories"""
        subcats = obj.subcategories.filter(is_active=True)
        return MediaCategorySerializer(subcats, many=True).data
    
    def get_item_count(self, obj):
        """Get media item count"""
        return obj.media_items.filter(status=MediaItem.Status.PUBLISHED).count()


class MediaItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing media"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    church_name = serializers.CharField(source='church_branch.name', read_only=True)
    tags = MediaTagSerializer(many=True, read_only=True)
    
    duration_formatted = serializers.ReadOnlyField()
    file_size_formatted = serializers.ReadOnlyField()
    has_audio = serializers.ReadOnlyField()
    has_video = serializers.ReadOnlyField()
    has_document = serializers.ReadOnlyField()
    
    average_rating = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaItem
        fields = [
            'id', 'title', 'slug', 'description', 'media_type',
            'category', 'category_name', 'tags', 'church_branch',
            'church_name', 'author', 'recorded_date', 'thumbnail',
            'duration', 'duration_formatted', 'file_size',
            'file_size_formatted', 'visibility', 'status',
            'is_featured', 'view_count', 'play_count',
            'download_count', 'has_audio', 'has_video',
            'has_document', 'average_rating', 'is_favorited',
            'created_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at']
    
    def get_average_rating(self, obj):
        """Get average rating"""
        avg = obj.ratings.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else None
    
    def get_is_favorited(self, obj):
        """Check if current user has favorited"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False


class MediaItemDetailSerializer(serializers.ModelSerializer):
    """Full serializer for media details"""
    
    category_detail = MediaCategorySerializer(source='category', read_only=True)
    tags = MediaTagSerializer(many=True, read_only=True)
    uploaded_by_detail = UserSerializer(source='uploaded_by', read_only=True)
    minister_detail = UserSerializer(source='minister', read_only=True)
    
    duration_formatted = serializers.ReadOnlyField()
    file_size_formatted = serializers.ReadOnlyField()
    has_audio = serializers.ReadOnlyField()
    has_video = serializers.ReadOnlyField()
    has_document = serializers.ReadOnlyField()
    
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    favorite_count = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaItem
        fields = '__all__'
        read_only_fields = [
            'id', 'slug', 'view_count', 'play_count',
            'download_count', 'created_at', 'updated_at'
        ]
    
    def get_average_rating(self, obj):
        """Get average rating"""
        avg = obj.ratings.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else None
    
    def get_rating_count(self, obj):
        """Get total ratings"""
        return obj.ratings.count()
    
    def get_comment_count(self, obj):
        """Get total comments"""
        return obj.comments.filter(is_approved=True).count()
    
    def get_favorite_count(self, obj):
        """Get total favorites"""
        return obj.favorited_by.count()
    
    def get_is_favorited(self, obj):
        """Check if current user has favorited"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False
    
    def get_user_rating(self, obj):
        """Get current user's rating"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            try:
                rating = obj.ratings.get(user=request.user)
                return rating.rating
            except MediaRating.DoesNotExist:
                return None
        return None


class MediaItemCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating media"""
    
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = MediaItem
        fields = [
            'title', 'description', 'media_type', 'category',
            'tag_ids', 'church_branch', 'author', 'minister',
            'recorded_date', 'thumbnail', 'audio_file',
            'video_file', 'document_file', 'external_video_url',
            'external_audio_url', 'duration', 'series',
            'series_number', 'scripture_references', 'language',
            'visibility', 'status', 'is_featured', 'allow_download'
        ]
    
    def create(self, validated_data):
        """Create media item"""
        tag_ids = validated_data.pop('tag_ids', [])
        
        # Set uploader
        request = self.context.get('request')
        if request and request.user:
            validated_data['uploaded_by'] = request.user
        
        media_item = MediaItem.objects.create(**validated_data)
        
        # Add tags
        if tag_ids:
            media_item.tags.set(tag_ids)
        
        return media_item
    
    def update(self, instance, validated_data):
        """Update media item"""
        tag_ids = validated_data.pop('tag_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update tags
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        
        return instance


class PlaylistItemSerializer(serializers.ModelSerializer):
    """Serializer for playlist items"""
    
    media_item = MediaItemListSerializer(read_only=True)
    
    class Meta:
        model = PlaylistItem
        fields = ['id', 'media_item', 'order', 'added_at']
        read_only_fields = ['id', 'added_at']


class MediaPlaylistSerializer(serializers.ModelSerializer):
    """Serializer for playlists"""
    
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    items = PlaylistItemSerializer(source='playlist_items', many=True, read_only=True)
    item_count = serializers.ReadOnlyField()
    
    class Meta:
        model = MediaPlaylist
        fields = [
            'id', 'name', 'description', 'slug', 'church_branch',
            'thumbnail', 'visibility', 'created_by',
            'created_by_detail', 'is_featured', 'item_count',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_by', 'created_at', 'updated_at']


class MediaFavoriteSerializer(serializers.ModelSerializer):
    """Serializer for favorites"""
    
    media_item = MediaItemListSerializer(read_only=True)
    
    class Meta:
        model = MediaFavorite
        fields = ['id', 'media_item', 'created_at']
        read_only_fields = ['id', 'created_at']


class MediaCommentSerializer(serializers.ModelSerializer):
    """Serializer for comments"""
    
    user_detail = UserSerializer(source='user', read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaComment
        fields = [
            'id', 'media_item', 'user', 'user_detail',
            'comment', 'parent', 'is_approved',
            'replies', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_replies(self, obj):
        """Get comment replies"""
        if obj.parent is None:
            replies = obj.replies.filter(is_approved=True)
            return MediaCommentSerializer(replies, many=True).data
        return []


class MediaRatingSerializer(serializers.ModelSerializer):
    """Serializer for ratings"""
    
    user_detail = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = MediaRating
        fields = [
            'id', 'media_item', 'user', 'user_detail',
            'rating', 'review', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        """Validate rating is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def create(self, validated_data):
        """Create rating"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['user'] = request.user
        return super().create(validated_data)


class MediaStatisticsSerializer(serializers.Serializer):
    """Serializer for media statistics"""
    
    total_media = serializers.IntegerField()
    total_sermons = serializers.IntegerField()
    total_music = serializers.IntegerField()
    total_books = serializers.IntegerField()
    total_videos = serializers.IntegerField()
    total_views = serializers.IntegerField()
    total_downloads = serializers.IntegerField()
    total_favorites = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    media_by_type = serializers.DictField()
    media_by_category = serializers.DictField()
    most_viewed = serializers.ListField()
    most_downloaded = serializers.ListField()
    recently_added = serializers.ListField()