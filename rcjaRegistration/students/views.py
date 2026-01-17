from django.http import JsonResponse, request
from django.http.request import HttpRequest
from django.shortcuts import render
from .models import StudentA
from schools.models import SchoolAdministrator

def getStudents(request):
    school_admin = SchoolAdministrator.objects.filter(user=request.user)
    if school_admin.exists():
        school = school_admin[0].school
    else:
        school = None

    query = request.GET.get('q', '')
    students = StudentA.objects.raw("""SELECT * FROM students_StudentA 
                                    WHERE starts_with("firstName" || ' ' ||  "lastName", %s) 
                                    AND ("mentorUser" = %s
                                    OR school = %s)
                                    LIMIT 10""", [query, request.user, school])[:]
    results = [{"id": student.pk, "name": str(student)} for student in students]
    return JsonResponse(results, safe=False)

def searchStudents(request: HttpRequest):
    for i in request.GET.items():
        print(i)
    return render(request, 'students/selectStandalone.html',context={"studentForm":0})