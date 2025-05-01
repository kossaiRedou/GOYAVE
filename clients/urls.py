from django.urls import path
from .views import (
    ClientListView, ClientDetailView,
    ClientCreateView, ClientUpdateView, ClientDeleteView
)

app_name = 'clients'
urlpatterns = [
    path('',                   ClientListView.as_view(),   name='liste'),
    path('ajouter/',           ClientCreateView.as_view(), name='ajouter'),
    path('<int:pk>/',          ClientDetailView.as_view(), name='detail'),
    path('<int:pk>/modifier/', ClientUpdateView.as_view(), name='modifier'),
    path('<int:pk>/supprimer/',ClientDeleteView.as_view(), name='supprimer'),
]
