# ventes/views.py

from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, DeleteView
from .models import Vente, VenteDetail, PaiementVente
from .forms import VenteForm, VenteDetailFormSet, PaiementVenteForm

# --- AJOUTER CETTE IMPORTATION ---
from stocks.models import MouvementStock


class VenteListView(ListView):
    model = Vente
    template_name = 'ventes/liste.html'
    context_object_name = 'ventes'
    paginate_by = 20


class VenteDetailView(DetailView):
    model = Vente
    template_name = 'ventes/detail.html'
    context_object_name = 'vente'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['paiement_form'] = PaiementVenteForm()
        return ctx


def vente_create(request):
    form = VenteForm(request.POST or None)
    formset = VenteDetailFormSet(request.POST or None)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        # 1) Récupère le paiement initial depuis le form
        montant_paye = form.cleaned_data['paiement']

        # 2) Création de la vente et de ses lignes
        vente = form.save(commit=False)
        total = 0
        for fs in formset:
            if fs.cleaned_data and not fs.cleaned_data.get('DELETE', False):
                montant_ligne = fs.cleaned_data['quantite'] * fs.cleaned_data['prix_unitaire']
                fs.instance.montant_ligne = montant_ligne
                total += montant_ligne

        vente.montant_total = total
        vente.reste_du = total
        vente.save()
        formset.instance = vente
        formset.save()

        # --- AJOUT : Génération des mouvements de stock (SORTIE) ---
        for ligne in vente.lignes.all():
            MouvementStock.objects.create(
                produit=ligne.produit,
                type=MouvementStock.SORTIE,
                quantite=ligne.quantite,
                reference=f"Vente #{vente.pk}"
            )
        # ---------------------------------------------------------

        # 3) Création systématique d’un paiement (traçabilité), même si 0
        PaiementVente.objects.create(vente=vente, montant=montant_paye)

        # 4) Mise à jour du reste dû
        vente.reste_du = max(Decimal('0.00'), total - montant_paye)
        vente.save(update_fields=['reste_du'])

        return redirect('ventes:detail', pk=vente.pk)

    return render(request, 'ventes/form.html', {
        'form': form,
        'formset': formset,
    })


def paiement_create(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    form = PaiementVenteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        paiement = form.save(commit=False)
        paiement.vente = vente
        paiement.save()
        # Met à jour le reste dû
        vente.reste_du = vente.reste_du - paiement.montant
        vente.save(update_fields=['reste_du'])
    return redirect('ventes:detail', pk=vente.pk)


class VenteDeleteView(DeleteView):
    model = Vente
    template_name = 'ventes/confirm_delete.html'
    success_url = reverse_lazy('ventes:liste')


def facture_generate(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    vente.generate_facture()
    return redirect('ventes:detail', pk=pk)
