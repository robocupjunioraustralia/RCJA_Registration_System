# Create your views here.
from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
# Create your views here.
from django.http import HttpResponse
from django.template import loader

from .forms import MentorForm,SchoolForm
@login_required
def mentorRegistration(request):
    if request.method == 'POST':
        form = MentorForm(request.POST)
        if form.is_valid(): 
            mentor = form.save(commit=False)
            mentor.user = request.user
            form.save()
            return redirect('/')
    else:
        form = MentorForm()
    return render(request, 'schools/mentorRegistration.html', {'form': form}) 

@login_required
def schoolCreation(request):
    if request.method == 'POST':
        form = SchoolForm(request.POST)
        if form.is_valid(): 
            form.save()
            return redirect('/')
    else:
        form = SchoolForm()
    return render(request, 'schools/createSchool.html', {'form': form})