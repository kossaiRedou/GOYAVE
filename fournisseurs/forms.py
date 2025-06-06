from django import forms
from django.forms import inlineformset_factory
from .models import Fournisseur, CommandeFournisseur, LigneCommande, ReceptionAppro, PaiementFournisseur
from django.core.exceptions import ValidationError

class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ['nom','contact','email','actif']

class CommandeFournisseurForm(forms.ModelForm):
    class Meta:
        model = CommandeFournisseur
        fields = ['fournisseur']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fournisseur'].empty_label = "Sélectionnez un fournisseur"
        self.fields['fournisseur'].queryset = Fournisseur.objects.filter(actif=True)

    def clean_fournisseur(self):
        fournisseur = self.cleaned_data.get('fournisseur')
        if not fournisseur:
            raise ValidationError("Le fournisseur est obligatoire")
        if not fournisseur.actif:
            raise ValidationError("Ce fournisseur n'est plus actif")
        return fournisseur

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
    # On cache le champ produit en HiddenInput pour qu'il soit reposté
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
        model  = PaiementFournisseur
        fields = ['montant']
        widgets = {
            'montant': forms.NumberInput(attrs={'step': '0.01'})
        }