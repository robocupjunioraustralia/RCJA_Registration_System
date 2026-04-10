from django.http import JsonResponse, request
from django.contrib.auth.decorators import login_required
from django.http.request import HttpRequest
from django.shortcuts import render
from django.db.models import Value as V
from django.db.models.functions import Concat

from datetime import datetime

from .models import Student
from .forms import NewStudentForm
from schools.models import SchoolAdministrator

@login_required
def getStudents(request):
    query = request.GET.get('q', '')
    school = request.user.currentlySelectedSchool
    if school is not None:
        students = Student.objects.annotate(name=Concat("firstName", V(" "), "lastName")).filter(school=school).filter(name__startswith=query)
    else:
        students = Student.objects.annotate(name=Concat("firstName", V(" "), "lastName")).filter(mentorUser=request.user).filter(name__startswith=query)
    results = [{"id": student.pk, "name": str(student)} for student in students]
    return JsonResponse(results, safe=False)

@login_required
def searchStudents(request: HttpRequest):
    return render(request, 'students/selectStandalone.html',context={"studentForm":0})

@login_required
def manageStudents(request: HttpRequest):
    if request.method == 'POST':
        form = NewStudentForm(request.POST, user=request.user)
        if form.is_valid():
            print("SAVING")
            form.save()
    else:
        print("GET")
        form = NewStudentForm(user=request.user)

    if request.user.currentlySelectedSchool is not None:
        students = Student.objects.filter(school=request.user.currentlySelectedSchool)
    else:
        students = Student.objects.filter(mentorUser=request.user).order_by("-graduationYear","firstName","lastName")

    return render(request, 'students/manageStudents.html', {'form': form, "students": students, "year": datetime.now().year})