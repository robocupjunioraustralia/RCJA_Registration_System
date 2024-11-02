from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def membership(request):

    return render(request, 'association/membership.html')
