# community/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('groups/', views.GroupListView.as_view(), name='group-list'),
    path('groups/<int:id>/', views.GroupDetailView.as_view(), name='group-detail'),
    path('groups/<int:group_id>/posts/', views.GroupPostListView.as_view(), name='group-posts'),
    # Add more as needed:
    # path('posts/<int:post_id>/reactions/', ...),
    # path('chat/<int:group_id>/', ...),
]