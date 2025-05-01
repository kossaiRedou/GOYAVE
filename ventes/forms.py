# ventes/forms.py

from decimal import Decimal
from django import forms
from django.forms import inlineformset_factory
from .models import Vente, VenteDetail, PaiementVente

class VenteForm(forms.ModelForm):
    paiement = forms.DecimalField(
        label="Paiement initial",
        required=True,
        min_value=Decimal('0.00'),
        max_digits=12,
        decimal_places=2,
        #initial=Decimal('0.00'),
        help_text="Saisissez le montant payé immédiatement (peut être 0)."
    )

    class Meta:
        model = Vente
        fields = ['client']  # on gère 'paiement' séparément

class VenteDetailForm(forms.ModelForm):
    class Meta:
        model = VenteDetail
        fields = ['produit', 'quantite', 'prix_unitaire']

VenteDetailFormSet = inlineformset_factory(
    parent_model=Vente,
    model=VenteDetail,
    form=VenteDetailForm,
    extra=1,
    can_delete=True
)

class PaiementVenteForm(forms.ModelForm):
    class Meta:
        model = PaiementVente
        fields = ['montant']
