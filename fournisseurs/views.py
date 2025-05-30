from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django import forms
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView, DetailView
from django.forms import inlineformset_factory
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import (
    Fournisseur, 
    CommandeFournisseur, 
    LigneCommande, 
    ReceptionAppro, 
    PaiementFournisseur
)
from .forms import (
    FournisseurForm, 
    CommandeFournisseurForm, 
    CommandeLigneFormSet,
    ReceptionApproForm, 
    PaiementFournisseurForm
)
from .services import recalc_commande_total
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError
from django.db.transaction import atomic


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
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['paiement_form'] = PaiementFournisseurForm()
        return ctx



def commande_create(request):
    form = CommandeFournisseurForm(request.POST or None)
    formset = CommandeLigneFormSet(request.POST or None)
    
    if request.method == 'POST':
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Sauvegarder la commande
                    cmd = form.save()
                    
                    # Lier le formset à la commande
                    formset.instance = cmd
                    
                    if formset.is_valid():
                        # Vérifier qu'il y a au moins une ligne
                        if not any(
                            form.cleaned_data and not form.cleaned_data.get('DELETE', False)
                            for form in formset.forms
                        ):
                            raise ValidationError("La commande doit contenir au moins une ligne")
                        
                        # Sauvegarder les lignes
                        formset.save()
                        
                        # Recalculer le montant total
                        recalc_commande_total(cmd)
                        messages.success(request, "Commande créée avec succès.")
                        return redirect('fournisseurs:commandes')
                    else:
                        # Afficher les erreurs du formset
                        for form in formset:
                            for field, errors in form.errors.items():
                                for error in errors:
                                    messages.error(request, f"Erreur dans la ligne {form.prefix}: {error}")
                        raise ValidationError("Erreur dans les lignes de commande")
            except ValidationError as e:
                messages.error(request, str(e))
                # En cas d'erreur de validation, on supprime la commande si elle a été créée
                if 'cmd' in locals() and cmd.pk:
                    cmd.delete()
            except Exception as e:
                messages.error(request, "Une erreur est survenue lors de la création de la commande")
                # En cas d'erreur, on supprime la commande si elle a été créée
                if 'cmd' in locals() and cmd.pk:
                    cmd.delete()
    
    return render(request, 'fournisseurs/commande_form.html', {
        'form': form,
        'formset': formset
    })


def commande_update(request, pk):
    cmd = get_object_or_404(CommandeFournisseur, pk=pk)
    
    if cmd.statut == CommandeFournisseur.RECEP:
        messages.warning(request, "Cette commande est déjà réceptionnée : modifications interdites.")
        return redirect('fournisseurs:commande_detail', pk=pk)


    form = CommandeFournisseurForm(request.POST or None, instance=cmd)
    formset = CommandeLigneFormSet(request.POST or None, instance=cmd)
    if request.method=='POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        from .services import recalc_commande_total
        recalc_commande_total(cmd)
        return redirect('fournisseurs:commandes')
    return render(request,'fournisseurs/commande_form.html',{'form':form,'formset':formset})


def commande_generate_pdf(request, pk):
    """
    Vue appelée par le bouton "Générer PDF" :
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

from django.shortcuts import redirect, get_object_or_404


def commande_paiement(request, pk):
    cmd = get_object_or_404(CommandeFournisseur, pk=pk)
    if request.method == 'POST':
        form = PaiementFournisseurForm(request.POST)
        if form.is_valid():
            pay = form.save(commit=False)
            pay.commande = cmd
            pay.save()
            # on ne change pas le statut ici
            messages.success(request, "Paiement enregistré.")
            # pas de recalc_commande_total ici : on ne touche qu'à montant_total de la commande
        else:
            messages.error(request, "Erreur dans le formulaire de paiement.")
    return redirect('fournisseurs:commande_detail', pk=pk)
