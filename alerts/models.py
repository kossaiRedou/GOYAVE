from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta

class Alert(models.Model):
    # Types d'alertes
    STOCK_LOW = 'STOCK_LOW'
    EXPIRATION = 'EXPIRATION'
    PAYMENT_LATE_CLIENT = 'PAYMENT_LATE_CLIENT'
    PAYMENT_LATE_SUPPLIER = 'PAYMENT_LATE_SUPPLIER'
    ORDER_PENDING = 'ORDER_PENDING'

    ALERT_TYPES = [
        (STOCK_LOW, 'Stock bas'),
        (EXPIRATION, 'Produit proche de la date d\'expiration'),
        (PAYMENT_LATE_CLIENT, 'Retard de paiement client'),
        (PAYMENT_LATE_SUPPLIER, 'Retard de paiement fournisseur'),
        (ORDER_PENDING, 'Commande en attente'),
    ]

    # Niveaux d'urgence
    LEVEL_INFO = 'INFO'
    LEVEL_WARNING = 'WARNING'
    LEVEL_DANGER = 'DANGER'

    ALERT_LEVELS = [
        (LEVEL_INFO, 'Information'),
        (LEVEL_WARNING, 'Avertissement'),
        (LEVEL_DANGER, 'Urgent'),
    ]

    # Couleurs par type d'alerte
    ALERT_COLORS = {
        STOCK_LOW: 'warning',
        EXPIRATION: 'danger',
        PAYMENT_LATE_CLIENT: 'danger',
        PAYMENT_LATE_SUPPLIER: 'danger',
        ORDER_PENDING: 'info',
    }

    type = models.CharField(max_length=30, choices=ALERT_TYPES)
    level = models.CharField(max_length=10, choices=ALERT_LEVELS, default=LEVEL_WARNING)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Relation générique vers l'objet concerné
    target_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_id = models.PositiveIntegerField()
    target = GenericForeignKey('target_ct', 'target_id')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['type', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.get_type_display()}] {self.message}"

    @property
    def color(self):
        """Retourne la classe Bootstrap correspondant au type d'alerte"""
        return self.ALERT_COLORS.get(self.type, 'secondary')

    @property
    def age(self):
        """Retourne le temps écoulé depuis la création de l'alerte"""
        return timezone.now() - self.created_at

    @property
    def is_expired(self):
        """Vérifie si l'alerte a expiré"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def mark_as_read(self):
        """Marque l'alerte comme lue"""
        self.is_read = True
        self.save(update_fields=['is_read'])

    def mark_as_unread(self):
        """Marque l'alerte comme non lue"""
        self.is_read = False
        self.save(update_fields=['is_read'])

    @classmethod
    def get_unread_count(cls):
        """Retourne le nombre d'alertes non lues"""
        return cls.objects.filter(is_read=False).count()

    @classmethod
    def cleanup_old_alerts(cls, days=30):
        """Supprime les alertes plus anciennes que le nombre de jours spécifié"""
        threshold = timezone.now() - timedelta(days=days)
        cls.objects.filter(created_at__lt=threshold).delete()
