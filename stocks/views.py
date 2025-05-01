from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .models import MouvementStock
from .forms import MouvementStockForm

class MouvementListView(ListView):
    model = MouvementStock
    template_name = 'stocks/mouvement_list.html'
    context_object_name = 'mouvements'
    paginate_by = 20

class MouvementCreateView(CreateView):
    model = MouvementStock
    form_class = MouvementStockForm
    template_name = 'stocks/mouvement_form.html'
    success_url = reverse_lazy('stocks:mouvements')