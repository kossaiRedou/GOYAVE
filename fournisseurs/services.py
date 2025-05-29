from decimal import Decimal
from .models import CommandeFournisseur

def recalc_commande_total(cmd: CommandeFournisseur):
    total = sum(
        ligne.quantite * ligne.prix_achat
        for ligne in cmd.lignes.all()
    ) or Decimal('0.00')
    cmd.montant_total = total
    cmd.save(update_fields=['montant_total'])
