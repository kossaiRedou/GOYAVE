from django.db import models
from produits.models import Produit
from stocks.models import MouvementStock
from decimal import Decimal

class Fournisseur(models.Model):
    nom     = models.CharField(max_length=255)
    contact = models.CharField(max_length=255, blank=True)
    email   = models.EmailField(blank=True)
    actif   = models.BooleanField(default=True)

    def __str__(self): return self.nom

class CommandeFournisseur(models.Model):
    EN_ATTENTE = 'EN_ATTENTE'
    PARTIEL    = 'PARTIEL'
    RECEP      = 'RECEPTIONNEE'
    STATUT_CHOICES = [(EN_ATTENTE,'En attente'),(PARTIEL,'Partiellement livré'), (RECEP, 'Réceptionnée')]

    fournisseur   = models.ForeignKey(Fournisseur, on_delete=models.PROTECT, related_name='commandes')
    date_commande = models.DateTimeField(auto_now_add=True)
    statut        = models.CharField(max_length=12, choices=STATUT_CHOICES, default=EN_ATTENTE)
    facture_pdf   = models.FileField(upload_to='factures/', blank=True, null=True)
    montant_total = models.DecimalField("Montant total", max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    
    def __str__(self): return f"Commande #{self.pk} - {self.fournisseur.nom}"

    def generate_pdf(self):
        from services.pdf import generate_commande_pdf
        
        # Refresh from DB to get latest paiements
        self.refresh_from_db()
        
        return generate_commande_pdf(self)



class LigneCommande(models.Model):
    commande   = models.ForeignKey(CommandeFournisseur, on_delete=models.CASCADE, related_name='lignes')
    produit    = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite   = models.PositiveIntegerField()
    prix_achat = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self): return f"{self.produit.nom} x{self.quantite}"

class ReceptionAppro(models.Model):
    commande        = models.ForeignKey(CommandeFournisseur, on_delete=models.PROTECT, related_name='receptions')
    produit         = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite_commandee = models.PositiveIntegerField(blank=True, null=True)
    quantite_livree = models.PositiveIntegerField()
    reference       = models.CharField(max_length=255, blank=True)
    date_reception  = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            MouvementStock.objects.create(
                produit=self.produit,
                type=MouvementStock.ENTREE,
                quantite=self.quantite_livree,
                reference=f"Réception #{self.pk} (Cmd #{self.commande.pk})"
            )
            total_cmd = sum(l.quantite for l in self.commande.lignes.all())
            total_rec = sum(r.quantite_livree for r in self.commande.receptions.all())
            self.commande.statut = (
                self.commande.RECEP if total_rec >= total_cmd else self.commande.PARTIEL
            )
            self.commande.save(update_fields=['statut'])

class PaiementFournisseur(models.Model):
    commande      = models.ForeignKey(CommandeFournisseur, on_delete=models.CASCADE, related_name='paiements')
    montant       = models.DecimalField(max_digits=12, decimal_places=2)
    date_paiement = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement {self.montant} le {self.date_paiement:%d/%m/%Y}"
