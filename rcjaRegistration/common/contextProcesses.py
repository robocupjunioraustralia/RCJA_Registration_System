from django.conf import settings

def environment_context(request):
    """ Add tag to header depending on environment """
    if settings.ENVIRONMENT == 'production':
        environment = None
    else:
        environment = settings.ENVIRONMENT.upper()
    return {"environment": environment}