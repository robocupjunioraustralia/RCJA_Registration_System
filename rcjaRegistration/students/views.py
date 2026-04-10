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
    query = request.GET.get("q", "")
    school = request.user.currentlySelectedSchool
    if school is not None:
        students = (
            Student.objects.annotate(name=Concat("firstName", V(" "), "lastName"))
            .filter(school=school)
            .filter(name__startswith=query)
            .exclude(archive=True)
        )
    else:
        students = (
            Student.objects.annotate(name=Concat("firstName", V(" "), "lastName"))
            .filter(mentorUser=request.user)
            .filter(name__startswith=query)
            .exclude(archive=True)
        )
    results = [{"id": student.pk, "name": str(student)} for student in students]
    return JsonResponse(results, safe=False)


@login_required
def searchStudents(request: HttpRequest):
    return render(request, "students/selectStandalone.html", context={"studentForm": 0})


@login_required
def archiveStudents(request: HttpRequest):
    studentId = 0
    try:
        print(request.GET.items)
        studentId = int(request.GET.get("student", ""))
    except ValueError:
        return JsonResponse([False], safe=False)
    editing = None
    try:
        editing = Student.objects.get(pk=studentId)
    except (Student.DoesNotExist, Student.MultipleObjectsReturned):
        return JsonResponse([False], safe=False)

    if request.user.currentlySelectedSchool is not None:
        if editing.school != request.user.currentlySelectedSchool:
            return JsonResponse([False], safe=False)
    else:
        if editing.mentorUser != request.user:
            return JsonResponse([False], safe=False)
    editing.archive = True
    editing.save()
    return JsonResponse([True], safe=False)


def edit(request: HttpRequest, form: NewStudentForm) -> bool:
    studentId = 0
    try:
        studentId = int(request.POST["studentID"])
    except ValueError:
        form.add_error(
            "firstName", "The student you are trying to edit does not exist."
        )
        return False
    editing = None
    try:
        editing = Student.objects.get(pk=studentId)
    except (Student.DoesNotExist, Student.MultipleObjectsReturned):
        form.add_error(
            "firstName", "The student you are trying to edit does not exist."
        )
        return False
    if request.user.currentlySelectedSchool is not None:
        if editing.school != request.user.currentlySelectedSchool:
            form.add_error(
                "firstName", "The student you are trying to edit does not exist."
            )
            return False
    else:
        if editing.mentorUser != request.user:
            form.add_error(
                "firstName", "The student you are trying to edit does not exist."
            )
            return False
    editing.firstName = form.cleaned_data["firstName"]
    editing.lastName = form.cleaned_data["lastName"]
    editing.graduationYear = form.cleaned_data["graduationYear"]
    editing.gender = form.cleaned_data["gender"]
    editing.archive = False
    editing.save()
    return True


@login_required
def manageStudents(request: HttpRequest):
    resetForm = True
    if request.method == "POST":
        resetForm = False
        form = NewStudentForm(request.POST, user=request.user)
        if request.POST["studentID"] == "-1":
            # New Student
            if form.is_valid():
                print("SAVING")
                form.save()
                resetForm = True
        else:
            if form.is_valid():
                resetForm = edit(request, form)
    if resetForm:
        form = NewStudentForm(user=request.user)

    if request.user.currentlySelectedSchool is not None:
        students = (
            Student.objects.filter(school=request.user.currentlySelectedSchool)
            .order_by("-graduationYear", "firstName", "lastName")
            .exclude(archive=True)
        )
        archived_students = (
            Student.objects.filter(school=request.user.currentlySelectedSchool)
            .order_by("-graduationYear", "firstName", "lastName")
            .exclude(archive=False)
        )
    else:
        students = (
            Student.objects.filter(mentorUser=request.user)
            .order_by("-graduationYear", "firstName", "lastName")
            .exclude(archive=True)
        )
        archived_students = (
            Student.objects.filter(mentorUser=request.user)
            .order_by("-graduationYear", "firstName", "lastName")
            .exclude(archive=False)
        )

    return render(
        request,
        "students/manageStudents.html",
        {
            "form": form,
            "students": students,
            "year": datetime.now().year,
            "archived_students": archived_students,
        },
    )
