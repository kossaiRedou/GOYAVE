from django.db import models
from produits.models import Produit

class MouvementStock(models.Model):
    ENTREE = 'ENTREE'
    SORTIE = 'SORTIE'
    TYPE_CHOICES = [
        (ENTREE, 'Entrée'),
        (SORTIE, 'Sortie'),
    ]

    produit    = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name='mouvements')
    type       = models.CharField('Type de mouvement', max_length=6, choices=TYPE_CHOICES)
    quantite   = models.PositiveIntegerField('Quantité')
    date       = models.DateTimeField('Date du mouvement', auto_now_add=True)
    reference  = models.CharField('Référence', max_length=100, blank=True,
                                  help_text='Ex: commande fournisseur ou vente')

    class Meta:
        verbose_name = 'Mouvement de stock'
        verbose_name_plural = 'Mouvements de stock'
        ordering = ['-date']

    def save(self, *args, **kwargs):
        # Ajuste le stock du produit
        if self.pk is None:
            if self.type == self.ENTREE:
                self.produit.stock += self.quantite
            else:
                self.produit.stock -= self.quantite
            self.produit.save(update_fields=['stock'])
        super().save(*args, **kwargs)