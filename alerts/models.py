from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Alert(models.Model):
    STOCK_LOW = 'STOCK_LOW'
    ALERT_TYPES = [
        (STOCK_LOW, 'Stock bas'),
        # à l’avenir d’autres types…
    ]

    type         = models.CharField(max_length=20, choices=ALERT_TYPES)
    message      = models.CharField(max_length=255)
    created_at   = models.DateTimeField(auto_now_add=True)
    is_read      = models.BooleanField(default=False)

    # relation générique vers n’importe quel objet (ici produit)
    target_ct    = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_id    = models.PositiveIntegerField()
    target       = GenericForeignKey('target_ct', 'target_id')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_type_display()}] {self.message}"
