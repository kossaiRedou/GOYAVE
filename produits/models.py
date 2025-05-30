from django.db import models
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

class Monnaie(models.TextChoices):
    CFA = 'CFA', 'Franc CFA'
    USD = 'USD', 'Dollar US'
    FGN = 'FGN', 'Franc Guinéen'
    EUR = 'EUR', 'Euro'

class TauxChange(models.Model):
    devise_source = models.CharField('Devise source', max_length=3, choices=Monnaie.choices)
    devise_cible = models.CharField('Devise cible', max_length=3, choices=Monnaie.choices)
    taux = models.DecimalField('Taux', max_digits=10, decimal_places=4)
    date_maj = models.DateTimeField('Dernière mise à jour', auto_now=True)

    class Meta:
        verbose_name = 'Taux de change'
        verbose_name_plural = 'Taux de change'
        unique_together = ['devise_source', 'devise_cible']

    def __str__(self):
        return f"{self.devise_source} → {self.devise_cible}: {self.taux}"

class Produit(models.Model):
    nom = models.CharField('Nom', max_length=255)
    code = models.CharField('Code', max_length=50, unique=True)
    prix_vente = models.DecimalField('Prix de vente', max_digits=10, decimal_places=2)
    monnaie = models.CharField('Devise', max_length=3, choices=Monnaie.choices, default=Monnaie.CFA)
    image = models.ImageField('Image', upload_to='produits/', blank=True, null=True)
    stock = models.PositiveIntegerField('Stock actuel', default=0)
    stock_minimum = models.PositiveIntegerField('Stock minimum', default=0)
    date_expiration = models.DateField('Date d\'expiration', null=True, blank=True)
    alerte_expiration = models.BooleanField('Alerter avant expiration', default=True)
    delai_alerte_expiration = models.IntegerField(
        'Délai d\'alerte (jours)',
        default=90,
        help_text='Nombre de jours avant expiration pour déclencher l\'alerte'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        ordering = ['nom']
        indexes = [
            models.Index(fields=['date_expiration']),
            models.Index(fields=['stock']),
        ]

    def __str__(self):
        return f"{self.nom} ({self.code})"

    def get_absolute_url(self):
        return reverse('produits:detail', args=[self.pk])

    @property
    def est_expire(self):
        """Vérifie si le produit est expiré"""
        if self.date_expiration:
            return self.date_expiration <= timezone.now().date()
        return False

    @property
    def jours_avant_expiration(self):
        """Retourne le nombre de jours avant expiration"""
        if self.date_expiration:
            delta = self.date_expiration - timezone.now().date()
            return delta.days
        return None

    @property
    def necessite_alerte_expiration(self):
        """Vérifie si une alerte d'expiration doit être émise"""
        if not self.alerte_expiration or not self.date_expiration:
            return False
        jours_restants = self.jours_avant_expiration
        return jours_restants is not None and jours_restants <= self.delai_alerte_expiration

    def convertir_prix(self, devise_cible):
        """Convertit le prix dans la devise cible"""
        if self.monnaie == devise_cible:
            return self.prix_vente
        try:
            taux = TauxChange.objects.get(
                devise_source=self.monnaie,
                devise_cible=devise_cible
            )
            return self.prix_vente * taux.taux
        except TauxChange.DoesNotExist:
            return None