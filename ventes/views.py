# ventes/views.py

from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, DeleteView
from .models import Vente, VenteDetail, PaiementVente
from .forms import VenteForm, VenteDetailFormSet, PaiementVenteForm
from django.views.generic import UpdateView
from .models import Vente, VenteDetail, PaiementVente
from .forms import VenteForm, VenteDetailFormSet
from django.db import transaction



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







#-----------------------------------------------below is the code for the update view-----------------------------------------------

from django.db import transaction
from decimal import Decimal
from django.shortcuts import redirect
from django.views.generic.edit import UpdateView
from .models import Vente
from .forms import VenteForm, VenteDetailFormSet

class VenteUpdateView(UpdateView):
    model = Vente
    form_class = VenteForm
    template_name = 'ventes/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = VenteDetailFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = VenteDetailFormSet(instance=self.object)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = VenteDetailFormSet(request.POST, instance=self.object)

        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_valid(self, form, formset):
        with transaction.atomic():
            self.object = form.save(commit=False)

            montant_total = Decimal('0.00')
            for f in formset:
                if f.cleaned_data and not f.cleaned_data.get('DELETE', False):
                    montant_total += f.cleaned_data['quantite'] * f.cleaned_data['prix_unitaire']

            self.object.montant_total = montant_total
            self.object.save()

            formset.instance = self.object
            formset.save()

        return redirect(self.object.get_absolute_url())

    def form_invalid(self, form, formset):
        return self.render_to_response(self.get_context_data(form=form, formset=formset))
