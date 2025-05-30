from django import forms
from django.forms import inlineformset_factory
from .models import Fournisseur, CommandeFournisseur, LigneCommande, ReceptionAppro, PaiementFournisseur
from django.core.exceptions import ValidationError
from dal import autocomplete
from django.db import models
from produits.models import Produit

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
        fields = ['produit', 'quantite', 'prix_achat']
        widgets = {
            'produit': autocomplete.ModelSelect2(
                url='fournisseurs:produit-autocomplete',
                attrs={
                    'data-placeholder': 'Rechercher un produit...',
                    'data-minimum-input-length': 2,
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.produit_id:
            # Si on a déjà un produit, on pré-remplit le prix d'achat
            self.fields['prix_achat'].initial = self.instance.produit.prix_achat

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
    quantite_commandee = forms.IntegerField(
        label="Qté commandée",
        required=False,
        disabled=True,
    )
    prix_achat = forms.DecimalField(
        label="Prix d'achat",
        max_digits=10,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'class': 'form-control',
            'placeholder': "Prix d'achat"
        }),
        help_text="Prix d'achat de la commande (modifiable si changement)"
    )
    produit = forms.ModelChoiceField(
        queryset=Produit.objects.all(),
        widget=forms.HiddenInput()
    )

    class Meta:
        model = ReceptionAppro
        fields = ['produit', 'quantite_commandee', 'quantite_livree', 'prix_achat', 'reference']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'commande'):
            # Récupérer la ligne de commande correspondante
            ligne = self.instance.commande.lignes.filter(produit=self.instance.produit).first()
            if ligne:
                # Utiliser le prix d'achat de la ligne de commande
                self.fields['prix_achat'].initial = ligne.prix_achat
                self.fields['quantite_commandee'].initial = ligne.quantite
                # Calculer la quantité déjà reçue
                deja_recu = self.instance.commande.receptions.filter(
                    produit=self.instance.produit
                ).exclude(pk=self.instance.pk).aggregate(
                    total=models.Sum('quantite_livree')
                )['total'] or 0
                self.fields['quantite_livree'].help_text = f"Déjà reçu: {deja_recu} / {ligne.quantite}"

    def clean(self):
        cleaned_data = super().clean()
        quantite_livree = cleaned_data.get('quantite_livree')
        produit = cleaned_data.get('produit')
        prix_achat = cleaned_data.get('prix_achat')

        if not all([quantite_livree, produit, prix_achat]):
            return cleaned_data

        if quantite_livree <= 0:
            raise ValidationError("La quantité livrée doit être supérieure à 0")

        if prix_achat <= 0:
            raise ValidationError("Le prix d'achat doit être supérieur à 0")

        # Vérifier la quantité totale reçue
        ligne = self.instance.commande.lignes.filter(produit=produit).first()
        if not ligne:
            raise ValidationError("Ce produit n'est pas dans la commande d'origine")

        deja_recu = self.instance.commande.receptions.exclude(
            pk=self.instance.pk
        ).filter(produit=produit).aggregate(
            total=models.Sum('quantite_livree')
        )['total'] or 0

        if deja_recu + quantite_livree > ligne.quantite:
            raise ValidationError({
                'quantite_livree': (
                    f"La quantité totale reçue ({deja_recu + quantite_livree}) "
                    f"ne peut pas dépasser la quantité commandée ({ligne.quantite})"
                )
            })

        return cleaned_data


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