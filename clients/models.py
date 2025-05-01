from django.db import models


class Client(models.Model):
    nom       = models.CharField("Nom", max_length=255)
    email     = models.EmailField("E-mail", unique=True)
    telephone = models.CharField("Téléphone", max_length=20, blank=True, null=True)
    adresse   = models.TextField("Adresse", blank=True)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    updated_at = models.DateTimeField("Mis à jour le", auto_now=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['nom']

    def __str__(self):
        return self.nom
