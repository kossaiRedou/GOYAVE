from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from .models import Alert

class AlertListView(LoginRequiredMixin, ListView):
    model = Alert
    template_name = 'alerts/liste.html'
    context_object_name = 'alerts'
    paginate_by = 50

    def get_queryset(self):
        queryset = Alert.objects.all()

        # Filtres
        alert_type = self.request.GET.get('type')
        status = self.request.GET.get('status')
        date_from = self.request.GET.get('from')
        date_to = self.request.GET.get('to')

        if alert_type:
            queryset = queryset.filter(type=alert_type)
        
        if status:
            if status == 'read':
                queryset = queryset.filter(is_read=True)
            elif status == 'unread':
                queryset = queryset.filter(is_read=False)
            elif status == 'expired':
                queryset = queryset.filter(
                    Q(expires_at__lt=timezone.now()) | 
                    Q(created_at__lt=timezone.now() - timezone.timedelta(days=30))
                )

        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['alert_types'] = Alert.ALERT_TYPES
        context['current_type'] = self.request.GET.get('type', '')
        context['current_status'] = self.request.GET.get('status', '')
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        alert_ids = request.POST.getlist('alert_ids')

        if not alert_ids:
            messages.warning(request, "Aucune alerte sélectionnée.")
            return redirect('alerts:liste')

        alerts = Alert.objects.filter(id__in=alert_ids)
        
        if action == 'mark_read':
            alerts.update(is_read=True)
            messages.success(request, "Les alertes sélectionnées ont été marquées comme lues.")
        elif action == 'mark_unread':
            alerts.update(is_read=False)
            messages.success(request, "Les alertes sélectionnées ont été marquées comme non lues.")
        elif action == 'delete':
            alerts.delete()
            messages.success(request, "Les alertes sélectionnées ont été supprimées.")

        return redirect('alerts:liste')

@login_required
@require_GET
def get_unread_count(request):
    """Retourne le nombre d'alertes non lues au format JSON"""
    count = Alert.get_unread_count()
    return JsonResponse({'count': count})

@login_required
@require_POST
def mark_as_read(request, pk):
    """Marque une alerte comme lue"""
    alert = get_object_or_404(Alert, pk=pk)
    alert.mark_as_read()
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def mark_as_unread(request, pk):
    """Marque une alerte comme non lue"""
    alert = get_object_or_404(Alert, pk=pk)
    alert.mark_as_unread()
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def delete_alert(request, pk):
    """Supprime une alerte"""
    alert = get_object_or_404(Alert, pk=pk)
    alert.delete()
    return JsonResponse({'status': 'success'})