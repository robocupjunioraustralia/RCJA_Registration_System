from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
from django.dispatch import receiver

from .models import MentorEventFileUpload

# MentorEventFileUpload post-delete
# Delete the file in S3 after the model is deleted
@receiver(post_delete, sender=MentorEventFileUpload)
def MentorEventFileUpload_post_delete(sender, instance, **kwargs):
    instance.fileUpload.delete(save=False)
