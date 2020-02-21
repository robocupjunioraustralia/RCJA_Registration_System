from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
from django.dispatch import receiver

from .models import Profile
from django.contrib.auth.models import User

# Create user profile on user save
@receiver(post_save, sender=User)
def GroupMembership_post_delete(sender, instance, **kwargs):
    Profile.objects.get_or_create(
        user=instance
    )
