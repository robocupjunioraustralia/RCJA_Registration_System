from events.models import Year

def yearsContext(request):
    return {
        'years': Year.objects.all(),
    }
