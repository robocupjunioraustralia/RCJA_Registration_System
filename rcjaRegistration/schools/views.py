from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from .forms import UserSignupForm, SchoolForm
from django.http import JsonResponse
from django.http import HttpResponseForbidden

from schools.models import SchoolAdministrator

def signup(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        schoolCreationDetails = SchoolForm(request.POST) #note this isn't saved here

        if form.is_valid():
            # Save user
            user = form.save()
            user.set_password(form.cleaned_data["password"])
            user.save()

            # Save school administrator
            SchoolAdministrator.objects.create(user=user, school=form.cleaned_data['school'])

            # Login and redirect
            login(request, user)
            return redirect('/')
    else:
        form = UserSignupForm()
        schoolCreationDetails = SchoolForm
    return render(request, 'registration/signup.html', {'form': form,'schoolCreationModal':schoolCreationDetails})
    #we include the school creation here so we can preload the form details, but we
    #don't actually want to do anything with the data on this endpoint, which is why
    #it's not in the post area

def schoolCreation(request):
    if request.method == 'POST':
        form = SchoolForm(request.POST)
        if form.is_valid(): 
            form.save()
            return redirect('/')
    else:
        form = SchoolForm()
    return render(request, 'schools/createSchool.html', {'form': form})

def createSchoolAJAX(request):
    if request.method == 'POST':
        form = SchoolForm(request.POST)
        if form.is_valid(): 
            newSchool = form.save()
            return JsonResponse({'id':newSchool.id,'name':newSchool.name})
        else:
            return JsonResponse({
                'success': False,
                'errors': dict(form.errors.items())
            },status=400)
    else:
        return HttpResponseForbidden()
