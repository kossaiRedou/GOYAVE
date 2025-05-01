from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from stocks.models import MouvementStock
from alerts.models import Alert

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
                message=f"Stock bas pour « {produit.nom} » : {produit.stock}",
                target_ct=ct,
                target_id=produit.pk
            )
