from django.conf import settings
from produits.models import Produit


def alerts(request):
    """
    Context processor: fournit `alerts` et `alerts_unread_count` pour les low-stock.
    """
    seuil = getattr(settings, 'LOW_STOCK_THRESHOLD', 5)
    low = Produit.objects.filter(stock__lte=seuil)
    items = []
    for p in low:
        items.append({
            'message': f"Stock faible: {p.nom} (\u2264 {seuil})",  # ≤ seuil
            'target': p
        })
    return {
        'alerts': items,
        'alerts_unread_count': len(items),
    }