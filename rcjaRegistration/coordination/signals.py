from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
from django.dispatch import receiver

from .models import Coordinator

# Coordinator post-delete
# This signal is important for security as it updates the user's permissions after the deletion of a coordinator object
@receiver(post_delete, sender=Coordinator)
def Coordinator_post_delete(sender, instance, **kwargs):
    instance.user.updateUserPermissions()
