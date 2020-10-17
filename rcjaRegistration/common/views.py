from django.db.models import ProtectedError

def saveDeleteFormsetSkipProtected(formset):
    """
    Saves the formset objects and performs deletions, skipping protected
    """
    # Need commit=False to do manual deletion to catch protected errors
    objects = formset.save(commit=False)

    for obj in formset.deleted_objects:
        try:
            obj.delete()
        except ProtectedError:
            pass

    for obj in objects:
        obj.save()
