from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Sum, F
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta

from produits.models import Produit
from ventes.models import Vente, PaiementVente
from fournisseurs.models import CommandeFournisseur, PaiementFournisseur
from .models import Alert

def alerts(request):
    """
    Context processor: fournit les alertes non lues et leur compte pour la navbar
    """
    if not request.user.is_authenticated:
        return {'alerts': [], 'alerts_unread_count': 0}

    # Récupérer toutes les alertes non lues
    alerts = Alert.objects.filter(is_read=False).order_by('-created_at')

    # Nettoyer les alertes expirées
    Alert.cleanup_old_alerts()

    # Vérifier les nouveaux problèmes potentiels
    check_stock_levels()
    check_product_expiration()
    check_payment_delays()
    check_pending_orders()

    return {
        'alerts': alerts[:5],  # 5 dernières alertes pour la navbar
        'alerts_unread_count': alerts.count(),
    }

def check_stock_levels():
    """Vérifie les niveaux de stock bas et nettoie les alertes obsolètes"""
    seuil = getattr(settings, 'LOW_STOCK_THRESHOLD', 5)
    
    # 1. Créer des alertes pour les stocks bas
    produits_bas = Produit.objects.filter(stock__lte=seuil)
    for produit in produits_bas:
        Alert.objects.get_or_create(
            type=Alert.STOCK_LOW,
            target_ct=ContentType.objects.get_for_model(produit),
            target_id=produit.pk,
            is_read=False,
            defaults={
                'level': Alert.LEVEL_WARNING,
                'message': f"Stock bas pour « {produit.nom} » ({produit.code}) : {produit.stock}"
            }
        )
    
    # 2. Marquer comme lues les alertes des produits dont le stock est redevenu suffisant
    ct_produit = ContentType.objects.get_for_model(Produit)
    Alert.objects.filter(
        type=Alert.STOCK_LOW,
        is_read=False,
        target_ct=ct_produit,
        target_id__in=Produit.objects.filter(stock__gt=seuil).values_list('id', flat=True)
    ).update(is_read=True)

def check_product_expiration():
    """Vérifie les produits proche de la date d'expiration"""
    produits_expiration = Produit.objects.filter(
        date_expiration__isnull=False,
        alerte_expiration=True
    ).exclude(date_expiration__lt=timezone.now().date())
    
    for produit in produits_expiration:
        if produit.necessite_alerte_expiration:
            Alert.objects.get_or_create(
                type=Alert.EXPIRATION,
                target_ct=ContentType.objects.get_for_model(produit),
                target_id=produit.pk,
                is_read=False,
                defaults={
                    'level': Alert.LEVEL_DANGER,
                    'message': f"Le produit « {produit.nom} » ({produit.code}) expire dans {produit.jours_avant_expiration} jours",
                    'expires_at': timezone.make_aware(timezone.datetime.combine(produit.date_expiration, timezone.datetime.min.time()))
                }
            )

def check_payment_delays():
    """Vérifie les retards de paiement"""
    delay_days = getattr(settings, 'PAYMENT_DELAY_WARNING_DAYS', 1)
    warning_date = timezone.now() - timedelta(days=delay_days)
    
    # Ventes avec paiement en retard
    ventes_retard = Vente.objects.annotate(
        total_paye=Sum('paiements__montant')
    ).filter(
        date__lt=warning_date,
        total_paye__lt=F('montant_total')
    )
    
    for vente in ventes_retard:
        jours_retard = (timezone.now() - vente.date).days
        Alert.objects.get_or_create(
            type=Alert.PAYMENT_LATE_CLIENT,
            target_ct=ContentType.objects.get_for_model(vente),
            target_id=vente.pk,
            is_read=False,
            defaults={
                'level': Alert.LEVEL_DANGER,
                'message': f"Retard de paiement de {jours_retard} jours pour la vente #{vente.pk} ({vente.client})"
            }
        )

def check_pending_orders():
    """Vérifie les commandes en attente depuis longtemps"""
    days_pending = getattr(settings, 'ORDER_PENDING_WARNING_DAYS', 7)
    warning_date = timezone.now() - timedelta(days=days_pending)
    
    commandes_attente = CommandeFournisseur.objects.filter(
        statut=CommandeFournisseur.EN_ATTENTE,
        date_commande__lte=warning_date
    )
    
    for commande in commandes_attente:
        jours_attente = (timezone.now() - commande.date_commande).days
        Alert.objects.get_or_create(
            type=Alert.ORDER_PENDING,
            target_ct=ContentType.objects.get_for_model(commande),
            target_id=commande.pk,
            is_read=False,
            defaults={
                'level': Alert.LEVEL_INFO,
                'message': f"Commande #{commande.pk} ({commande.fournisseur.nom}) en attente depuis {jours_attente} jours"
            }
        )