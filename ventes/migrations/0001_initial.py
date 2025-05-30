# Generated by Django 5.2 on 2025-05-01 18:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clients', '0001_initial'),
        ('produits', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Date de vente')),
                ('montant_total', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Montant total')),
                ('reste_du', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Reste dû')),
                ('facture_pdf', models.FileField(blank=True, null=True, upload_to='factures/', verbose_name='Facture PDF')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='clients.client', verbose_name='Client')),
            ],
            options={
                'verbose_name': 'Vente',
                'verbose_name_plural': 'Ventes',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='PaiementVente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_paiement', models.DateTimeField(auto_now_add=True, verbose_name='Date paiement')),
                ('montant', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Montant payé')),
                ('vente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='paiements', to='ventes.vente')),
            ],
            options={
                'verbose_name': 'Paiement',
                'verbose_name_plural': 'Paiements',
            },
        ),
        migrations.CreateModel(
            name='VenteDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantite', models.PositiveIntegerField(default=1, verbose_name='Quantité')),
                ('prix_unitaire', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Prix unitaire')),
                ('montant_ligne', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Montant ligne')),
                ('produit', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='produits.produit', verbose_name='Produit')),
                ('vente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lignes', to='ventes.vente')),
            ],
            options={
                'verbose_name': 'Ligne de vente',
                'verbose_name_plural': 'Lignes de vente',
            },
        ),
    ]
