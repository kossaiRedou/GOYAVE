from django.views.generic import TemplateView
from .context_processors import alerts as _get_alerts

class AlertListView(TemplateView):
    template_name = 'alerts/liste.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        data = _get_alerts(self.request)
        ctx.update(data)
        return ctx