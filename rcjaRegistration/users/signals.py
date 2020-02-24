from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
from django.dispatch import receiver

from schools.models import SchoolAdministrator

# School administrator post-delete
# This signal is important for security because many front end checks use the currentlySelectedSchool field to check school permissions.
# If this is not set to None as necessary then a user's permission will not be revoked.
# TODO: Write tests for this: GitHub issue #102
@receiver(post_delete, sender=SchoolAdministrator)
def SchoolAdministrator_post_delete(sender, instance, **kwargs):
    # Set currentlySelectedSchool to another school for this user or None if no other schools
    if instance.user.currentlySelectedSchool == instance.school:
        if instance.user.schooladministrator_set.exists():
            instance.user.currentlySelectedSchool = instance.user.schooladministrator_set.first().school
        else:
            instance.user.currentlySelectedSchool = None
        instance.user.save(update_fields=['currentlySelectedSchool'])
