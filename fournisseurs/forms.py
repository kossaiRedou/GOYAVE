
from django import forms
from django.forms import inlineformset_factory
from .models import Fournisseur, CommandeFournisseur, LigneCommande, ReceptionAppro, PaiementFournisseur

class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ['nom','contact','email','actif']

class CommandeFournisseurForm(forms.ModelForm):
    class Meta:
        model = CommandeFournisseur
        fields = ['fournisseur','statut']

class LigneCommandeForm(forms.ModelForm):
    class Meta:
        model = LigneCommande
        fields = ['produit','quantite','prix_achat']

CommandeLigneFormSet = inlineformset_factory(
    parent_model=CommandeFournisseur,
    model=LigneCommande,
    form=LigneCommandeForm,
    extra=1, can_delete=True
)

class ReceptionApproForm(forms.ModelForm):
    class Meta:
        model = ReceptionAppro
        fields = ['commande','produit','quantite_livree','reference']

class PaiementFournisseurForm(forms.ModelForm):
    class Meta:
        model = PaiementFournisseur
        fields = ['commande','montant']