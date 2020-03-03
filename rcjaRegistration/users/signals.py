from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
from django.dispatch import receiver

from schools.models import SchoolAdministrator
from .models import User

# School administrator post-delete
# This signal is important for security because many front end checks use the currentlySelectedSchool field to check school permissions.
# If this is not set to None as necessary then a user's permission will not be revoked.
@receiver(post_delete, sender=SchoolAdministrator)
def SchoolAdministrator_post_delete(sender, instance, **kwargs):
    if instance.user.currentlySelectedSchool == instance.school:
        instance.user.setCurrentlySelectedSchool()

# User post save
# Used to set state and region on connected school if null
@receiver(post_save, sender=User)
def User_post_save(sender, instance, **kwargs):
    if instance.currentlySelectedSchool:
        # Set state
        if instance.currentlySelectedSchool.state is None:
            instance.currentlySelectedSchool.state = instance.homeState
            instance.currentlySelectedSchool.save(update_fields=['state'])

        # Set region
        if instance.currentlySelectedSchool.region is None:
            instance.currentlySelectedSchool.region = instance.homeRegion
            instance.currentlySelectedSchool.save(update_fields=['region'])
