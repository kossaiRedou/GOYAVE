# ventes/services.py

from decimal import Decimal
from django.db.models import Sum
from stocks.models import MouvementStock

def recalc_vente_et_stock(vente):
    """
    1) Rétablit le stock en inversant les anciens mouvements SORTIE
    2) Supprime ces anciens mouvements
    3) Recalcule les montant_ligne (via VenteDetail.save())
    4) Crée de nouveaux mouvements SORTIE
    5) Recalcule montant_total et reste_du
    """
    vente.refresh_from_db()
    ref = f"Vente #{vente.pk}"

    # 1) Inversion des anciens mouvements
    old_ms = list(MouvementStock.objects.filter(reference=ref))
    for ms in old_ms:
        # si on avait sorti du stock, on le remet
        if ms.type == MouvementStock.SORTIE:
            ms.produit.stock += ms.quantite
        else:
            ms.produit.stock -= ms.quantite
        ms.produit.save(update_fields=['stock'])

    # 2) Suppression des anciens mouvements
    MouvementStock.objects.filter(reference=ref).delete()

    # 3 & 4) Enregistrement des lignes (save() recalcule montant_ligne)
    #      puis création des nouvelles sorties
    for ligne in vente.lignes.all():
        ligne.save()  # mise à jour de montant_ligne
        MouvementStock.objects.create(
            produit=ligne.produit,
            type=MouvementStock.SORTIE,
            quantite=ligne.quantite,
            reference=ref
        )

    # 5) Mise à jour des totaux
    total = vente.lignes.aggregate(s=Sum('montant_ligne'))['s'] or Decimal('0.00')
    deja_paye = vente.paiements.aggregate(s=Sum('montant'))['s'] or Decimal('0.00')
    vente.montant_total = total
    vente.reste_du      = max(Decimal('0.00'), total - deja_paye)
    vente.save(update_fields=['montant_total', 'reste_du'])
