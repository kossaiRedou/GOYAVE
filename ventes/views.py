from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, DeleteView
from django.db import transaction

from .models import Vente
from .forms import VenteForm, VenteDetailFormSet, PaiementVenteForm
from .services import recalc_vente_et_stock

class VenteListView(ListView):
    model = Vente
    template_name = 'ventes/list.html'
    context_object_name = 'ventes'

class VenteDetailView(DetailView):
    model = Vente
    template_name = 'ventes/detail.html'
    context_object_name = 'vente'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['paiement_form'] = PaiementVenteForm()
        return ctx


def vente_create(request):
    form, formset = VenteForm(request.POST or None), VenteDetailFormSet(request.POST or None)
    if request.method=='POST' and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            montant_paye = form.cleaned_data['paiement']
            vente = form.save(commit=False)
            vente.montant_total = vente.reste_du = 0
            vente.save()
            formset.instance = vente
            formset.save()
            # paiement initial
            from .models import PaiementVente
            PaiementVente.objects.create(vente=vente, montant=montant_paye)
            recalc_vente_et_stock(vente)
        return redirect('ventes:detail', vente.pk)
    return render(request,'ventes/form.html', {'form':form,'formset':formset})


def vente_update(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    form = VenteForm(request.POST or None, instance=vente)
    form.fields.pop('paiement')  # on ne gère plus paiement ici
    formset = VenteDetailFormSet(request.POST or None, instance=vente)
    if request.method=='POST' and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            form.save()
            formset.save()
            recalc_vente_et_stock(vente)
        return redirect('ventes:detail', vente.pk)
    return render(request,'ventes/form.html', {'form':form,'formset':formset,'vente':vente,'update':True})


def paiement_create(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    form = PaiementVenteForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        pay = form.save(commit=False)
        pay.vente = vente; pay.save()
        recalc_vente_et_stock(vente)
    return redirect('ventes:detail', pk)

class VenteDeleteView(DeleteView):
    model = Vente
    template_name = 'ventes/confirm_delete.html'
    success_url = reverse_lazy('ventes:list')


def facture_generate(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    vente.generate_facture()
    return redirect('ventes:detail', pk)