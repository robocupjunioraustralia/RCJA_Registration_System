# Create your views here.
from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
# Create your views here.
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, login
from .forms import MentorForm,SchoolForm
from django.http import JsonResponse
from django.http import HttpResponseForbidden

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