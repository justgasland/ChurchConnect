"""
URL Configuration for MediaHub App
"""

from django.urls import path
from .views import (
    MediaCategoryListCreateView,
    MediaCategoryDetailView,
    MediaTagListCreateView,
    MediaItemListCreateView,
    MediaItemDetailView,
    MediaItemPlayView,
    MediaItemDownloadView,
    MediaPlaylistListCreateView,
    MediaPlaylistDetailView,
    AddToPlaylistView,
    MediaFavoriteListView,
    ToggleFavoriteView,
    MediaCommentListCreateView,
    MediaRatingCreateUpdateView,
    MediaStatisticsView,
)

app_name = 'mediahub'

urlpatterns = [
    # Categories
    path('categories/', MediaCategoryListCreateView.as_view(), name='category_list_create'),
    path('categories/<int:id>/', MediaCategoryDetailView.as_view(), name='category_detail'),
    
    # Tags
    path('tags/', MediaTagListCreateView.as_view(), name='tag_list_create'),
    
    # Media Items
    path('', MediaItemListCreateView.as_view(), name='media_list_create'),
    path('<int:id>/', MediaItemDetailView.as_view(), name='media_detail'),
    path('<int:id>/play/', MediaItemPlayView.as_view(), name='media_play'),
    path('<int:id>/download/', MediaItemDownloadView.as_view(), name='media_download'),
    path('statistics/', MediaStatisticsView.as_view(), name='media_statistics'),
    
    # Playlists
    path('playlists/', MediaPlaylistListCreateView.as_view(), name='playlist_list_create'),
    path('playlists/<int:id>/', MediaPlaylistDetailView.as_view(), name='playlist_detail'),
    path('playlists/<int:playlist_id>/add/<int:media_id>/', AddToPlaylistView.as_view(), name='add_to_playlist'),
    # Favorites
    path('favorites/', MediaFavoriteListView.as_view(), name='favorite_list'),
    path('<int:id>/favorite/', ToggleFavoriteView.as_view(), name='toggle_favorite'),

    # Comments and ratings
    path('<int:media_id>/comments/', MediaCommentListCreateView.as_view(), name='comments_list_create'),
    path('<int:media_id>/rate/', MediaRatingCreateUpdateView.as_view(), name='media_rate'),

    # Statistics
    path('statistics/', MediaStatisticsView.as_view(), name='media_statistics'),
    ]
    