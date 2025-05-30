from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Fournisseur, CommandeFournisseur, LigneCommande, ReceptionAppro, PaiementFournisseur
from produits.models import Produit
from .services import recalc_commande_total, process_paiement, get_fournisseur_stats

class FournisseurTests(TestCase):
    def setUp(self):
        self.fournisseur = Fournisseur.objects.create(
            nom="Test Fournisseur",
            email="test@fournisseur.com"
        )

    def test_creation_fournisseur(self):
        self.assertEqual(str(self.fournisseur), "Test Fournisseur")
        self.assertTrue(self.fournisseur.actif)

    def test_email_unique(self):
        with self.assertRaises(ValidationError):
            Fournisseur.objects.create(
                nom="Autre Fournisseur",
                email="test@fournisseur.com"
            )

class CommandeTests(TestCase):
    def setUp(self):
        self.fournisseur = Fournisseur.objects.create(nom="Test Fournisseur")
        self.produit = Produit.objects.create(
            nom="Test Produit",
            prix_vente=Decimal('10.00')
        )
        self.commande = CommandeFournisseur.objects.create(
            fournisseur=self.fournisseur
        )
        self.ligne = LigneCommande.objects.create(
            commande=self.commande,
            produit=self.produit,
            quantite=5,
            prix_achat=Decimal('8.00')
        )

    def test_montant_total(self):
        self.assertEqual(self.commande.montant_total, Decimal('40.00'))

    def test_reception_partielle(self):
        ReceptionAppro.objects.create(
            commande=self.commande,
            produit=self.produit,
            quantite_livree=2
        )
        self.assertEqual(self.commande.statut, CommandeFournisseur.PARTIEL)

    def test_reception_complete(self):
        ReceptionAppro.objects.create(
            commande=self.commande,
            produit=self.produit,
            quantite_livree=5
        )
        self.assertEqual(self.commande.statut, CommandeFournisseur.RECEP)

    def test_paiement(self):
        paiement = process_paiement(self.commande, Decimal('20.00'))
        self.assertEqual(self.commande.total_paye, Decimal('20.00'))
        self.assertEqual(self.commande.reste_a_payer, Decimal('20.00'))

        # Test paiement excessif
        with self.assertRaises(ValidationError):
            process_paiement(self.commande, Decimal('30.00'))

class StatsTests(TestCase):
    def setUp(self):
        self.fournisseur = Fournisseur.objects.create(nom="Test Fournisseur")
        self.produit = Produit.objects.create(
            nom="Test Produit",
            prix_vente=Decimal('10.00')
        )
        self.commande = CommandeFournisseur.objects.create(
            fournisseur=self.fournisseur
        )
        self.ligne = LigneCommande.objects.create(
            commande=self.commande,
            produit=self.produit,
            quantite=5,
            prix_achat=Decimal('8.00')
        )

    def test_stats_fournisseur(self):
        stats = get_fournisseur_stats(self.fournisseur.id)
        self.assertEqual(stats['total_commandes'], Decimal('40.00'))
        self.assertEqual(stats['total_paye'], Decimal('0.00'))
        self.assertEqual(stats['nb_commandes'], 1)
        self.assertEqual(stats['nb_commandes_en_cours'], 1)
