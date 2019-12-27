# Create your views here.
from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
# Create your views here.
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from .forms import MentorForm,SchoolForm


def signup(request):
    if request.method == 'POST':
        form = MentorForm(request.POST)
        if form.is_valid(): 
            mentor = form.save()
            user = mentor.user
            user.set_password(request.POST["password"])
            user.save()
            login(request, user)
            return redirect('/')
    else:
        form = MentorForm()
    return render(request, 'registration/signup.html', {'form': form})


def schoolCreation(request):
    if request.method == 'POST':
        form = SchoolForm(request.POST)
        if form.is_valid(): 
            form.save()
            return redirect('/')
    else:
        form = SchoolForm()
    return render(request, 'schools/createSchool.html', {'form': form})