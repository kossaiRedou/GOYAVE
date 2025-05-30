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
from django.http import JsonResponse, FileResponse
from produits.models import Produit
from dal import autocomplete
import os
from django.conf import settings


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
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Sauvegarder la commande
                    cmd = form.save()
        
                    # Lier le formset à la commande
                    formset.instance = cmd
                    
                    # Vérifier qu'il y a au moins une ligne non supprimée
                    if not any(
                        form.cleaned_data and not form.cleaned_data.get('DELETE', False)
                        for form in formset.forms
                    ):
                        cmd.delete()
                        messages.error(request, "La commande doit contenir au moins une ligne")
                        return render(request, 'fournisseurs/commande_form.html', {
                            'form': form,
                            'formset': formset
                        })
                    
                    # Sauvegarder les lignes
                    formset.save()
                    
                    # Recalculer le montant total
                    recalc_commande_total(cmd)
                    messages.success(request, "Commande créée avec succès.")
                    return redirect('fournisseurs:commandes')
                    
            except Exception as e:
                messages.error(request, f"Erreur : {str(e)}")
                import traceback
                print(traceback.format_exc())
        else:
            # Afficher les erreurs du formset
            for form in formset:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Erreur dans la ligne {form.prefix}: {error}")
            
            # Afficher les erreurs du formulaire principal
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
    
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
    - Génère le PDF
    - Envoie directement le fichier au navigateur
    """
    try:
        cmd = get_object_or_404(CommandeFournisseur, pk=pk)
        pdf_path = cmd.generate_pdf()
        
        # Ouvrir le fichier PDF
        pdf_file = open(os.path.join(settings.MEDIA_ROOT, pdf_path), 'rb')
        
        # Créer la réponse avec le fichier
        response = FileResponse(pdf_file)
        
        # Définir les en-têtes pour forcer le téléchargement
        filename = f"commande_{cmd.pk}.pdf"
        response['Content-Type'] = 'application/pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du PDF : {str(e)}")
        import traceback
        print("Erreur de génération PDF :")
        print(traceback.format_exc())
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
                'prix_achat': lg.prix_achat,  # Ajout du prix d'achat de la ligne
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
            try:
                with transaction.atomic():
                    # Sauvegarder les réceptions
                    formset.save()
                    
                    # Mettre à jour les prix d'achat des lignes de commande si modifiés
                    for form in formset:
                        if form.cleaned_data.get('prix_achat'):
                            ligne = cmd.lignes.get(produit=form.cleaned_data['produit'])
                            if ligne.prix_achat != form.cleaned_data['prix_achat']:
                                ligne.prix_achat = form.cleaned_data['prix_achat']
                                ligne.save()
                    
                    # Recalculer le montant total de la commande
                    from .services import recalc_commande_total
                    recalc_commande_total(cmd)
                    
                    return redirect('fournisseurs:receptions')
            except Exception as e:
                messages.error(request, f"Erreur lors de la sauvegarde : {str(e)}")
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

def search_products(request):
    """Vue pour rechercher des produits et retourner leurs informations en JSON"""
    query = request.GET.get('q', '')
    if query.isdigit():
        # Si q est un ID, chercher directement le produit
        products = Produit.objects.filter(id=query)
    else:
        # Sinon chercher par nom
        products = Produit.objects.filter(nom__icontains=query)
    
    data = [{
        'id': p.id,
        'nom': p.nom,
        'prix_achat': float(p.prix_achat) if p.prix_achat else 0
    } for p in products[:10]]  # Limiter à 10 résultats
    
    return JsonResponse(data, safe=False)

class ProduitAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Produit.objects.none()

        qs = Produit.objects.all()

        if self.q:
            qs = qs.filter(nom__icontains=self.q)

        return qs[:10]  # Limiter à 10 résultats
