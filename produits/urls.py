from django.urls import path
from .views import (
    ProduitListView, ProduitDetailView,
    ProduitCreateView, ProduitUpdateView, ProduitDeleteView
)

app_name = 'produits'
urlpatterns = [
    path('',                ProduitListView.as_view(),   name='liste'),
    path('ajouter/',        ProduitCreateView.as_view(), name='ajouter'),
    path('<int:pk>/',       ProduitDetailView.as_view(), name='detail'),
    path('<int:pk>/modifier/', ProduitUpdateView.as_view(), name='modifier'),
    path('<int:pk>/supprimer/',ProduitDeleteView.as_view(), name='supprimer'),
]