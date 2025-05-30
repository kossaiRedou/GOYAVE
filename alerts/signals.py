from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta
from django.db import models

from stocks.models import MouvementStock
from produits.models import Produit
from ventes.models import Vente, PaiementVente
from fournisseurs.models import CommandeFournisseur, PaiementFournisseur
from .models import Alert

@receiver(post_save, sender=MouvementStock)
def create_low_stock_alert(sender, instance, created, **kwargs):
    if not created or instance.type != MouvementStock.SORTIE:
        return

    produit = instance.produit
    # après mise à jour du stock dans MouvementStock.save()
    seuil = getattr(settings, 'LOW_STOCK_THRESHOLD', 5)
    if produit.stock <= seuil:
        ct = ContentType.objects.get_for_model(produit)
        # éviter les doublons non lus
        exists = Alert.objects.filter(
            type=Alert.STOCK_LOW,
            target_ct=ct,
            target_id=produit.pk,
            is_read=False
        ).exists()
        if not exists:
            Alert.objects.create(
                type=Alert.STOCK_LOW,
                level=Alert.LEVEL_WARNING,
                message=f"Stock bas pour « {produit.nom} » ({produit.code}) : {produit.stock}",
                target_ct=ct,
                target_id=produit.pk
            )

@receiver(post_save, sender=Produit)
def check_product_expiration(sender, instance, **kwargs):
    if not instance.date_expiration or not instance.alerte_expiration:
        return

    days_before = instance.delai_alerte_expiration
    warning_date = timezone.now().date() + timedelta(days=days_before)
    
    if instance.date_expiration <= warning_date:
        ct = ContentType.objects.get_for_model(instance)
        # Éviter les doublons non lus
        exists = Alert.objects.filter(
            type=Alert.EXPIRATION,
            target_ct=ct,
            target_id=instance.pk,
            is_read=False
        ).exists()
        
        if not exists:
            jours_restants = (instance.date_expiration - timezone.now().date()).days
            Alert.objects.create(
                type=Alert.EXPIRATION,
                level=Alert.LEVEL_DANGER,
                message=f"Le produit « {instance.nom} » ({instance.code}) expire dans {jours_restants} jours",
                target_ct=ct,
                target_id=instance.pk,
                expires_at=timezone.make_aware(timezone.datetime.combine(instance.date_expiration, timezone.datetime.min.time()))
            )

@receiver(post_save, sender=Vente)
def check_payment_delay_client(sender, instance, created, **kwargs):
    # Vérifier si la vente est entièrement payée
    total_paye = instance.paiements.aggregate(total=models.Sum('montant'))['total'] or 0
    if total_paye >= instance.montant_total:
        return

    delay_days = getattr(settings, 'PAYMENT_DELAY_WARNING_DAYS', 1)
    warning_date = timezone.now() - timedelta(days=delay_days)
    
    if instance.date <= warning_date:
        ct = ContentType.objects.get_for_model(instance)
        exists = Alert.objects.filter(
            type=Alert.PAYMENT_LATE_CLIENT,
            target_ct=ct,
            target_id=instance.pk,
            is_read=False
        ).exists()
        
        if not exists:
            jours_retard = (timezone.now() - instance.date).days
            Alert.objects.create(
                type=Alert.PAYMENT_LATE_CLIENT,
                level=Alert.LEVEL_DANGER,
                message=f"Retard de paiement de {jours_retard} jours pour la vente #{instance.pk} ({instance.client})",
                target_ct=ct,
                target_id=instance.pk
            )

@receiver(post_save, sender=CommandeFournisseur)
def check_pending_orders(sender, instance, **kwargs):
    if instance.statut != CommandeFournisseur.EN_ATTENTE:
        return

    days_pending = getattr(settings, 'ORDER_PENDING_WARNING_DAYS', 7)
    warning_date = timezone.now() - timedelta(days=days_pending)
    
    if instance.date_commande <= warning_date:
        ct = ContentType.objects.get_for_model(instance)
        exists = Alert.objects.filter(
            type=Alert.ORDER_PENDING,
            target_ct=ct,
            target_id=instance.pk,
            is_read=False
        ).exists()
        
        if not exists:
            jours_attente = (timezone.now() - instance.date_commande).days
            Alert.objects.create(
                type=Alert.ORDER_PENDING,
                level=Alert.LEVEL_INFO,
                message=f"Commande #{instance.pk} ({instance.fournisseur.nom}) en attente depuis {jours_attente} jours",
                target_ct=ct,
                target_id=instance.pk
            )
