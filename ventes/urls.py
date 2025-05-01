from django.urls import path
from .views import (
    VenteListView, VenteDetailView,
    vente_create, VenteDeleteView,
    paiement_create, facture_generate
)

app_name = 'ventes'
urlpatterns = [
    path('',            VenteListView.as_view(), name='liste'),
    path('nouvelle/',   vente_create,              name='nouvelle'),
    path('<int:pk>/',   VenteDetailView.as_view(), name='detail'),
    path('<int:pk>/supprimer/', VenteDeleteView.as_view(), name='supprimer'),
    path('<int:pk>/paiement/', paiement_create, name='paiement'),
    path('<int:pk>/facture/', facture_generate, name='facture'),


]