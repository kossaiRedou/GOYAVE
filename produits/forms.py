from django import forms
from .models import Produit

class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['nom', 'code', 'prix_vente', 'monnaie', 'stock', 'image']
        widgets = {
            'prix_vente': forms.NumberInput(attrs={'step': '0.01'}),
        }