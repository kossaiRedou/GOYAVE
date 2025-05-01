from django.db import models
from django.urls import reverse

class Monnaie(models.TextChoices):
    CFA = 'CFA', 'Franc CFA'
    USD = 'USD', 'Dollar US'
    FGN = 'FGN', 'Franc Guinéen'

class Produit(models.Model):
    nom         = models.CharField('Nom', max_length=255)
    code        = models.CharField('Code', max_length=50, unique=True)
    prix_vente  = models.DecimalField('Prix de vente', max_digits=10, decimal_places=2)
    monnaie     = models.CharField('Devise', max_length=3, choices=Monnaie.choices, default=Monnaie.CFA)
    image       = models.ImageField('Image', upload_to='produits/', blank=True, null=True)
    stock       = models.PositiveIntegerField('Stock initial', default=0)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.code})"

    def get_absolute_url(self):
        return reverse('produits:detail', args=[self.pk])