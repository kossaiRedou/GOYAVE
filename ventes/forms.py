
### `ventes/forms.py`
from decimal import Decimal
from django import forms
from django.forms import inlineformset_factory
from .models import Vente, VenteDetail, PaiementVente

class VenteForm(forms.ModelForm):
    paiement = forms.DecimalField(
        label="Paiement initial",
        required=True,
        min_value=Decimal('0.00'),
        max_digits=12, decimal_places=2,
        help_text="Montant payé à la création (peut être 0)."
    )
    class Meta:
        model = Vente
        fields = ['client']
        exclude = ()

class VenteDetailForm(forms.ModelForm):
    class Meta:
        model = VenteDetail
        fields = ['produit', 'quantite', 'prix_unitaire']


VenteDetailFormSet = inlineformset_factory(
    Vente, VenteDetail,
    form=VenteDetailForm,
    extra=1
)


class PaiementVenteForm(forms.ModelForm):
    class Meta:
        model = PaiementVente
        fields = ['montant']