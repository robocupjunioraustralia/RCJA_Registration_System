from events.models import Year
from django.conf import settings

def yearsContext(request):
    return {
        'years': Year.objects.all(),
    }

def environmentContext(request):
    """ Add tag to header depending on environment """
    if settings.ENVIRONMENT == 'production':
        environment = None
    else:
        environment = settings.ENVIRONMENT.upper()
    return {"environment": environment}
