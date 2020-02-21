from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from .forms import UserEditForm
from django.http import JsonResponse
from django.http import HttpResponseForbidden

@login_required
def editProfile(request):
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            # Save user
            user = form.save()

            return redirect('/')
    else:
        form = UserEditForm(instance=request.user)
    return render(request, 'registration/profile.html', {'form': form})
