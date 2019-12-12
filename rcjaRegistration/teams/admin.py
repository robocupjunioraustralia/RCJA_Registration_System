from django.contrib import admin

from .models import *

# Register your models here.

class StudentInline(admin.TabularInline):
    model = Student
    extra = 0


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    inlines = [
        StudentInline
    ]




admin.site.register(Student)
