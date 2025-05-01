from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Produit
from .forms import ProduitForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin


class ProduitListView(LoginRequiredMixin, ListView):
    model = Produit
    template_name = 'produits/liste.html'
    context_object_name = 'produits'
    paginate_by = 8

class ProduitDetailView(LoginRequiredMixin, DetailView):
    model = Produit
    template_name = 'produits/detail.html'
    context_object_name = 'produit'

class ProduitCreateView(LoginRequiredMixin, CreateView):
    model = Produit
    form_class = ProduitForm
    template_name = 'produits/form.html'
    success_url = reverse_lazy('produits:liste')

class ProduitUpdateView(LoginRequiredMixin, UpdateView):
    model = Produit
    form_class = ProduitForm
    template_name = 'produits/form.html'
    success_url = reverse_lazy('produits:liste')

class ProduitDeleteView(LoginRequiredMixin, DeleteView):
    model = Produit
    template_name = 'produits/confirm_delete.html'
    success_url = reverse_lazy('produits:liste')