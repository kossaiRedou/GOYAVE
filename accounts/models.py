from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class User(AbstractUser):
    ROLE_CHOICES = [
        ('MANAGER', 'Manager'),
        ('EMPLOYEE', 'Employé'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='EMPLOYEE')

    def is_manager(self):
        return self.role == 'MANAGER'

    def __str__(self):
        return self.get_full_name() or self.username

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['username']

class UserAction(models.Model):
    ACTION_TYPES = [
        ('CREATE', 'Création'),
        ('UPDATE', 'Modification'),
        ('DELETE', 'Suppression'),
        ('VIEW', 'Consultation'),
        ('LOGIN', 'Connexion'),
        ('LOGOUT', 'Déconnexion'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Pour lier l'action à n'importe quel modèle
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Description de l'action
    description = models.CharField(max_length=255)
    
    # Informations supplémentaires (IP, navigateur, etc.)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Action utilisateur"
        verbose_name_plural = "Actions utilisateurs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()} - {self.timestamp}"
