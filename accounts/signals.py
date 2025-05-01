import os
from django.apps import apps
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission, Group
from django.conf import settings
from .models import User

@receiver(post_migrate)
def create_user_groups(sender, **kwargs):
    if sender.name != 'accounts':
        return
    # Create groups
    managers, _ = Group.objects.get_or_create(name='Managers')
    employees, _ = Group.objects.get_or_create(name='Employees')
    # Assign permissions
    all_perms = Permission.objects.all()
    managers.permissions.set(all_perms)
    # Employees get only non-auth, non-account perms
    biz_perms = Permission.objects.exclude(content_type__app_label__in=['auth', 'accounts'])
    employees.permissions.set(biz_perms)

@receiver(post_save, sender=User)
def assign_user_group(sender, instance, created, **kwargs):
    if not created:
        return
    grp_name = 'Managers' if instance.role == 'MANAGER' else 'Employees'
    group = Group.objects.get(name=grp_name)
    instance.groups.add(group)
