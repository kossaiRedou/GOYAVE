from django.contrib import admin
from .models import Fournisseur, CommandeFournisseur, LigneCommande, ReceptionAppro, PaiementFournisseur

class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 1

class ReceptionApproInline(admin.TabularInline):
    model = ReceptionAppro
    extra = 0
    readonly_fields = ['date_reception']

class PaiementFournisseurInline(admin.TabularInline):
    model = PaiementFournisseur
    extra = 0
    readonly_fields = ['date_paiement']

@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ['nom', 'contact', 'email', 'actif', 'total_commandes', 'total_non_paye']
    list_filter = ['actif']
    search_fields = ['nom', 'email']
    ordering = ['nom']

@admin.register(CommandeFournisseur)
class CommandeFournisseurAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'fournisseur', 'date_commande', 'statut', 'montant_total', 'total_paye', 'reste_a_payer']
    list_filter = ['statut', 'date_commande']
    search_fields = ['fournisseur__nom']
    inlines = [LigneCommandeInline, ReceptionApproInline, PaiementFournisseurInline]
    readonly_fields = ['date_commande', 'montant_total']
    ordering = ['-date_commande']

    def has_delete_permission(self, request, obj=None):
        if obj and obj.statut != CommandeFournisseur.EN_ATTENTE:
            return False
        return super().has_delete_permission(request, obj)
