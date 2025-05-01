from django.shortcuts import render
from django.urls import reverse_lazy
from .models import Client

from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)


class ClientListView(ListView):
    model               = Client
    template_name       = 'clients/liste.html'
    context_object_name = 'clients'
    paginate_by         = 20


class ClientDetailView(DetailView):
    model               = Client
    template_name       = 'clients/detail.html'
    context_object_name = 'client'


class ClientCreateView(CreateView):
    model         = Client
    fields        = ['nom', 'email', 'telephone', 'adresse']
    template_name = 'clients/form.html'
    success_url   = reverse_lazy('clients:liste')


class ClientUpdateView(UpdateView):
    model         = Client
    fields        = ['nom', 'email', 'telephone', 'adresse']
    template_name = 'clients/form.html'
    success_url   = reverse_lazy('clients:liste')


class ClientDeleteView(DeleteView):
    model         = Client
    template_name = 'clients/confirm_delete.html'
    success_url   = reverse_lazy('clients:liste')
