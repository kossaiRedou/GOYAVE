
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



#====================================================
# fournisseurs/forms.py
#====================================================
from django import forms
from django.forms import inlineformset_factory
from .models import CommandeFournisseur, ReceptionAppro
from produits.models import Produit

class ReceptionApproForm(forms.ModelForm):
    # Champ en lecture seule pour afficher la qté commandée
    quantite_commandee = forms.IntegerField(
        label="Qté commandée",
        required=False,
        disabled=True,
    )
    # On cache le champ produit en HiddenInput pour qu’il soit reposté
    produit = forms.ModelChoiceField(
        queryset=Produit.objects.all(),
        widget=forms.HiddenInput()
    )

    class Meta:
        model = ReceptionAppro
        fields = ['produit', 'quantite_commandee', 'quantite_livree', 'reference']


# InlineFormSet par défaut extra=0
BaseReceptionFormSet = inlineformset_factory(
    CommandeFournisseur, ReceptionAppro,
    form=ReceptionApproForm,
    extra=0, can_delete=False
)


class PaiementFournisseurForm(forms.ModelForm):
    class Meta:
        model = PaiementFournisseur
        fields = ['commande','montant']