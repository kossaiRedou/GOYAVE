from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('clients/', include('clients.urls')),
    path('produits/', include('produits.urls')),
    path('ventes/', include('ventes.urls')),
    path('stocks/', include('stocks.urls')),
    path('fournisseurs/', include('fournisseurs.urls')),
    path('alerts/', include('alerts.urls')),

] + (static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) if settings.DEBUG else []) 