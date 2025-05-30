from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    path('', views.AlertListView.as_view(), name='liste'),
    path('api/count/', views.get_unread_count, name='unread_count'),
    path('api/mark-read/<int:pk>/', views.mark_as_read, name='mark_read'),
    path('api/mark-unread/<int:pk>/', views.mark_as_unread, name='mark_unread'),
    path('api/delete/<int:pk>/', views.delete_alert, name='delete'),
]