from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta
from django.db import models, transaction
from django.db.models import F
import logging

logger = logging.getLogger(__name__)

from stocks.models import MouvementStock
from produits.models import Produit
from ventes.models import Vente, PaiementVente
from fournisseurs.models import CommandeFournisseur, PaiementFournisseur, ReceptionAppro
from .models import Alert

def check_and_mark_stock_alerts(produit):
    """Vérifie et marque les alertes de stock comme lues si nécessaire"""
    seuil = getattr(settings, 'LOW_STOCK_THRESHOLD', 5)
    if produit.stock > seuil:
        ct = ContentType.objects.get_for_model(produit)
        count = Alert.objects.filter(
            type=Alert.STOCK_LOW,
            target_ct=ct,
            target_id=produit.pk,
            is_read=False
        ).update(is_read=True)
        if count > 0:
            logger.info(f"{count} alerte(s) marquée(s) comme lue(s) pour {produit.nom} (stock: {produit.stock})")
        return count
    return 0

@receiver(post_save, sender=MouvementStock)
def handle_stock_alerts(sender, instance, **kwargs):
    """Gère les alertes de stock (création et nettoyage) lors des mouvements"""
    # Recharger le produit pour avoir la valeur la plus récente du stock
    produit = Produit.objects.get(pk=instance.produit.pk)
    seuil = getattr(settings, 'LOW_STOCK_THRESHOLD', 5)
    ct = ContentType.objects.get_for_model(produit)

    logger.info(f"Vérification du stock pour {produit.nom} - Stock actuel: {produit.stock}, Seuil: {seuil}, Type: {instance.type}")

    # Si c'est une sortie et que le stock est bas, créer une alerte si nécessaire
    if instance.type == MouvementStock.SORTIE and produit.stock <= seuil:
        alert, created = Alert.objects.get_or_create(
            type=Alert.STOCK_LOW,
            target_ct=ct,
            target_id=produit.pk,
            is_read=False,
            defaults={
                'level': Alert.LEVEL_WARNING,
                'message': f"Stock bas pour « {produit.nom} » ({produit.code}) : {produit.stock}"
            }
        )
        if created:
            logger.info(f"Nouvelle alerte créée pour {produit.nom}")
    
    # Pour toute entrée de stock, vérifier si on peut marquer les alertes comme lues
    elif instance.type == MouvementStock.ENTREE:
        transaction.on_commit(lambda: check_and_mark_stock_alerts(produit))

@receiver(post_save, sender=ReceptionAppro)
def handle_reception_stock(sender, instance, created, **kwargs):
    """Vérifie les alertes après une réception de commande"""
    if created:  # Seulement pour les nouvelles réceptions
        # On attend que la transaction soit terminée pour vérifier le stock
        transaction.on_commit(lambda: check_and_mark_stock_alerts(instance.produit))

@receiver(post_save, sender=Produit)
def check_product_expiration(sender, instance, **kwargs):
    if not instance.date_expiration or not instance.alerte_expiration:
        return

    days_before = instance.delai_alerte_expiration
    warning_date = timezone.now().date() + timedelta(days=days_before)
    
    if instance.date_expiration <= warning_date:
        ct = ContentType.objects.get_for_model(instance)
        Alert.objects.get_or_create(
            type=Alert.EXPIRATION,
            target_ct=ct,
            target_id=instance.pk,
            is_read=False,
            defaults={
                'level': Alert.LEVEL_DANGER,
                'message': f"Le produit « {instance.nom} » ({instance.code}) expire dans {(instance.date_expiration - timezone.now().date()).days} jours",
                'expires_at': timezone.make_aware(timezone.datetime.combine(instance.date_expiration, timezone.datetime.min.time()))
            }
        )

@receiver(post_save, sender=PaiementVente)
def check_payment_alerts(sender, instance, **kwargs):
    """Vérifie et nettoie les alertes de paiement pour la vente concernée"""
    vente = instance.vente
    total_paye = vente.paiements.aggregate(total=models.Sum('montant'))['total'] or 0
    
    if total_paye >= vente.montant_total:
        # Si la vente est entièrement payée, marquer les alertes comme lues
        ct = ContentType.objects.get_for_model(vente)
        Alert.objects.filter(
            type=Alert.PAYMENT_LATE_CLIENT,
            target_ct=ct,
            target_id=vente.pk,
            is_read=False
        ).update(is_read=True)

@receiver(post_save, sender=CommandeFournisseur)
def check_order_alerts(sender, instance, **kwargs):
    """Vérifie et nettoie les alertes de commande en attente"""
    if instance.statut != CommandeFournisseur.EN_ATTENTE:
        ct = ContentType.objects.get_for_model(instance)
        Alert.objects.filter(
            type=Alert.ORDER_PENDING,
            target_ct=ct,
            target_id=instance.pk,
            is_read=False
        ).update(is_read=True)
