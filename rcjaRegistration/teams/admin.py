from django.contrib import admin
from common.admin import *

from .models import *

# Register your models here.

class StudentInline(admin.TabularInline):
    model = Student
    extra = 0


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin, ExportCSVMixin):
    inlines = [
        StudentInline
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'event',
        'division',
        'school',
        'name'
    ]

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin, ExportCSVMixin):
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'team',
        'firstName',
        'lastName',
        'yearLevel',
        'gender',
        'birthday'
    ]
