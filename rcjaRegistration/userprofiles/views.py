from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from .forms import ProfileEditForm
from django.http import JsonResponse
from django.http import HttpResponseForbidden

@login_required
def editProfile(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user.profile)
        if form.is_valid(): 
            profile = form.save()
            user = profile.user

            # Set user attributes
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.username = form.cleaned_data['email']

            # Save user
            user.save()
            return redirect('/')
    else:
        data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email
        }
        form = ProfileEditForm(instance=request.user.profile, initial=data)
    return render(request, 'registration/profile.html', {'form': form})
