from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django import forms
from django.views.generic  import View
from django.forms import inlineformset_factory
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .models import Fournisseur, CommandeFournisseur, ReceptionAppro, PaiementFournisseur
from .forms import (
    FournisseurForm, CommandeFournisseurForm, CommandeLigneFormSet,
    ReceptionApproForm, PaiementFournisseurForm
)

# Fournisseurs
class FournisseurListView(ListView):
    model = Fournisseur
    template_name = 'fournisseurs/liste.html'
    context_object_name = 'fournisseurs'
    paginate_by = 8

class FournisseurCreateView(CreateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'fournisseurs/form.html'
    success_url = reverse_lazy('fournisseurs:liste')

class FournisseurUpdateView(UpdateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'fournisseurs/form.html'
    success_url = reverse_lazy('fournisseurs:liste')

class FournisseurDeleteView(DeleteView):
    model = Fournisseur
    template_name = 'fournisseurs/confirm_delete.html'
    success_url = reverse_lazy('fournisseurs:liste')


class FournisseurDetailView(DetailView):
    model = Fournisseur
    template_name = 'fournisseurs/detail.html'
    context_object_name = 'fournisseur'



# Commandes
class CommandeListView(ListView):
    model = CommandeFournisseur
    template_name = 'fournisseurs/commandes.html'
    context_object_name = 'commandes'
    paginate_by = 8
    


class CommandeDetailView(DetailView):
    model = CommandeFournisseur
    template_name = 'fournisseurs/commande_detail.html'
    context_object_name = 'commande'



def commande_create(request):
    form = CommandeFournisseurForm(request.POST or None)
    formset = CommandeLigneFormSet(request.POST or None)
    if request.method=='POST' and form.is_valid() and formset.is_valid():
        cmd = form.save()
        formset.instance = cmd
        formset.save()
        return redirect('fournisseurs:commandes')
    return render(request,'fournisseurs/commande_form.html',{'form':form,'formset':formset})


def commande_update(request, pk):
    cmd = get_object_or_404(CommandeFournisseur, pk=pk)
    form = CommandeFournisseurForm(request.POST or None, instance=cmd)
    formset = CommandeLigneFormSet(request.POST or None, instance=cmd)
    if request.method=='POST' and form.is_valid() and formset.is_valid():
        form.save(); formset.save()
        return redirect('fournisseurs:commandes')
    return render(request,'fournisseurs/commande_form.html',{'form':form,'formset':formset})


def commande_generate_pdf(request, pk):
    """
    Vue appelée par le bouton “Générer PDF” :
    - Récupère la commande
    - Appelle la méthode generate_pdf() du modèle
    - Redirige vers la page de détail de la commande
    """
    cmd = get_object_or_404(CommandeFournisseur, pk=pk)
    cmd.generate_pdf()
    return redirect('fournisseurs:commande_detail', pk=pk)



# Réceptions
class ReceptionListView(ListView):
    model = ReceptionAppro
    template_name = 'fournisseurs/receptions.html'
    context_object_name = 'receptions'
    paginate_by = 8



#==========================================================================
# Réception d'une commande fournisseur
#==========================================================================
# fournisseurs/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .models import CommandeFournisseur, ReceptionAppro
from .forms import BaseReceptionFormSet

class ReceptionCreateView(View):
    template_name = 'fournisseurs/reception_form.html'

    def _make_formset(self, cmd, post_data=None):
        # Prépare l'initial et le label du produit
        initial = []
        for lg in cmd.lignes.all():
            initial.append({
                'produit': lg.produit.pk,
                'quantite_commandee': lg.quantite,
                'produit_label': str(lg.produit),  # pour afficher le nom
            })

        # On « sous‐classe » le formset pour donner extra = nombre de lignes
        DynamicReceptionFormSet = type(
            'DynamicReceptionFormSet',
            (BaseReceptionFormSet,),
            {'extra': len(initial)}
        )

        kwargs = dict(
            instance=cmd,
            initial=initial,
            queryset=ReceptionAppro.objects.none()
        )
        if post_data is not None:
            kwargs['data'] = post_data

        return DynamicReceptionFormSet(**kwargs)

    def get(self, request, pk):
        cmd = get_object_or_404(CommandeFournisseur, pk=pk)
        formset = self._make_formset(cmd)
        return render(request, self.template_name, {
            'commande': cmd,
            'formset': formset,
        })

    def post(self, request, pk):
        cmd = get_object_or_404(CommandeFournisseur, pk=pk)
        formset = self._make_formset(cmd, post_data=request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('fournisseurs:receptions')
        # si invalide, on ré‐affiche avec le même initial
        return render(request, self.template_name, {
            'commande': cmd,
            'formset': formset,
        })

        
        
    
    
    
    
    
    
    
    
    
    
 #==========================================================================       








# Paiements
#==========================================================================
class PaiementListView(ListView):
    model = PaiementFournisseur
    template_name = 'fournisseurs/paiements.html'
    context_object_name = 'paiements'
    paginate_by = 8

class PaiementCreateView(CreateView):
    model = PaiementFournisseur
    form_class = PaiementFournisseurForm
    template_name = 'fournisseurs/paiements_form.html'
    success_url = reverse_lazy('fournisseurs:paiements')