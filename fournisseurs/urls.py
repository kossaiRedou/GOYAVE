from django.urls import path
from .views import (
    FournisseurListView,
    FournisseurCreateView,
    FournisseurUpdateView,
    FournisseurDeleteView,
    FournisseurDetailView,
    CommandeListView,
    CommandeDetailView,
    commande_create,
    commande_update,
    commande_generate_pdf,
    ReceptionListView,
    ReceptionCreateView,
    PaiementListView,
    PaiementCreateView
)

app_name = 'fournisseurs'
urlpatterns = [
    # Fournisseurs
    path('', FournisseurListView.as_view(), name='liste'),
    path('ajouter/', FournisseurCreateView.as_view(), name='ajouter'),
    path('<int:pk>/', FournisseurDetailView.as_view(), name='detail'),
    path('<int:pk>/modifier/', FournisseurUpdateView.as_view(), name='modifier'),
    path('<int:pk>/supprimer/', FournisseurDeleteView.as_view(), name='supprimer'),

    # Commandes fournisseur
    path('commandes/', CommandeListView.as_view(), name='commandes'),
    path('commandes/nouveau/', commande_create, name='commande_create'),
    path('commandes/<int:pk>/', CommandeDetailView.as_view(), name='commande_detail'),
    path('commandes/<int:pk>/modifier/', commande_update, name='commande_update'),
    path('commandes/<int:pk>/pdf/', commande_generate_pdf, name='commande_generate_pdf'),

    # Réceptions
    path('receptions/', ReceptionListView.as_view(), name='receptions'),
    path('commandes/<int:pk>/receptionner/', ReceptionCreateView.as_view(), name='reception_commande'),

    # Paiements fournisseurs
    path('paiements/', PaiementListView.as_view(), name='paiements'),
    path('paiements/nouveau/', PaiementCreateView.as_view(), name='paiement_create'),
]