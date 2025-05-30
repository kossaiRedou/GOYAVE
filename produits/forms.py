from django import forms
from .models import Produit

class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['nom', 'code', 'prix_achat', 'prix_vente', 'monnaie', 'stock', 'image']
        widgets = {
            'prix_achat': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'prix_vente': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        prix_achat = cleaned_data.get('prix_achat')
        prix_vente = cleaned_data.get('prix_vente')

        if prix_achat and prix_vente:
            if prix_achat < 0:
                self.add_error('prix_achat', "Le prix d'achat ne peut pas être négatif")
            if prix_vente < 0:
                self.add_error('prix_vente', "Le prix de vente ne peut pas être négatif")
            if prix_achat > prix_vente:
                self.add_error('prix_achat', "Le prix d'achat ne peut pas être supérieur au prix de vente")

        return cleaned_data