from decimal import Decimal
from django.db.models import Sum, F
from .models import CommandeFournisseur, PaiementFournisseur

def recalc_commande_total(cmd: CommandeFournisseur):
    """Recalcule le montant total d'une commande"""
    total = sum(
        ligne.quantite * ligne.prix_achat
        for ligne in cmd.lignes.all()
    ) or Decimal('0.00')
    cmd.montant_total = total
    cmd.save(update_fields=['montant_total'])

def process_paiement(commande: CommandeFournisseur, montant: Decimal) -> PaiementFournisseur:
    """
    Traite un paiement pour une commande
    Retourne le paiement créé
    Lève une ValidationError si le montant est invalide
    """
    from django.core.exceptions import ValidationError
    
    # Vérifier que le montant est positif
    if montant <= 0:
        raise ValidationError("Le montant du paiement doit être supérieur à 0")
    
    # Vérifier que le montant ne dépasse pas le reste à payer
    if montant > commande.reste_a_payer:
        raise ValidationError(
            f"Le montant du paiement ({montant}) ne peut pas dépasser "
            f"le reste à payer ({commande.reste_a_payer})"
        )
    
    # Créer le paiement
    return PaiementFournisseur.objects.create(
        commande=commande,
        montant=montant
    )

def get_fournisseur_stats(fournisseur_id: int) -> dict:
    """
    Retourne des statistiques pour un fournisseur
    """
    from .models import Fournisseur
    fournisseur = Fournisseur.objects.get(pk=fournisseur_id)
    
    commandes = fournisseur.commandes.all()
    commandes_stats = commandes.aggregate(
        total_commandes=Sum('montant_total'),
        total_paye=Sum('paiements__montant'),
        nb_commandes=Count('id'),
        nb_commandes_en_cours=Count('id', filter=~Q(statut=CommandeFournisseur.RECEP))
    )
    
    return {
        'fournisseur': fournisseur,
        'total_commandes': commandes_stats['total_commandes'] or Decimal('0.00'),
        'total_paye': commandes_stats['total_paye'] or Decimal('0.00'),
        'reste_a_payer': (commandes_stats['total_commandes'] or Decimal('0.00')) - 
                        (commandes_stats['total_paye'] or Decimal('0.00')),
        'nb_commandes': commandes_stats['nb_commandes'],
        'nb_commandes_en_cours': commandes_stats['nb_commandes_en_cours']
    }
