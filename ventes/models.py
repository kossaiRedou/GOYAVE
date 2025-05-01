from django.db import models
from django.urls import reverse
from clients.models import Client
from produits.models import Produit


class Vente(models.Model):
    client        = models.ForeignKey(Client, verbose_name='Client', on_delete=models.PROTECT)
    date          = models.DateTimeField('Date de vente', auto_now_add=True)
    montant_total = models.DecimalField('Montant total', max_digits=12, decimal_places=2, default=0)
    reste_du      = models.DecimalField('Reste dû', max_digits=12, decimal_places=2, default=0)
    facture_pdf   = models.FileField(
        'Facture PDF',
        upload_to='factures/',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Vente'
        verbose_name_plural = 'Ventes'
        ordering = ['-date']

    
    def generate_facture(self):
        """
        Recharge l'état de la vente, génère la facture PDF nommée
        avec le format vente_<pk>_<YYYYMMDD_HHMMSS>.pdf,
        supprime l'ancienne si elle existe, et stocke le nouveau chemin.
        """
        from services.pdf import generate_vente_pdf

        # Refresh from DB to get latest paiements
        self.refresh_from_db()
        
        return generate_vente_pdf(self)
    
    def __str__(self):
        return f"Vente #{self.pk} - {self.client.nom}"

    def get_absolute_url(self):
        return reverse('ventes:detail', args=[self.pk])


class VenteDetail(models.Model):
    vente           = models.ForeignKey(Vente, related_name='lignes', on_delete=models.CASCADE)
    produit         = models.ForeignKey(Produit, verbose_name='Produit', on_delete=models.PROTECT)
    quantite        = models.PositiveIntegerField('Quantité', default=1)
    prix_unitaire   = models.DecimalField('Prix unitaire', max_digits=10, decimal_places=2)
    montant_ligne   = models.DecimalField('Montant ligne', max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Ligne de vente'
        verbose_name_plural = 'Lignes de vente'

    def __str__(self):
        return f"{self.produit.nom} x{self.quantite}"

class PaiementVente(models.Model):
    vente           = models.ForeignKey(Vente, related_name='paiements', on_delete=models.CASCADE)
    date_paiement   = models.DateTimeField('Date paiement', auto_now_add=True)
    montant         = models.DecimalField('Montant payé', max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'

    def __str__(self):
        return f"Paiement {self.montant} le {self.date_paiement:%d/%m/%Y}"