from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from .forms import UserSignupForm, SchoolForm
from django.http import JsonResponse
from django.http import HttpResponseForbidden
from django.core.exceptions import ValidationError, PermissionDenied

from .models import School, Campus, SchoolAdministrator

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

def setCurrentSchool(request, schoolID):
    school = get_object_or_404(School, pk=schoolID)

    # Check permissions
    if not request.user.schooladministrator_set.filter(school=school).exists():
        raise PermissionDenied("You do not have permission to view this school")

    # Set current school on user
    request.user.currentlySelectedSchool = school
    request.user.save(update_fields=['currentlySelectedSchool'])
    
    return redirect('/')
