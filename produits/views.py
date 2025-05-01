from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Produit
from .forms import ProduitForm

class ProduitListView(ListView):
    model = Produit
    template_name = 'produits/liste.html'
    context_object_name = 'produits'
    paginate_by = 8

class ProduitDetailView(DetailView):
    model = Produit
    template_name = 'produits/detail.html'
    context_object_name = 'produit'

class ProduitCreateView(CreateView):
    model = Produit
    form_class = ProduitForm
    template_name = 'produits/form.html'
    success_url = reverse_lazy('produits:liste')

class ProduitUpdateView(UpdateView):
    model = Produit
    form_class = ProduitForm
    template_name = 'produits/form.html'
    success_url = reverse_lazy('produits:liste')

class ProduitDeleteView(DeleteView):
    model = Produit
    template_name = 'produits/confirm_delete.html'
    success_url = reverse_lazy('produits:liste')