from django.urls import path
from .views import (
    VenteListView, VenteDetailView,
    vente_create, vente_update,
    paiement_create, facture_generate,
    VenteDeleteView
)

app_name = 'ventes'
urlpatterns = [
    path('',          VenteListView.as_view(),  name='list'),
    path('new/',      vente_create,             name='nouvelle'),
    path('<int:pk>/', VenteDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/',   vente_update,       name='modifier'),
    path('<int:pk>/delete/', VenteDeleteView.as_view(), name='delete'),
    path('<int:pk>/paiement/', paiement_create,    name='paiement'),
    path('<int:pk>/facture/',  facture_generate,    name='facture'),
]