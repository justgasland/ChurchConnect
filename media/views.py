"""
Class-Based Views for MediaHub Management
"""

from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q
from django.shortcuts import get_object_or_404

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
from .serializers import (
    MediaCategorySerializer,
    MediaTagSerializer,
    MediaItemListSerializer,
    MediaItemDetailSerializer,
    MediaItemCreateUpdateSerializer,
    MediaPlaylistSerializer,
    MediaFavoriteSerializer,
    MediaCommentSerializer,
    MediaRatingSerializer,
    MediaStatisticsSerializer
)
from authentication.permissions import IsAnyAdmin


# ==================== CATEGORY VIEWS ====================

class MediaCategoryListCreateView(generics.ListCreateAPIView):
    """
    List media categories or create a new one
    GET/POST /api/media/categories/
    """
    queryset = MediaCategory.objects.filter(is_active=True)
    serializer_class = MediaCategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    def get_permissions(self):
        """Public can view, admins can create"""
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAnyAdmin()]
        return [AllowAny()]
    
    def create(self, request, *args, **kwargs):
        """Create category"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Category created successfully!',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        """List categories"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })


class MediaCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update or delete a category
    GET/PUT/PATCH/DELETE /api/media/categories/<id>/
    """
    queryset = MediaCategory.objects.all()
    serializer_class = MediaCategorySerializer
    permission_classes = [IsAuthenticated, IsAnyAdmin]
    lookup_field = 'id'
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Category updated successfully!',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Category deactivated successfully!'
        })


# ==================== TAG VIEWS ====================

class MediaTagListCreateView(generics.ListCreateAPIView):
    """
    List tags or create a new one
    GET/POST /api/media/tags/
    """
    queryset = MediaTag.objects.all()
    serializer_class = MediaTagSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    def get_permissions(self):
        """Public can view, authenticated users can create"""
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def create(self, request, *args, **kwargs):
        """Create tag"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Tag created successfully!',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        """List tags"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })


# ==================== MEDIA ITEM VIEWS ====================

class MediaItemListCreateView(generics.ListCreateAPIView):
    """
    List all media or create a new one
    GET/POST /api/media/
    """
    queryset = MediaItem.objects.select_related('category', 'church_branch', 'uploaded_by')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'media_type', 'category', 'church_branch', 'visibility',
        'status', 'is_featured', 'language'
    ]
    search_fields = ['title', 'description', 'author', 'tags__name']
    ordering_fields = ['created_at', 'published_date', 'view_count', 'play_count']
    ordering = ['-published_date', '-created_at']
    
    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'POST':
            return MediaItemCreateUpdateSerializer
        return MediaItemListSerializer
    
    def get_permissions(self):
        """Public can view published, admins can create"""
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAnyAdmin()]
        return [AllowAny()]
    
    def get_queryset(self):
        """Filter media based on user and visibility"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Public users see only public published media
        if not user.is_authenticated:
            return queryset.filter(
                status=MediaItem.Status.PUBLISHED,
                visibility=MediaItem.Visibility.PUBLIC
            )
        
        # Super admin sees all
        if user.is_super_admin():
            return queryset
        
        # Admins see their church/denomination media
        if user.is_admin():
            if user.church_branch:
                return queryset.filter(
                    Q(church_branch=user.church_branch) |
                    Q(visibility=MediaItem.Visibility.PUBLIC, status=MediaItem.Status.PUBLISHED)
                )
        
        # Regular members see published media
        if user.church_branch:
            return queryset.filter(
                Q(church_branch=user.church_branch, status=MediaItem.Status.PUBLISHED) |
                Q(visibility__in=[MediaItem.Visibility.PUBLIC, MediaItem.Visibility.MEMBERS_ONLY], 
                  status=MediaItem.Status.PUBLISHED)
            )
        
        # Default: public published media
        return queryset.filter(
            status=MediaItem.Status.PUBLISHED,
            visibility=MediaItem.Visibility.PUBLIC
        )
    
    def create(self, request, *args, **kwargs):
        """Create media item"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        media_item = serializer.save()
        
        # Return full details
        response_serializer = MediaItemDetailSerializer(media_item, context={'request': request})
        
        return Response({
            'success': True,
            'message': 'Media item created successfully!',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        """List media items"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })


class MediaItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update or delete a media item
    GET/PUT/PATCH/DELETE /api/media/<id>/
    """
    queryset = MediaItem.objects.select_related('category', 'church_branch')
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Use different serializers for different methods"""
        if self.request.method in ['PUT', 'PATCH']:
            return MediaItemCreateUpdateSerializer
        return MediaItemDetailSerializer
    
    def get_permissions(self):
        """Public can view, admins can modify"""
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsAnyAdmin()]
    
    def retrieve(self, request, *args, **kwargs):
        """Get media details and increment view count"""
        instance = self.get_object()
        
        # Increment view count
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        
        serializer = self.get_serializer(instance, context={'request': request})
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """Update media item"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return full details
        response_serializer = MediaItemDetailSerializer(instance, context={'request': request})
        
        return Response({
            'success': True,
            'message': 'Media item updated successfully!',
            'data': response_serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Archive media item"""
        instance = self.get_object()
        instance.status = MediaItem.Status.ARCHIVED
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Media item archived successfully!'
        })


class MediaItemPlayView(APIView):
    """
    Record play/stream event
    POST /api/media/<id>/play/
    """
    permission_classes = [AllowAny]
    
    def post(self, request, id):
        """Increment play count"""
        media_item = get_object_or_404(MediaItem, id=id)
        media_item.play_count += 1
        media_item.save(update_fields=['play_count'])
        
        return Response({
            'success': True,
            'message': 'Play recorded',
            'play_count': media_item.play_count
        })


class MediaItemDownloadView(APIView):
    """
    Record download event
    POST /api/media/<id>/download/
    """
    permission_classes = [AllowAny]
    
    def post(self, request, id):
        """Increment download count"""
        media_item = get_object_or_404(MediaItem, id=id)
        
        if not media_item.allow_download:
            return Response({
                'success': False,
                'message': 'Downloads are not allowed for this media'
            }, status=status.HTTP_403_FORBIDDEN)
        
        media_item.download_count += 1
        media_item.save(update_fields=['download_count'])
        
        return Response({
            'success': True,
            'message': 'Download recorded',
            'download_count': media_item.download_count
        })


# ==================== PLAYLIST VIEWS ====================

class MediaPlaylistListCreateView(generics.ListCreateAPIView):
    """
    List playlists or create a new one
    GET/POST /api/media/playlists/
    """
    queryset = MediaPlaylist.objects.select_related('created_by', 'church_branch')
    serializer_class = MediaPlaylistSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        """Filter playlists based on user"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Show public playlists + user's own playlists
        return queryset.filter(
            Q(visibility=MediaPlaylist.Visibility.PUBLIC) |
            Q(created_by=user)
        )
    
    def create(self, request, *args, **kwargs):
        """Create playlist"""
        data = request.data.copy()
        data['created_by'] = request.user.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Playlist created successfully!',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        """List playlists"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })


class MediaPlaylistDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update or delete a playlist
    GET/PUT/PATCH/DELETE /api/media/playlists/<id>/
    """
    queryset = MediaPlaylist.objects.select_related('created_by')
    serializer_class = MediaPlaylistSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check ownership
        if instance.created_by != request.user and not request.user.is_admin():
            return Response({
                'success': False,
                'message': 'You do not have permission to edit this playlist'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Playlist updated successfully!',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check ownership
        if instance.created_by != request.user and not request.user.is_admin():
            return Response({
                'success': False,
                'message': 'You do not have permission to delete this playlist'
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance.delete()
        
        return Response({
            'success': True,
            'message': 'Playlist deleted successfully!'
        })


class AddToPlaylistView(APIView):
    """
    Add media item to playlist
    POST /api/media/playlists/<playlist_id>/add/<media_id>/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, playlist_id, media_id):
        """Add item to playlist"""
        playlist = get_object_or_404(MediaPlaylist, id=playlist_id)
        media_item = get_object_or_404(MediaItem, id=media_id)
        
        # Check ownership
        if playlist.created_by != request.user and not request.user.is_admin():
            return Response({
                'success': False,
                'message': 'You do not have permission to edit this playlist'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Add to playlist
        playlist_item, created = PlaylistItem.objects.get_or_create(
            playlist=playlist,
            media_item=media_item,
            defaults={'order': playlist.playlist_items.count()}
        )
        
        if not created:
            return Response({
                'success': False,
                'message': 'Item already in playlist'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': 'Item added to playlist successfully!'
        })


# ==================== FAVORITE VIEWS ====================

class MediaFavoriteListView(generics.ListAPIView):
    """
    List user's favorite media
    GET /api/media/favorites/
    """
    serializer_class = MediaFavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MediaFavorite.objects.filter(user=self.request.user).select_related('media_item')
    
    def list(self, request, *args, **kwargs):
        """List favorites"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })


class ToggleFavoriteView(APIView):
    """
    Add or remove from favorites
    POST /api/media/<id>/favorite/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, id):
        """Toggle favorite status"""
        media_item = get_object_or_404(MediaItem, id=id)
        
        favorite, created = MediaFavorite.objects.get_or_create(
            user=request.user,
            media_item=media_item
        )
        
        if not created:
            favorite.delete()
            return Response({
                'success': True,
                'message': 'Removed from favorites',
                'is_favorited': False
            })
        
        return Response({
            'success': True,
            'message': 'Added to favorites',
            'is_favorited': True
        })


# ==================== COMMENT & RATING VIEWS ====================

class MediaCommentListCreateView(generics.ListCreateAPIView):
    """
    List or create comments
    GET/POST /api/media/<media_id>/comments/
    """
    serializer_class = MediaCommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        media_id = self.kwargs.get('media_id')
        return MediaComment.objects.filter(
            media_item_id=media_id,
            is_approved=True,
            parent=None  # Only top-level comments
        ).select_related('user')
    
    def create(self, request, media_id):
        """Create comment"""
        data = request.data.copy()
        data['media_item'] = media_id
        data['user'] = request.user.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Comment posted successfully!',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, media_id):
        """List comments"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })


class MediaRatingCreateUpdateView(APIView):
    """
    Create or update rating
    POST /api/media/<media_id>/rate/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, media_id):
        """Create or update rating"""
        media_item = get_object_or_404(MediaItem, id=media_id)
        
        data = request.data.copy()
        data['media_item'] = media_id
        
        # Check if user already rated
        try:
            rating = MediaRating.objects.get(user=request.user, media_item=media_item)
            serializer = MediaRatingSerializer(rating, data=data, partial=True, context={'request': request})
        except MediaRating.DoesNotExist:
            serializer = MediaRatingSerializer(data=data, context={'request': request})
        
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Rating submitted successfully!',
            'data': serializer.data
        })


# ==================== STATISTICS VIEWS ====================

class MediaStatisticsView(APIView):
    """
    Get media statistics
    GET /api/media/statistics/
    """
    permission_classes = [IsAuthenticated, IsAnyAdmin]
    
    def get(self, request):
        """Calculate media statistics"""
        user = request.user
        
        # Filter based on user role
        if user.is_super_admin():
            media = MediaItem.objects.all()
        elif user.is_denomination_admin() and user.denomination:
            media = MediaItem.objects.filter(denomination=user.denomination)
        elif user.church_branch:
            media = MediaItem.objects.filter(church_branch=user.church_branch)
        else:
            media = MediaItem.objects.none()
        
        stats = {
            'total_media': media.count(),
            'total_sermons': media.filter(media_type=MediaItem.MediaType.SERMON).count(),
            'total_music': media.filter(media_type=MediaItem.MediaType.MUSIC).count(),
            'total_books': media.filter(media_type=MediaItem.MediaType.BOOK).count(),
            'total_videos': media.filter(media_type=MediaItem.MediaType.VIDEO).count(),
            'total_views': media.aggregate(total=Count('view_count'))['total'] or 0,
            'total_downloads': media.aggregate(total=Count('download_count'))['total'] or 0,
            'total_favorites': MediaFavorite.objects.filter(media_item__in=media).count(),
            'total_comments': MediaComment.objects.filter(media_item__in=media).count(),
            'media_by_type': dict(
                media.values('media_type').annotate(count=Count('id')).values_list('media_type', 'count')
            ),
            'media_by_category': dict(
                media.values('category__name').annotate(count=Count('id')).values_list('category__name', 'count')
            ),
            'most_viewed': list(
                media.order_by('-view_count')[:5].values('id', 'title', 'view_count')
            ),
            'most_downloaded': list(
                media.order_by('-download_count')[:5].values('id', 'title', 'download_count')
            ),
            'recently_added': list(
                media.order_by('-created_at')[:5].values('id', 'title', 'created_at')
            ),
        }
        
        serializer = MediaStatisticsSerializer(stats)
        
        return Response({
            'success': True,
            'data': serializer.data
        })