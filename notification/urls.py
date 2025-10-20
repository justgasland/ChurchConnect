# notifications/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<int:id>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('mark-all-read/', views.MarkAllNotificationsAsReadView.as_view(), name='mark-all-read'),
]