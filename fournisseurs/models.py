from django.db import models, transaction
from produits.models import Produit
from stocks.models import MouvementStock
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.models import F, Sum

class Fournisseur(models.Model):
    nom     = models.CharField(max_length=255)
    contact = models.CharField(max_length=255, blank=True)
    email   = models.EmailField(blank=True)
    actif   = models.BooleanField(default=True)

    class Meta:
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom']),
            models.Index(fields=['email'])
        ]

    def __str__(self): 
        return self.nom

    def clean(self):
        if not self.nom:
            raise ValidationError({'nom': "Le nom du fournisseur est obligatoire"})
        if self.email and Fournisseur.objects.exclude(pk=self.pk).filter(email=self.email).exists():
            raise ValidationError({'email': "Cette adresse email est déjà utilisée"})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def total_commandes(self):
        return self.commandes.aggregate(
            total=Sum('montant_total')
        )['total'] or Decimal('0.00')

    @property
    def total_non_paye(self):
        commandes = self.commandes.annotate(
            total_paye=Sum('paiements__montant')
        ).aggregate(
            total_du=Sum(F('montant_total') - F('total_paye'))
        )
        return commandes['total_du'] or Decimal('0.00')


class CommandeFournisseur(models.Model):
    EN_ATTENTE = 'EN_ATTENTE'
    PARTIEL    = 'PARTIEL'
    RECEP      = 'RECEPTIONNEE'
    STATUT_CHOICES = [
        (EN_ATTENTE, 'En attente'),
        (PARTIEL, 'Partiellement livré'),
        (RECEP, 'Réceptionnée')
    ]

    fournisseur   = models.ForeignKey(Fournisseur, on_delete=models.PROTECT, related_name='commandes')
    date_commande = models.DateTimeField(auto_now_add=True)
    statut        = models.CharField(max_length=12, choices=STATUT_CHOICES, default=EN_ATTENTE)
    facture_pdf   = models.FileField(upload_to='factures/', blank=True, null=True)
    montant_total = models.DecimalField("Montant total", max_digits=12, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        ordering = ['-date_commande']
        indexes = [
            models.Index(fields=['fournisseur', 'date_commande']),
            models.Index(fields=['statut'])
        ]

    def __str__(self): 
        return f"Commande #{self.pk} - {self.fournisseur.nom if self.fournisseur else 'Nouveau'}"

    def clean(self):
        if self.fournisseur_id and not self.fournisseur.actif:
            raise ValidationError({
                'fournisseur': "Ce fournisseur n'est plus actif"
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def generate_pdf(self):
        from services.pdf import generate_commande_pdf
        self.refresh_from_db()
        return generate_commande_pdf(self)

    @property
    def total_paye(self):
        return self.paiements.aggregate(
            total=Sum('montant')
        )['total'] or Decimal('0.00')

    @property
    def reste_a_payer(self):
        return self.montant_total - self.total_paye

    @property
    def est_entierement_payee(self):
        return self.reste_a_payer <= Decimal('0.00')

    @property
    def total_recu(self):
        return self.receptions.aggregate(
            total=Sum('quantite_livree')
        )['total'] or 0

    def update_statut(self):
        total_cmd = sum(l.quantite for l in self.lignes.all())
        if self.total_recu >= total_cmd:
            self.statut = self.RECEP
        elif self.total_recu > 0:
            self.statut = self.PARTIEL
        else:
            self.statut = self.EN_ATTENTE
        self.save(update_fields=['statut'])


class LigneCommande(models.Model):
    commande   = models.ForeignKey(CommandeFournisseur, on_delete=models.CASCADE, related_name='lignes')
    produit    = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite   = models.PositiveIntegerField()
    prix_achat = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ['commande', 'produit']
        ordering = ['produit__nom']

    def __str__(self): 
        return f"{self.produit.nom} x{self.quantite}"

    def clean(self):
        if self.quantite <= 0:
            raise ValidationError({'quantite': "La quantité doit être supérieure à 0"})
        if self.prix_achat <= 0:
            raise ValidationError({'prix_achat': "Le prix d'achat doit être supérieur à 0"})
        if self.pk is None and self.commande_id is not None:
            if LigneCommande.objects.filter(
                commande=self.commande, 
                produit=self.produit
            ).exists():
                raise ValidationError({'produit': "Ce produit est déjà dans la commande"})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        from .services import recalc_commande_total
        recalc_commande_total(self.commande)

    @property
    def montant_total(self):
        return self.quantite * self.prix_achat

    @property
    def quantite_recue(self):
        return self.commande.receptions.filter(
            produit=self.produit
        ).aggregate(
            total=Sum('quantite_livree')
        )['total'] or 0

    @property
    def reste_a_livrer(self):
        return self.quantite - self.quantite_recue


class ReceptionAppro(models.Model):
    commande        = models.ForeignKey(CommandeFournisseur, on_delete=models.PROTECT, related_name='receptions')
    produit         = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite_commandee = models.PositiveIntegerField(blank=True, null=True)
    quantite_livree = models.PositiveIntegerField()
    prix_achat      = models.DecimalField(max_digits=10, decimal_places=2)
    reference       = models.CharField(max_length=255, blank=True)
    date_reception  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Réception #{self.pk} - {self.produit.nom} x{self.quantite_livree}"

    def clean(self):
        if self.quantite_livree <= 0:
            raise ValidationError({'quantite_livree': "La quantité livrée doit être supérieure à 0"})
        ligne_commande = self.commande.lignes.filter(produit=self.produit).first()
        if not ligne_commande:
            raise ValidationError({'produit': "Ce produit n'est pas dans la commande d'origine"})
        total_recu = self.commande.receptions.exclude(pk=self.pk).filter(
            produit=self.produit
        ).aggregate(total=Sum('quantite_livree'))['total'] or 0
        if total_recu + self.quantite_livree > ligne_commande.quantite:
            raise ValidationError({
                'quantite_livree': (
                    f"La quantité totale reçue ({total_recu + self.quantite_livree}) "
                    f"ne peut pas dépasser la quantité commandée ({ligne_commande.quantite})"
                )
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None

        with transaction.atomic():
            super().save(*args, **kwargs)

            if is_new:
                MouvementStock.objects.create(
                    produit=self.produit,
                    type=MouvementStock.ENTREE,
                    quantite=self.quantite_livree,
                    reference=f"Réception #{self.pk} (Cmd #{self.commande.pk})"
                )

            if self.prix_achat != self.produit.prix_achat:
                self.produit.prix_achat = self.prix_achat
                self.produit.save(update_fields=['prix_achat'])

            total_cmd = sum(l.quantite for l in self.commande.lignes.all())
            total_rec = sum(r.quantite_livree for r in self.commande.receptions.all())

            self.commande.statut = (
                self.commande.RECEP if total_rec >= total_cmd
                else self.commande.PARTIEL
            )
            self.commande.save(update_fields=['statut'])


class PaiementFournisseur(models.Model):
    commande      = models.ForeignKey(CommandeFournisseur, on_delete=models.CASCADE, related_name='paiements')
    montant       = models.DecimalField(max_digits=12, decimal_places=2)
    date_paiement = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement {self.montant} le {self.date_paiement:%d/%m/%Y}"
