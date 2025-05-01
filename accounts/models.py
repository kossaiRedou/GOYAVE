from django.contrib.auth.models import AbstractUser
from django.db import models

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
