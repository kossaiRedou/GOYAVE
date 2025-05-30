from django.db import models
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

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
    prix_achat = models.DecimalField('Prix d\'achat', max_digits=10, decimal_places=2)
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

    @property
    def pourcentage_marge(self):
        """Calcule le pourcentage de marge"""
        if self.prix_vente and self.prix_achat and self.prix_achat > 0:
            return ((self.prix_vente - self.prix_achat) / self.prix_achat) * 100
        return None

    @property
    def marge(self):
        """Calcule la marge entre le prix de vente et le prix d'achat"""
        if self.prix_vente and self.prix_achat:
            return self.prix_vente - self.prix_achat
        return None

    def clean(self):
        super().clean()
        if self.prix_achat is not None and self.prix_achat < 0:
            raise ValidationError({'prix_achat': "Le prix d'achat ne peut pas être négatif"})
        if self.prix_vente is not None and self.prix_vente < 0:
            raise ValidationError({'prix_vente': "Le prix de vente ne peut pas être négatif"})
        if self.prix_achat is not None and self.prix_vente is not None and self.prix_achat > self.prix_vente:
            raise ValidationError("Le prix d'achat ne peut pas être supérieur au prix de vente")